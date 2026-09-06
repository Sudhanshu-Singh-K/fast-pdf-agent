import pymupdf


def extract_pages(file_path: str) -> list[dict]:
    """
    Extract text from a PDF page-by-page.

    The page number is preserved so that we can
    trace information back to the original document.
    """

    pages = []

    with pymupdf.open(file_path) as pdf:

        for page_number, page in enumerate(pdf, start=1):

            text = page.get_text(
                "text",
                sort=True
            ).strip()

            pages.append({
                "page": page_number,
                "text": text
            })

    return pages