"""
SSIM (Structural Similarity Index) calculation service
"""

import io
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim


def detect_content_bounds(
    img: Image.Image,
    margin_threshold: int = 250,
    min_content_ratio: float = 0.05
) -> tuple[int, int, int, int] | None:
    """
    Detect content bounds by finding non-white pixels.

    Args:
        img: PIL Image to analyze
        margin_threshold: Pixel value threshold (< this = content)
        min_content_ratio: Minimum ratio of content pixels per row/column

    Returns:
        Tuple of (left, top, right, bottom) or None if detection fails
    """
    try:
        gray = np.array(img.convert('L'))

        # Mask: True = content (non-white)
        mask = gray < margin_threshold

        # Content ratio per row/column
        row_content = np.sum(mask, axis=1) / mask.shape[1]
        col_content = np.sum(mask, axis=0) / mask.shape[0]

        # Find content boundaries
        content_rows = np.where(row_content > min_content_ratio)[0]
        content_cols = np.where(col_content > min_content_ratio)[0]

        if len(content_rows) == 0 or len(content_cols) == 0:
            return None

        top, bottom = content_rows[0], content_rows[-1]
        left, right = content_cols[0], content_cols[-1]

        # Add 2% padding
        h, w = gray.shape
        padding_h, padding_w = int(h * 0.02), int(w * 0.02)

        return (
            max(0, left - padding_w),
            max(0, top - padding_h),
            min(w, right + padding_w),
            min(h, bottom + padding_h)
        )
    except Exception as e:
        print(f"Error in detect_content_bounds: {e}")
        return None


def resize_preserve_aspect(img: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """
    Resize image preserving aspect ratio with white padding.

    Args:
        img: PIL Image to resize
        target_size: Target dimensions (width, height)

    Returns:
        Resized image with white padding
    """
    img_copy = img.copy()
    img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)

    result = Image.new('RGB', target_size, 'white')
    offset = (
        (target_size[0] - img_copy.size[0]) // 2,
        (target_size[1] - img_copy.size[1]) // 2
    )
    result.paste(img_copy, offset)

    return result


def calculate_similarity(
    img1_bytes: bytes,
    img2_bytes: bytes,
    auto_crop: bool = True
) -> dict:
    """
    Calculate SSIM similarity between two images.

    Args:
        img1_bytes: First image as PNG bytes
        img2_bytes: Second image as PNG bytes
        auto_crop: Whether to auto-detect and crop content

    Returns:
        Dict with similarity score, bounds, confidence, and method
    """
    try:
        img1 = Image.open(io.BytesIO(img1_bytes))
        img2 = Image.open(io.BytesIO(img2_bytes))

        bounds1 = None
        bounds2 = None
        confidence = 1.0
        method = 'full'

        if auto_crop:
            bounds1 = detect_content_bounds(img1)
            bounds2 = detect_content_bounds(img2)

            if bounds1 and bounds2:
                method = 'threshold'
                w1, h1 = img1.size
                w2, h2 = img2.size

                # Check if bounds are reasonable (15-95% of image)
                area1 = ((bounds1[2] - bounds1[0]) * (bounds1[3] - bounds1[1])) / (w1 * h1)
                area2 = ((bounds2[2] - bounds2[0]) * (bounds2[3] - bounds2[1])) / (w2 * h2)

                if 0.15 < area1 < 0.95 and 0.15 < area2 < 0.95:
                    img1 = img1.crop(bounds1)
                    img2 = img2.crop(bounds2)
                    confidence = 0.9
                else:
                    bounds1 = None
                    bounds2 = None
                    method = 'full'

        # Resize to common size
        target_size = (800, 800)
        img1_resized = resize_preserve_aspect(img1, target_size)
        img2_resized = resize_preserve_aspect(img2, target_size)

        # Convert to grayscale
        gray1 = np.array(img1_resized.convert('L'))
        gray2 = np.array(img2_resized.convert('L'))

        # Calculate SSIM
        score = ssim(gray1, gray2)
        score = max(0.0, min(1.0, score))

        return {
            'similarity': round(score * 100, 2),
            'bounds1': bounds1,
            'bounds2': bounds2,
            'confidence': confidence,
            'method': method
        }
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return {
            'similarity': 0,
            'bounds1': None,
            'bounds2': None,
            'confidence': 0,
            'method': 'error',
            'error': str(e)
        }
