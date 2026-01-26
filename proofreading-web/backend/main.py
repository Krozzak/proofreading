"""
FastAPI backend for PDF Proofreading application.
Handles PDF to image conversion and SSIM similarity calculation.
Now with Firebase authentication and quota management.

Deploy to Google Cloud Run for serverless execution.
"""

import base64
from typing import Optional, Literal
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services.pdf_converter import pdf_to_image
from services.ssim_calculator import calculate_similarity
from services.auth_dependency import get_current_user, get_optional_user, AuthenticatedUser
from services.quota_service import (
    get_quota,
    check_and_increment_quota,
    get_anonymous_quota,
    check_and_increment_anonymous_quota
)
from services.stripe_service import (
    create_checkout_session,
    create_customer_portal_session,
    get_subscription_info,
    verify_webhook_signature,
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_invoice_payment_failed,
)
from services.history_service import (
    generate_file_signature,
    save_comparison_batch,
    match_files_from_history,
    get_user_history,
    get_history_count,
    delete_history_entry,
)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Proofreading API",
    description="API for PDF comparison using SSIM with Firebase Auth",
    version="2.1.0"
)

# CORS configuration - restrict to known domains
# Note: allow_origin_regex is used to support Vercel preview deployments
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://proofslab.vercel.app",
    "https://proofslab.com",
    "https://www.proofslab.com",
]

# Regex to match Vercel preview URLs (e.g., proofreading-xxx-thomas-silliards-projects.vercel.app)
ALLOWED_ORIGIN_REGEX = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure CORS headers are always returned.
    Without this, errors during dependency injection (like Firebase init failures)
    bypass the CORS middleware and return 500 without CORS headers.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Request/Response models
class ConvertRequest(BaseModel):
    pdf: str  # Base64 encoded PDF
    page: int = 0


class ConvertResponse(BaseModel):
    success: bool
    image: str | None = None  # Base64 encoded PNG
    totalPages: int = 0
    page: int = 0
    error: str | None = None


class CompareRequest(BaseModel):
    image1: str  # Base64 encoded PNG
    image2: str  # Base64 encoded PNG
    autoCrop: bool = True


class QuotaInfo(BaseModel):
    used: int
    limit: int
    remaining: int
    resetsAt: str


class CompareResponse(BaseModel):
    success: bool
    similarity: float = 0
    bounds1: tuple[int, int, int, int] | None = None
    bounds2: tuple[int, int, int, int] | None = None
    confidence: float = 0
    method: str = "error"
    error: str | None = None
    quota: QuotaInfo | None = None  # Return updated quota after comparison


class HealthResponse(BaseModel):
    status: str
    version: str


class QuotaResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    resetsAt: str


# Stripe models
class CheckoutRequest(BaseModel):
    billingPeriod: Literal['monthly', 'yearly'] = 'monthly'
    successUrl: str
    cancelUrl: str


class CheckoutResponse(BaseModel):
    url: str


class PortalRequest(BaseModel):
    returnUrl: str


class PortalResponse(BaseModel):
    url: str


class SubscriptionResponse(BaseModel):
    status: str
    currentPeriodEnd: str | None
    cancelAtPeriodEnd: bool
    tier: str
    billingPeriod: str | None


# History models
class FileInfoModel(BaseModel):
    name: str
    size: int


class PageValidationModel(BaseModel):
    status: str | None  # 'approved' | 'rejected' | None
    comment: str = ''


class ComparisonEntryModel(BaseModel):
    fileSignature: str
    code: str
    originalFile: FileInfoModel | None = None
    printerFile: FileInfoModel | None = None
    similarity: float | None = None
    validation: str = 'pending'
    pageValidations: dict[str, PageValidationModel] = {}
    comment: str = ''
    validatedAt: str | None = None


class HistorySaveRequest(BaseModel):
    comparisons: list[ComparisonEntryModel]


class HistorySaveResponse(BaseModel):
    savedCount: int


class HistoryMatchRequest(BaseModel):
    fileSignatures: list[str]


class HistoryMatchEntry(BaseModel):
    fileSignature: str
    similarity: float | None
    validation: str
    pageValidations: dict[str, PageValidationModel]
    comment: str
    validatedAt: str | None


class HistoryMatchResponse(BaseModel):
    matches: dict[str, HistoryMatchEntry]


class HistoryEntryResponse(BaseModel):
    id: str
    fileSignature: str
    code: str
    originalFile: FileInfoModel | None
    printerFile: FileInfoModel | None
    similarity: float | None
    validation: str
    pageValidations: dict
    comment: str
    validatedAt: str | None
    createdAt: str | None
    updatedAt: str | None


class HistoryListResponse(BaseModel):
    entries: list[HistoryEntryResponse]
    total: int


