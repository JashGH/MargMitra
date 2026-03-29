"""
MargMitra - Main Orchestrator API (Port 8000)
--------------------------------------------
This is YOUR service. It:
  1. Receives an image from the frontend
  2. Sends it to the OCR service (port 8001) → gets extracted text
  3. Sends that text to the Transliteration service (port 8002) → gets converted script
  4. Saves the result to the local SQLite database
  5. Returns the full result to the frontend

Run with:
    uvicorn main:app --port 8000 --reload

Interactive API docs available at:
    http://localhost:8000/docs
"""

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from database import delete_scan, get_all_scans, get_scan_by_id, get_stats, init_db, save_scan

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MargMitra - Main API",
    description="Orchestrator: OCR → Transliteration → Database",
    version="1.0.0",
)

# Allow the frontend (HTML file opened in browser) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs — change only if teammates run on different ports
OCR_SERVICE_URL       = "http://localhost:8001/ocr"
TRANSLIT_SERVICE_URL  = "http://localhost:8002/transliterate"

# Supported language codes (Google Input Tools codes)
SUPPORTED_LANGS = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "kn": "Kannada",
    "pa": "Punjabi",
    "mr": "Marathi",
    "or": "Odia",
    "ur": "Urdu",
}


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    print("[MargMitra] Main API running on port 8000")
    print(f"[MargMitra] OCR service    → {OCR_SERVICE_URL}")
    print(f"[MargMitra] Translit service → {TRANSLIT_SERVICE_URL}")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
def root():
    return {
        "status": "running",
        "service": "MargMitra Main API",
        "port": 8000,
        "docs": "http://localhost:8000/docs"
    }


@app.get("/health", summary="Check if all services are reachable")
async def health():
    results = {}
    async with httpx.AsyncClient(timeout=3) as client:
        for name, url in [("ocr", "http://localhost:8001"), ("transliteration", "http://localhost:8002")]:
            try:
                r = await client.get(url)
                results[name] = "online" if r.status_code < 500 else "error"
            except Exception:
                results[name] = "offline — make sure the service is running"
    results["database"] = "online"
    return results


# ── MAIN ENDPOINT: Scan a signboard ──────────────────────────────────────────

@app.post("/scan", summary="Scan a signboard image end-to-end")
async def scan(
    image: UploadFile = File(..., description="Photo of a street sign"),
    target_lang: str  = Form(default="hi", description="Target language code e.g. hi, ta, te, bn")
):
    """
    Full pipeline:
      Image → OCR (port 8001) → Transliteration (port 8002) → Save to DB → Return result
    """

    # Validate language
    if target_lang not in SUPPORTED_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{target_lang}'. Choose from: {list(SUPPORTED_LANGS.keys())}"
        )

    # Validate file type
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    # ── Step 1: OCR ──────────────────────────────────────────────────────────
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            ocr_response = await client.post(
                OCR_SERVICE_URL,
                files={"image": (image.filename, image_bytes, image.content_type or "image/jpeg")}
            )
            ocr_response.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="OCR service is offline. Run: uvicorn main:app --port 8001 in the ocr folder."
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"OCR service error: {e.response.text}")

    extracted_text = ocr_response.json().get("text", "").strip()
    if not extracted_text:
        raise HTTPException(status_code=422, detail="No text found in the image. Try a clearer photo.")

    # ── Step 2: Transliteration ───────────────────────────────────────────────
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            translit_response = await client.post(
                TRANSLIT_SERVICE_URL,
                json={"text": extracted_text, "target_lang": target_lang}
            )
            translit_response.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Transliteration service is offline. Run: uvicorn main:app --port 8002 in the translit folder."
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Transliteration service error: {e.response.text}")

    transliterated_text = translit_response.json().get("output", extracted_text)

    # ── Step 3: Save to database ──────────────────────────────────────────────
    scan_id = save_scan(
        original=extracted_text,
        transliterated=transliterated_text,
        target_lang=target_lang,
        image_name=image.filename
    )

    # ── Step 4: Return result ─────────────────────────────────────────────────
    return {
        "scan_id":        scan_id,
        "original":       extracted_text,
        "transliterated": transliterated_text,
        "target_lang":    target_lang,
        "language_name":  SUPPORTED_LANGS[target_lang],
        "image":          image.filename,
        "status":         "success"
    }


# ── History endpoints ─────────────────────────────────────────────────────────

@app.get("/history", summary="Get all past scan results")
def history():
    """Returns all saved scans, newest first. Used by the History tab in the app."""
    scans = get_all_scans()
    return {"total": len(scans), "scans": scans}


@app.get("/history/{scan_id}", summary="Get one scan by ID")
def history_item(scan_id: int):
    scan = get_scan_by_id(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan #{scan_id} not found.")
    return scan


@app.delete("/history/{scan_id}", summary="Delete a scan by ID")
def delete_history_item(scan_id: int):
    deleted = delete_scan(scan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Scan #{scan_id} not found.")
    return {"message": f"Scan #{scan_id} deleted successfully."}


@app.get("/stats", summary="Get usage statistics for the home screen")
def stats():
    """Returns total scans and number of languages used."""
    return get_stats()


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
