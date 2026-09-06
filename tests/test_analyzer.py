from app.pdf.validator import validate_pdf
from app.pdf.extractor import extract_pages
from app.pdf.processor import process_pages
from app.ai.analyzer import analyze_document
import time 


PDF_PATH = "test.pdf"


# ---------------------------------------
# 1. VALIDATE
# ---------------------------------------

valid, message = validate_pdf(PDF_PATH)

if not valid:
    print("❌", message)
    exit()

print("✅ PDF validated")


# ---------------------------------------
# 2. EXTRACT
# ---------------------------------------

pages = extract_pages(PDF_PATH)

print(f"✅ Extracted {len(pages)} pages")


# ---------------------------------------
# 3. PROCESS
# ---------------------------------------

processed_pages = process_pages(pages)

print(
    f"✅ Processed {len(processed_pages)} pages"
)


# ---------------------------------------
# 4. PREPARE AI CONTEXT
# ---------------------------------------

from app.pdf.context import optimize_context

document_text = optimize_context(
    processed_pages
)

print(
    f"✅ Prepared {len(document_text)} characters for AI"
)


# ---------------------------------------
# 5. AI ANALYSIS
# ---------------------------------------

print("\n🤖 Analyzing document...\n")

start = time.perf_counter()

description = analyze_document(
    processed_pages
)

elapsed = time.perf_counter() - start

print(f"\n⏱️ AI analysis time: {elapsed:.2f} seconds")


# ---------------------------------------
# 6. DISPLAY RESULT
# ---------------------------------------

print("=" * 60)
print("DOCUMENT DESCRIPTION")
print("=" * 60)

print(description)

print("=" * 60)