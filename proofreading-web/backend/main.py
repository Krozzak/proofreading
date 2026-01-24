"""
FastAPI backend for PDF Proofreading application.
Handles PDF to image conversion and SSIM similarity calculation.

Deploy to Google Cloud Run for serverless execution.
"""

import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.pdf_converter import pdf_to_image
from services.ssim_calculator import calculate_similarity

# Initialize FastAPI app
app = FastAPI(
    title="PDF Proofreading API",
    description="API for PDF comparison using SSIM",
    version="1.0.0"
)

# CORS configuration - allow all origins for now
# In production, restrict to your Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


class CompareResponse(BaseModel):
    success: bool
    similarity: float = 0
    bounds1: tuple[int, int, int, int] | None = None
    bounds2: tuple[int, int, int, int] | None = None
    confidence: float = 0
    method: str = "error"
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


# Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/convert", response_model=ConvertResponse)
async def convert_pdf(request: ConvertRequest):
    """
    Convert a PDF page to a PNG image.

    Args:
        request: ConvertRequest with base64 PDF and page number

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


@app.post("/api/compare", response_model=CompareResponse)
async def compare_images(request: CompareRequest):
    """
    Compare two images using SSIM.

    Args:
        request: CompareRequest with two base64 images

    Returns:
        CompareResponse with similarity score and metadata
    """
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
            error=result.get('error')
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
