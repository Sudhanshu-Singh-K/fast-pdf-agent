import os
from app.pdf.context import optimize_context

from dotenv import load_dotenv
from google import genai


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )


client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.6-flash"


def analyze_document(pages: list[dict]) -> str:
    """
    Analyze the processed PDF text and return
    a natural-language description.
    """

    document_text = optimize_context(pages)

    if not document_text.strip():
        return (
            "The PDF does not contain enough extractable text "
            "to generate a description."
        )

    prompt = f"""
You are a fast and accurate PDF document analyzer.

Read the document provided below and explain what it is
about in simple, natural language.

Your response must be plain text.

Do NOT return JSON.
Do NOT use key-value pairs.
Do NOT create a dictionary-like response.

Give the user a useful description of the document.

Cover, when the information is available:

- What the document is about
- Its main purpose
- The most important ideas or information
- The type of document, if it can be determined
- Any important conclusion, finding, or recommendation

Keep the explanation concise and easy to understand.

Do not invent information that is not present in the document.

DOCUMENT:

{document_text}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    return response.text.strip()

