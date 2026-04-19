"""
AI-powered image analysis service using Claude Haiku vision.
Detects and describes printing errors between an original and a printed document.

Used for the Pro/Enterprise "AI Analysis" feature.
"""

import base64
import io
import json
import re
from PIL import Image
import anthropic

# Model to use — Haiku for speed and cost efficiency
AI_MODEL = "claude-haiku-4-5-20251001"

# System prompt for printing QC analysis
SYSTEM_PROMPT = """\
You are an expert in print quality control for PDF documents.
You will receive two images: the ORIGINAL design file and the PRINTED version.

Your task: identify real printing errors between the two.

Rules:
- Ignore minor differences in the outer 5% border (crop marks, bleeds, white margins).
- Focus on: text shifts, missing text or images, wrong images, color errors, rotation, cut-off content.
- If the images are essentially identical (no meaningful errors), return an empty issues array.
- Return ONLY valid JSON — no markdown, no prose, no code fences.

Return this exact JSON structure:
{
  "issues": [
    {
      "zone": {"x_pct": 0.0, "y_pct": 0.0, "w_pct": 0.0, "h_pct": 0.0},
      "type": "text_shift | missing_element | image_substitution | color_error | rotation | cutoff | other",
      "severity": "low | medium | high | critical",
      "false_positive": false,
      "description": "Brief description in French"
    }
  ],
  "summary": "One-sentence summary in French of the overall result"
}

Zone coordinates are percentages (0.0–1.0) of the image dimensions.
If no issues: return {"issues": [], "summary": "Aucune anomalie détectée."}
"""


def _resize_for_vision(img_bytes: bytes, max_size: int = 1024) -> str:
    """
    Resize image to max_size px on the longest side and return as base64 PNG.
    Claude vision performs well at 1024px and this keeps token cost low.
    """
    img = Image.open(io.BytesIO(img_bytes))
    img = img.convert('RGB')

    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def analyze_with_ai(
    img1_bytes: bytes,
    img2_bytes: bytes,
    model: str = AI_MODEL,
) -> dict:
    """
    Compare two images using Claude vision and return a structured analysis.

    Args:
        img1_bytes: Original image as PNG bytes
        img2_bytes: Printer image as PNG bytes
        model: Claude model ID to use

    Returns:
        Dict with keys:
          - issues: list of AIIssue dicts
          - summary: str
          - false_positive_count: int
          - model_used: str
    """
    try:
        client = anthropic.Anthropic()

        img1_b64 = _resize_for_vision(img1_bytes)
        img2_b64 = _resize_for_vision(img2_bytes)

        message = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Image 1 — ORIGINAL (fichier de référence) :",
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img1_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Image 2 — IMPRIMEUR (version imprimée à vérifier) :",
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img2_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Analyse les différences et retourne le JSON demandé.",
                        },
                    ],
                }
            ],
        )

        raw_text = message.content[0].text.strip()

        # Strip markdown code fences if model wraps in ```json ... ```
        raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)

        result = json.loads(raw_text)

        issues = result.get('issues', [])
        false_positive_count = sum(1 for i in issues if i.get('false_positive'))

        return {
            'issues': issues,
            'summary': result.get('summary', ''),
            'false_positive_count': false_positive_count,
            'model_used': model,
        }

    except json.JSONDecodeError as e:
        print(f"[AI] JSON parse error: {e} — raw: {raw_text[:200]}")
        return {
            'issues': [],
            'summary': 'Erreur lors de l\'analyse IA (réponse invalide).',
            'false_positive_count': 0,
            'model_used': model,
            'error': f'JSON parse error: {str(e)}',
        }
    except Exception as e:
        print(f"[AI] analyze_with_ai error: {e}")
        return {
            'issues': [],
            'summary': 'Erreur lors de l\'analyse IA.',
            'false_positive_count': 0,
            'model_used': model,
            'error': str(e),
        }
