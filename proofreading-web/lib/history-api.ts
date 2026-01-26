/**
 * History API utilities
 * Handles saving and retrieving comparison history from the backend
 */

import type {
  SavedComparison,
  HistoryMatch,
  HistoryEntry,
  HistoryFileInfo,
} from './types';

// API URL - uses environment variable or defaults to localhost for development
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generate a file signature for matching files in history.
 * Uses the same algorithm as the backend.
 *
 * @param originalName - Name of original file (or null)
 * @param originalSize - Size of original file in bytes (or null)
 * @param printerName - Name of printer file (or null)
 * @param printerSize - Size of printer file in bytes (or null)
 * @returns 32-character hex string signature
 */
export async function generateFileSignature(
  originalName: string | null,
  originalSize: number | null,
  printerName: string | null,
  printerSize: number | null
): Promise<string> {
  const components: string[] = [];

  if (originalName) {
    components.push(`orig:${originalName}:${originalSize || 0}`);
  }
  if (printerName) {
    components.push(`print:${printerName}:${printerSize || 0}`);
  }

  // Sort to ensure consistent ordering
  const signatureString = components.sort().join('|');

  // Use Web Crypto API for SHA-256 hash
  const encoder = new TextEncoder();
  const data = encoder.encode(signatureString);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');

  return hashHex.slice(0, 32);
}

/**
 * Save comparison history to the backend.
 *
 * @param token - Firebase auth token
 * @param comparisons - Array of comparisons to save
 * @returns Number of saved entries
 */
export async function saveComparisonHistory(
  token: string,
  comparisons: SavedComparison[]
): Promise<{ savedCount: number }> {
  const response = await fetch(`${API_URL}/api/history/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ comparisons }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to save history');
  }

  return response.json();
}

/**
 * Match files from history.
 * Used to restore previous approvals when user re-uploads same files.
 *
 * @param token - Firebase auth token
 * @param fileSignatures - Array of file signatures to match
 * @returns Map of file signatures to their history matches
 */
export async function matchFilesFromHistory(
  token: string,
  fileSignatures: string[]
): Promise<Record<string, HistoryMatch>> {
  const response = await fetch(`${API_URL}/api/history/match`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ fileSignatures }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to match history');
  }

  const data = await response.json();
  return data.matches;
}

/**
 * Get user's comparison history.
 *
 * @param token - Firebase auth token
 * @param limit - Maximum entries to return
 * @param offset - Number of entries to skip (for pagination)
 * @returns History entries and total count
 */
export async function getUserHistory(
  token: string,
  limit: number = 100,
  offset: number = 0
): Promise<{ entries: HistoryEntry[]; total: number }> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response = await fetch(`${API_URL}/api/history?${params}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to fetch history');
  }

  return response.json();
}

/**
 * Delete a history entry.
 *
 * @param token - Firebase auth token
 * @param fileSignature - File signature of entry to delete
 * @returns Success status
 */
export async function deleteHistoryEntry(
  token: string,
  fileSignature: string
): Promise<{ success: boolean }> {
  const response = await fetch(
    `${API_URL}/api/history/${encodeURIComponent(fileSignature)}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to delete entry');
  }

  return response.json();
}

/**
 * Helper to convert File to HistoryFileInfo
 */
export function fileToHistoryInfo(file: File | undefined): HistoryFileInfo | null {
  if (!file) return null;
  return {
    name: file.name,
    size: file.size,
  };
}
