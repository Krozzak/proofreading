"""
History service for persistent comparison approvals using Firestore.
Handles saving and retrieving user comparison history.
"""

import hashlib
from datetime import datetime, timezone
from typing import TypedDict, Optional
from services.firebase_admin import get_firestore_client


class FileInfo(TypedDict):
    """File information stored in history."""
    name: str
    size: int


class PageValidation(TypedDict):
    """Page validation status."""
    status: Optional[str]  # 'approved' | 'rejected' | None
    comment: str


class HistoryEntry(TypedDict):
    """Single comparison history entry."""
    fileSignature: str
    code: str
    originalFile: Optional[FileInfo]
    printerFile: Optional[FileInfo]
    similarity: Optional[float]
    validation: str  # 'pending' | 'approved' | 'rejected' | 'partial'
    pageValidations: dict[int, PageValidation]
    comment: str
    validatedAt: Optional[str]


class HistoryMatch(TypedDict):
    """History match returned to frontend."""
    fileSignature: str
    similarity: Optional[float]
    validation: str
    pageValidations: dict[int, PageValidation]
    comment: str
    validatedAt: Optional[str]


def generate_file_signature(
    original_name: Optional[str],
    original_size: Optional[int],
    printer_name: Optional[str],
    printer_size: Optional[int]
) -> str:
    """
    Generate a unique signature for a file pair based on names and sizes.

    This allows matching the same files when they are re-uploaded.

    Args:
        original_name: Name of original file (or None)
        original_size: Size of original file in bytes (or None)
        printer_name: Name of printer file (or None)
        printer_size: Size of printer file in bytes (or None)

    Returns:
        32-character hex string signature
    """
    components = []

    if original_name:
        components.append(f"orig:{original_name}:{original_size or 0}")
    if printer_name:
        components.append(f"print:{printer_name}:{printer_size or 0}")

    # Sort to ensure consistent ordering
    signature_string = "|".join(sorted(components))

    return hashlib.sha256(signature_string.encode()).hexdigest()[:32]


def save_comparison_batch(
    uid: str,
    comparisons: list[dict]
) -> int:
    """
    Save a batch of comparisons to user's history.

    Uses Firestore batched writes for efficiency.
    Each comparison is identified by fileSignature - if it already exists,
    it will be updated (upsert behavior).

    Args:
        uid: Firebase user ID
        comparisons: List of comparison dictionaries with:
            - fileSignature: str
            - code: str
            - originalFile: {name, size} | None
            - printerFile: {name, size} | None
            - similarity: float | None
            - validation: str
            - pageValidations: dict
            - comment: str
            - validatedAt: str | None

    Returns:
        Number of comparisons saved
    """
    if not comparisons:
        return 0

    db = get_firestore_client()
    batch = db.batch()
    now = datetime.now(timezone.utc).isoformat()

    saved_count = 0

    for comparison in comparisons:
        file_signature = comparison.get('fileSignature')
        if not file_signature:
            continue

        # Document ID is combination of userId and fileSignature
        # This ensures uniqueness per user and allows easy updates
        doc_id = f"{uid}_{file_signature}"
        doc_ref = db.collection('comparison_history').document(doc_id)

        # Prepare document data
        doc_data = {
            'userId': uid,
            'fileSignature': file_signature,
            'code': comparison.get('code', ''),
            'originalFile': comparison.get('originalFile'),
            'printerFile': comparison.get('printerFile'),
            'similarity': comparison.get('similarity'),
            'validation': comparison.get('validation', 'pending'),
            'pageValidations': comparison.get('pageValidations', {}),
            'comment': comparison.get('comment', ''),
            'validatedAt': comparison.get('validatedAt'),
            'updatedAt': now,
        }

        # Check if document exists to set createdAt only on first save
        existing = doc_ref.get()
        if not existing.exists:
            doc_data['createdAt'] = now

        batch.set(doc_ref, doc_data, merge=True)
        saved_count += 1

        # Firestore batch limit is 500 operations
        if saved_count % 450 == 0:
            batch.commit()
            batch = db.batch()

    # Commit remaining
    if saved_count % 450 != 0:
        batch.commit()

    return saved_count


def match_files_from_history(
    uid: str,
    file_signatures: list[str]
) -> dict[str, HistoryMatch]:
    """
    Find history entries matching the given file signatures.

    Args:
        uid: Firebase user ID
        file_signatures: List of file signatures to match

    Returns:
        Dictionary mapping fileSignature to HistoryMatch
    """
    if not file_signatures:
        return {}

    db = get_firestore_client()
    matches: dict[str, HistoryMatch] = {}

    # Query in batches of 30 (Firestore 'in' query limit)
    batch_size = 30
    for i in range(0, len(file_signatures), batch_size):
        batch_signatures = file_signatures[i:i + batch_size]

        # Build document IDs to fetch directly (more efficient than query)
        for sig in batch_signatures:
            doc_id = f"{uid}_{sig}"
            doc_ref = db.collection('comparison_history').document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                matches[sig] = HistoryMatch(
                    fileSignature=sig,
                    similarity=data.get('similarity'),
                    validation=data.get('validation', 'pending'),
                    pageValidations=data.get('pageValidations', {}),
                    comment=data.get('comment', ''),
                    validatedAt=data.get('validatedAt'),
                )

    return matches


def get_user_history(
    uid: str,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    """
    Get user's comparison history, ordered by most recent.

    Args:
        uid: Firebase user ID
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        List of history entries
    """
    db = get_firestore_client()

    # Query user's history ordered by updatedAt descending
    query = (
        db.collection('comparison_history')
        .where('userId', '==', uid)
        .order_by('updatedAt', direction='DESCENDING')
        .limit(limit)
        .offset(offset)
    )

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        results.append({
            'id': doc.id,
            'fileSignature': data.get('fileSignature'),
            'code': data.get('code'),
            'originalFile': data.get('originalFile'),
            'printerFile': data.get('printerFile'),
            'similarity': data.get('similarity'),
            'validation': data.get('validation'),
            'pageValidations': data.get('pageValidations', {}),
            'comment': data.get('comment', ''),
            'validatedAt': data.get('validatedAt'),
            'createdAt': data.get('createdAt'),
            'updatedAt': data.get('updatedAt'),
        })

    return results


def get_history_count(uid: str) -> int:
    """
    Get total count of user's history entries.

    Args:
        uid: Firebase user ID

    Returns:
        Number of history entries
    """
    db = get_firestore_client()

    # Use aggregation query for count
    query = db.collection('comparison_history').where('userId', '==', uid)

    # Count documents (Firestore v2 feature)
    try:
        count_query = query.count()
        result = count_query.get()
        return result[0][0].value
    except Exception:
        # Fallback: count manually (less efficient)
        count = 0
        for _ in query.stream():
            count += 1
        return count


def delete_history_entry(uid: str, file_signature: str) -> bool:
    """
    Delete a single history entry.

    Args:
        uid: Firebase user ID
        file_signature: File signature to delete

    Returns:
        True if deleted, False if not found
    """
    db = get_firestore_client()
    doc_id = f"{uid}_{file_signature}"
    doc_ref = db.collection('comparison_history').document(doc_id)

    if doc_ref.get().exists:
        doc_ref.delete()
        return True

    return False