# Endpoints

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for Cloud Run.
    PUBLIC - No authentication required.
    """
    return HealthResponse(status="healthy", version="2.1.0")


@app.get("/api/quota", response_model=QuotaResponse)
async def get_user_quota(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get current user's quota information.
    PROTECTED - Requires authentication.
    """
    quota = get_quota(user.uid, user.tier)
    return QuotaResponse(**quota)


@app.post("/api/convert", response_model=ConvertResponse)
async def convert_pdf(
    request: ConvertRequest,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """
    Convert a PDF page to a PNG image.
    PUBLIC - Works for both authenticated and anonymous users.
    No quota consumed for conversion (only for comparison).

    Args:
        request: ConvertRequest with base64 PDF and page number
        user: Optional authenticated user

    Returns:
        ConvertResponse with base64 PNG image
    """
    try:
        # Decode PDF
        pdf_bytes = base64.b64decode(request.pdf)

        # Convert to image
        img_bytes, total_pages = pdf_to_image(pdf_bytes, request.page)

        if img_bytes:
            return ConvertResponse(
                success=True,
                image=base64.b64encode(img_bytes).decode('utf-8'),
                totalPages=total_pages,
                page=request.page
            )
        else:
            return ConvertResponse(
                success=False,
                error="Failed to convert PDF"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Cloud Run sets X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.post("/api/compare", response_model=CompareResponse)
async def compare_images(
    request: CompareRequest,
    http_request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """
    Compare two images using SSIM.
    PUBLIC - Works for both authenticated and anonymous users with quota:
    - Anonymous: 1 comparison/day (based on IP)
    - Free account: 5 comparisons/day
    - Pro account: 100 comparisons/day
    - Enterprise: unlimited

    Args:
        request: CompareRequest with two base64 images
        http_request: FastAPI request for IP extraction
        user: Optional authenticated user

    Returns:
        CompareResponse with similarity score, metadata, and updated quota

    Raises:
        HTTPException 429: If daily quota exceeded
    """
    # Check and increment quota based on auth status
    if user:
        # Authenticated user
        success, quota = check_and_increment_quota(user.uid, user.tier)
        quota_message = "Quota journalier atteint. Passez au plan Pro pour plus de comparaisons."
    else:
        # Anonymous user - use IP-based quota
        client_ip = get_client_ip(http_request)
        success, quota = check_and_increment_anonymous_quota(client_ip)
        quota_message = "Limite gratuite atteinte (1/jour). Connectez-vous pour 5 comparaisons/jour gratuites."

    if not success:
        raise HTTPException(
            status_code=429,
            detail=quota_message,
            headers={"X-Quota-Remaining": "0"},
        )

    try:
        # Decode images
        img1_bytes = base64.b64decode(request.image1)
        img2_bytes = base64.b64decode(request.image2)

        # Calculate similarity
        result = calculate_similarity(img1_bytes, img2_bytes, request.autoCrop)

        return CompareResponse(
            success=True,
            similarity=result['similarity'],
            bounds1=result.get('bounds1'),
            bounds2=result.get('bounds2'),
            confidence=result['confidence'],
            method=result['method'],
            error=result.get('error'),
            quota=QuotaInfo(**quota)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Stripe endpoints

@app.post("/api/stripe/checkout", response_model=CheckoutResponse)
async def stripe_create_checkout(
    request: CheckoutRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session for Pro subscription.
    PROTECTED - Requires authentication.

    Args:
        request: CheckoutRequest with billing period and redirect URLs

    Returns:
        CheckoutResponse with checkout session URL
    """
    try:
        checkout_url = create_checkout_session(
            uid=user.uid,
            email=user.email,
            billing_period=request.billingPeriod,
            success_url=request.successUrl,
            cancel_url=request.cancelUrl,
        )
        return CheckoutResponse(url=checkout_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@app.post("/api/stripe/portal", response_model=PortalResponse)
async def stripe_create_portal(
    request: PortalRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a Stripe Customer Portal session.
    PROTECTED - Requires authentication.

    Args:
        request: PortalRequest with return URL

    Returns:
        PortalResponse with customer portal URL
    """
    try:
        portal_url = create_customer_portal_session(
            uid=user.uid,
            return_url=request.returnUrl,
        )
        return PortalResponse(url=portal_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portal session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@app.get("/api/subscription", response_model=SubscriptionResponse)
async def get_user_subscription(
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get current user's subscription information.
    PROTECTED - Requires authentication.

    Returns:
        SubscriptionResponse with subscription details and user tier
    """
    info = get_subscription_info(user.uid)
    return SubscriptionResponse(
        status=info['status'],
        currentPeriodEnd=info['currentPeriodEnd'],
        cancelAtPeriodEnd=info['cancelAtPeriodEnd'],
        tier=user.tier,
        billingPeriod=info['billingPeriod'],
    )


@app.post("/api/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature")
):
    """
    Handle Stripe webhook events.
    PUBLIC - No authentication (uses webhook signature verification).

    This endpoint receives events from Stripe and updates user subscriptions
    in Firestore accordingly.
    """
    payload = await request.body()

    try:
        event = verify_webhook_signature(payload, stripe_signature)
    except ValueError as e:
        logger.warning(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Handle events
    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == 'checkout.session.completed':
            handle_checkout_completed(data)
        elif event_type in ['customer.subscription.created', 'customer.subscription.updated']:
            handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(data)
        elif event_type == 'invoice.payment_failed':
            handle_invoice_payment_failed(data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
    except Exception as e:
        logger.error(f"Webhook handler error: {e}", exc_info=True)
        # Return 200 to prevent Stripe retries for non-recoverable errors

    return {"received": True}


# History endpoints

@app.post("/api/history/save", response_model=HistorySaveResponse)
async def save_history(
    request: HistorySaveRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Save comparison history for authenticated user.
    PROTECTED - Requires authentication.

    Saves a batch of comparisons to the user's history.
    Uses upsert behavior - existing entries are updated, new ones created.

    Args:
        request: HistorySaveRequest with list of comparisons

    Returns:
        HistorySaveResponse with count of saved entries
    """
    try:
        # Convert Pydantic models to dicts for the service
        comparisons_data = []
        for comp in request.comparisons:
            comp_dict = comp.model_dump()
            # Convert pageValidations keys back to strings (Firestore doesn't support int keys)
            if comp_dict.get('pageValidations'):
                comp_dict['pageValidations'] = {
                    str(k): v for k, v in comp_dict['pageValidations'].items()
                }
            comparisons_data.append(comp_dict)

        saved_count = save_comparison_batch(user.uid, comparisons_data)
        return HistorySaveResponse(savedCount=saved_count)

    except Exception as e:
        logger.error(f"History save error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save history")


@app.post("/api/history/match", response_model=HistoryMatchResponse)
async def match_history(
    request: HistoryMatchRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Find history entries matching file signatures.
    PROTECTED - Requires authentication.

    Used to restore previous approvals when user re-uploads same files.

    Args:
        request: HistoryMatchRequest with list of file signatures

    Returns:
        HistoryMatchResponse with matching entries
    """
    try:
        matches = match_files_from_history(user.uid, request.fileSignatures)

        # Convert to response format
        response_matches = {}
        for sig, match in matches.items():
            response_matches[sig] = HistoryMatchEntry(
                fileSignature=match['fileSignature'],
                similarity=match['similarity'],
                validation=match['validation'],
                pageValidations={
                    str(k): PageValidationModel(
                        status=v.get('status'),
                        comment=v.get('comment', '')
                    )
                    for k, v in match.get('pageValidations', {}).items()
                },
                comment=match['comment'],
                validatedAt=match['validatedAt'],
            )

        return HistoryMatchResponse(matches=response_matches)

    except Exception as e:
        logger.error(f"History match error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to match history")


@app.get("/api/history", response_model=HistoryListResponse)
async def list_history(
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get user's comparison history.
    PROTECTED - Requires authentication.

    Returns paginated list of user's past comparisons.

    Args:
        limit: Maximum entries to return (default 100)
        offset: Number of entries to skip (for pagination)

    Returns:
        HistoryListResponse with entries and total count
    """
    try:
        entries = get_user_history(user.uid, limit=limit, offset=offset)
        total = get_history_count(user.uid)

        response_entries = []
        for entry in entries:
            response_entries.append(HistoryEntryResponse(
                id=entry['id'],
                fileSignature=entry['fileSignature'],
                code=entry['code'],
                originalFile=FileInfoModel(**entry['originalFile']) if entry.get('originalFile') else None,
                printerFile=FileInfoModel(**entry['printerFile']) if entry.get('printerFile') else None,
                similarity=entry['similarity'],
                validation=entry['validation'],
                pageValidations=entry.get('pageValidations', {}),
                comment=entry.get('comment', ''),
                validatedAt=entry.get('validatedAt'),
                createdAt=entry.get('createdAt'),
                updatedAt=entry.get('updatedAt'),
            ))

        return HistoryListResponse(entries=response_entries, total=total)

    except Exception as e:
        logger.error(f"History list error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@app.delete("/api/history/{file_signature}")
async def delete_history_item(
    file_signature: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete a single history entry.
    PROTECTED - Requires authentication.

    Args:
        file_signature: File signature of entry to delete

    Returns:
        Success status
    """
    try:
        deleted = delete_history_entry(user.uid, file_signature)
        if deleted:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Entry not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History delete error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete entry")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
