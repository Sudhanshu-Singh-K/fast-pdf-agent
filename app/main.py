from pathlib import Path
import time

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.pdf.validator import validate_pdf
from app.pdf.extractor import extract_pages
from app.pdf.processor import process_pages
from app.ai.analyzer import analyze_document
from app.pdf.context import optimize_context


app = FastAPI(
    title="Fast PDF Analyzer",
    description="Fast PDF-only document analysis system"
)


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"

UPLOAD_DIR.mkdir(exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB


@app.get("/", response_class=HTMLResponse)
async def home():

    index_file = STATIC_DIR / "index.html"

    return index_file.read_text(
        encoding="utf-8"
    )


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # -----------------------------------------
    # 1. READ FILE
    # -----------------------------------------

    data = await file.read(MAX_FILE_SIZE + 1)


    # -----------------------------------------
    # 2. SIZE VALIDATION
    # -----------------------------------------

    if len(data) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="PDF is too large. Maximum size is 30 MB."
        )


    # -----------------------------------------
    # 3. FAST SIGNATURE CHECK
    # -----------------------------------------

    if not data.startswith(b"%PDF-"):

        raise HTTPException(
            status_code=415,
            detail="Rejected: only genuine PDF files are accepted."
        )


    # -----------------------------------------
    # 4. SAVE TEMPORARY PDF
    # -----------------------------------------

    file_path = UPLOAD_DIR / "current_upload.pdf"

    file_path.write_bytes(data)


    # -----------------------------------------
    # 5. COMPLETE PDF VALIDATION
    # -----------------------------------------

    valid, message = validate_pdf(
        str(file_path)
    )

    if not valid:

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=415,
            detail=f"Rejected: {message}"
        )


    # -----------------------------------------
    # 6. EXTRACT TEXT
    # -----------------------------------------

    extraction_start = time.perf_counter()

    pages = extract_pages(
        str(file_path)
    )

    extraction_time = (
        time.perf_counter()
        - extraction_start
    ) * 1000


    # -----------------------------------------
    # 7. PROCESS TEXT
    # -----------------------------------------

    processed_pages = process_pages(
        pages
    )


    # -----------------------------------------
    # 8. OPTIMIZE AI CONTEXT
    # -----------------------------------------

    document_context = optimize_context(
        processed_pages
    )


    # -----------------------------------------
    # 9. AI ANALYSIS
    # -----------------------------------------

    analysis_start = time.perf_counter()

    description = analyze_document(
    processed_pages
    )

    analysis_time = (
        time.perf_counter()
        - analysis_start
    ) * 1000


    # -----------------------------------------
    # 10. RETURN RESULT
    # -----------------------------------------

    return {
        "description": description,
        "pages": len(pages),
        "extraction_time_ms": round(
            extraction_time,
            2
        ),
        "analysis_time_ms": round(
            analysis_time,
            2
        )
    }