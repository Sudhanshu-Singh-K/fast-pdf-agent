from app.pdf.validator import validate_pdf
from app.pdf.extractor import extract_pages
from app.pdf.processor import process_pages, build_document_text


PDF_PATH = "test.pdf"


# ---------------------------------------
# STEP 1: VALIDATE
# ---------------------------------------

valid, message = validate_pdf(PDF_PATH)

print("\nPDF VALIDATION")
print("----------------")
print(message)

if not valid:
    print("❌ Pipeline stopped.")
    exit()


# ---------------------------------------
# STEP 2: EXTRACT
# ---------------------------------------

pages = extract_pages(PDF_PATH)

print("\nPDF EXTRACTION")
print("----------------")
print(f"Extracted pages: {len(pages)}")


# ---------------------------------------
# STEP 3: PROCESS
# ---------------------------------------

processed_pages = process_pages(pages)

print("\nTEXT PROCESSING")
print("----------------")
print(f"Pages containing text: {len(processed_pages)}")


# ---------------------------------------
# STEP 4: BUILD AI CONTEXT
# ---------------------------------------

document_text = build_document_text(processed_pages)

print("\nAI CONTEXT")
print("----------------")
print(f"Characters prepared for AI: {len(document_text)}")

print("\nPreview:")
print(document_text[:1000])