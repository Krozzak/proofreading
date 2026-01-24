# PDF Proofreading API Backend

FastAPI backend for PDF comparison using SSIM (Structural Similarity Index).

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run locally

```bash
uvicorn main:app --reload --port 8000
```

API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### `GET /api/health`
Health check endpoint.

### `POST /api/convert`
Convert a PDF page to PNG image.

**Request:**
```json
{
  "pdf": "<base64-encoded-pdf>",
  "page": 0
}
```

**Response:**
```json
{
  "success": true,
  "image": "<base64-encoded-png>",
  "totalPages": 5,
  "page": 0
}
```

### `POST /api/compare`
Compare two images using SSIM.

**Request:**
```json
{
  "image1": "<base64-encoded-png>",
  "image2": "<base64-encoded-png>",
  "autoCrop": true
}
```

**Response:**
```json
{
  "success": true,
  "similarity": 95.5,
  "bounds1": [10, 20, 790, 780],
  "bounds2": [15, 25, 785, 775],
  "confidence": 0.9,
  "method": "threshold"
}
```

## Deploy to Google Cloud Run

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed and configured
- Docker installed (for local builds)

### Option 1: Deploy with Cloud Build (Recommended)

```bash
cd backend

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

### Option 2: Manual deployment

```bash
# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/proofreading-api

# Deploy to Cloud Run
gcloud run deploy proofreading-api \
  --image gcr.io/YOUR_PROJECT_ID/proofreading-api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --min-instances 0 \
  --max-instances 10
```

### Get the API URL

After deployment, Cloud Run will provide a URL like:
`https://proofreading-api-xxxxx-ew.a.run.app`

Use this URL in your frontend `.env.local`:
```
NEXT_PUBLIC_API_URL=https://proofreading-api-xxxxx-ew.a.run.app
```

## Cost Optimization

Cloud Run charges only when processing requests:
- **Min instances: 0** - No cost when idle
- **Memory: 1Gi** - Sufficient for PDF processing
- **Timeout: 300s** - Allow time for large PDFs

Estimated costs:
- Free tier: 2 million requests/month
- After free tier: ~$0.00002400 per GB-second
