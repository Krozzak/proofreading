"""
PDF to Image conversion service using PyMuPDF
"""

import io
import fitz  # PyMuPDF
from PIL import Image


def pdf_to_image(pdf_bytes: bytes, page_number: int = 0, scale: float = 2.0) -> tuple[bytes | None, int]:
    """
    Convert a PDF page to a PNG image.

    Args:
        pdf_bytes: The PDF file as bytes
        page_number: Which page to render (0-indexed)
        scale: Resolution multiplier (2.0 = 2x resolution)

    Returns:
        Tuple of (PNG image bytes or None, total page count)
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        if page_number >= total_pages:
            page_number = 0

        page = doc.load_page(page_number)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)

        return buffer.getvalue(), total_pages
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None, 0
