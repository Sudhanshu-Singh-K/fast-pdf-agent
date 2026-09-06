import re


def clean_page_text(text: str) -> str:
    """
    Clean extracted PDF text while preserving
    the actual document content.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def process_pages(pages: list[dict]) -> list[dict]:
    """
    Clean extracted pages and remove completely
    empty pages.
    """

    processed_pages = []

    for page in pages:

        cleaned_text = clean_page_text(page["text"])

        # Ignore pages containing no extractable text
        if not cleaned_text:
            continue

        processed_pages.append({
            "page": page["page"],
            "text": cleaned_text
        })

    return processed_pages


def build_document_text(pages: list[dict]) -> str:
    """
    Combine processed pages into one AI-ready document.

    Page markers are preserved so the AI knows
    where information came from.
    """

    sections = []

    for page in pages:

        sections.append(
            f"[Page {page['page']}]\n"
            f"{page['text']}"
        )

    return "\n\n".join(sections)