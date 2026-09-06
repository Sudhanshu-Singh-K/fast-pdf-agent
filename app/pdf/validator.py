from pathlib import Path
import pymupdf


def has_pdf_signature(file_path: str) -> bool:
    """
    Quickly check whether the uploaded file has
    the standard PDF file signature.
    """

    path = Path(file_path)

    try:
        with path.open("rb") as file:
            header = file.read(5)

        return header == b"%PDF-"

    except OSError:
        return False


def validate_pdf(file_path: str) -> tuple[bool, str]:
    """
    Perform complete PDF validation.

    Returns:
        (True, "Valid PDF") if valid
        (False, reason) if invalid
    """

    path = Path(file_path)

    # Check that the file exists
    if not path.exists():
        return False, "File does not exist."

    # Check PDF signature
    if not has_pdf_signature(file_path):
        return False, "File is not a genuine PDF."

    # Try opening the document with PyMuPDF
    try:
        with pymupdf.open(file_path) as pdf:

            if pdf.page_count == 0:
                return False, "PDF contains no pages."

    except Exception:
        return False, "PDF is corrupted or cannot be opened."

    return True, "Valid PDF."