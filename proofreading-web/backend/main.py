"""
FastAPI backend for PDF Proofreading application.
Handles PDF to image conversion and SSIM similarity calculation.
Now with Firebase authentication and quota management.

Deploy to Google Cloud Run for serverless execution.
"""

import base64
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
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


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
