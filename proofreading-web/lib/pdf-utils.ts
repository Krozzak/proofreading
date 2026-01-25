/**
 * PDF processing utilities
 * Calls external API (Cloud Run) for PDF conversion and comparison
 */

// API URL - uses environment variable or defaults to localhost for development
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Convert a File to base64 string
 */
export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix to get just the base64 string
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Call the Python serverless function to convert PDF to image
 * @param pdfBase64 - Base64 encoded PDF
 * @param page - Page number (0-indexed)
 * @param token - Optional auth token for authenticated requests
 */
export async function convertPdfToImage(
  pdfBase64: string,
  page: number = 0,
  token?: string | null
): Promise<{ image: string; totalPages: number } | null> {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add auth token if provided
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/convert`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        pdf: pdfBase64,
        page,
      }),
    });

    if (!response.ok) {
      console.error('Failed to convert PDF:', response.statusText);
      return null;
    }

    const data = await response.json();
    if (data.success) {
      return {
        image: `data:image/png;base64,${data.image}`,
        totalPages: data.totalPages,
      };
    }
    return null;
  } catch (error) {
    console.error('Error converting PDF:', error);
    return null;
  }
}

/**
 * Call the Python serverless function to compare two images
 * @param image1Base64 - First image (base64 or data URL)
 * @param image2Base64 - Second image (base64 or data URL)
 * @param autoCrop - Whether to auto-crop to content
 * @param token - Optional auth token for authenticated requests
 */
export async function compareImages(
  image1Base64: string,
  image2Base64: string,
  autoCrop: boolean = true,
  token?: string | null
): Promise<{
  similarity: number;
  method: string;
  confidence: number;
} | null> {
  try {
    // Remove data URL prefix if present
    const clean1 = image1Base64.includes(',')
      ? image1Base64.split(',')[1]
      : image1Base64;
    const clean2 = image2Base64.includes(',')
      ? image2Base64.split(',')[1]
      : image2Base64;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add auth token if provided
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}/api/compare`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        image1: clean1,
        image2: clean2,
        autoCrop,
      }),
    });

    // Handle quota exceeded error
    if (response.status === 429) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Quota exceeded');
    }

    if (!response.ok) {
      console.error('Failed to compare images:', response.statusText);
      return null;
    }

    const data = await response.json();
    if (data.success) {
      return {
        similarity: data.similarity,
        method: data.method,
        confidence: data.confidence,
      };
    }
    return null;
  } catch (error) {
    console.error('Error comparing images:', error);
    throw error; // Re-throw for caller to handle
  }
}

/**
 * Export results to CSV format
 */
export function exportToCSV(
  data: Array<{
    code: string;
    filename: string;
    matching: string;
    similarity: string;
    validation: string;
    comment: string;
    date: string;
  }>
): string {
  const headers = ['Code Litho', 'Filename', 'Matching', 'Similarity', 'Validation', 'Comment', 'Date'];
  const rows = data.map((row) => [
    row.code,
    row.filename,
    row.matching,
    row.similarity,
    row.validation,
    row.comment,
    row.date,
  ]);

  const csvContent = [
    headers.join(';'),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(';')),
  ].join('\n');

  return csvContent;
}

/**
 * Download a string as a file
 */
export function downloadFile(content: string, filename: string, mimeType: string = 'text/csv') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
}
