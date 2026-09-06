def optimize_context(
    pages: list[dict],
    max_characters: int = 100000
) -> str:
    """
    Prepare PDF content for the AI.

    Small and medium documents are kept almost entirely intact.
    Very large documents are bounded to prevent unnecessarily
    large AI requests.
    """

    sections = []
    total_characters = 0

    for page in pages:

        page_text = page["text"].strip()

        if not page_text:
            continue

        section = (
            f"[Page {page['page']}]\n"
            f"{page_text}"
        )

        section_length = len(section)

        # Stop before exceeding the context limit
        if total_characters + section_length > max_characters:

            remaining = max_characters - total_characters

            if remaining > 500:

                sections.append(
                    section[:remaining]
                )

            break

        sections.append(section)

        total_characters += section_length

    return "\n\n".join(sections)