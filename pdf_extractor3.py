import re
import time
from pathlib import Path

import pymupdf
import nltk

from nltk.tokenize import sent_tokenize, word_tokenize


# =========================================================
# NLTK SETUP
# =========================================================

def setup_nltk():
    packages = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
    ]

    for resource, package in packages:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(package, quiet=True)


setup_nltk()


# =========================================================
# BASIC NORMALIZATION
# =========================================================

def normalize_text(text):
    if not text:
        return ""

    # PDF non-breaking spaces
    text = text.replace("\xa0", " ")

    # Fix common PDF hyphenation across lines
    text = re.sub(r"-\s*\n\s*", "", text)

    # Normalize strange dash characters
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")

    # Remove PDF bullet characters
    text = re.sub(
        r"[•●▪◦■□►▶➢➤]",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_line(line):
    line = line.replace("\xa0", " ")

    line = re.sub(
        r"^[•●▪◦■□►▶➢➤]+\s*",
        "",
        line
    )

    line = re.sub(r"\s+", " ", line)

    return line.strip()


# =========================================================
# REMOVE FOUR-QUOTE BLOCKS
# =========================================================

def remove_quote_blocks(lines):
    """
    Removes anything marked with ''''.

    Handles both:

        ''''
        unwanted text
        ''''

    and:

        ''''1''''

    The marker line itself is ALWAYS removed.
    """

    result = []
    inside_quotes = False

    for raw_line in lines:

        line = normalize_line(raw_line)

        if not line:
            continue

        marker_count = line.count("''''")

        if marker_count:

            # Always discard the marker line.
            # Toggle only if there is an odd number
            # of markers on that line.
            if marker_count % 2 == 1:
                inside_quotes = not inside_quotes

            continue

        if inside_quotes:
            continue

        result.append(line)

    return result


# =========================================================
# DETECT BODY START
# =========================================================

def find_body_start(lines):

    for i, line in enumerate(lines):

        clean = normalize_line(line)
        lower = clean.lower()

        # Exact thesis heading
        if re.fullmatch(
            r"1\.\s*introduction",
            lower
        ):
            return i + 1

        # More general fallback
        if lower == "introduction":
            return i + 1

    # Other academic documents
    for i, line in enumerate(lines):

        lower = normalize_line(line).lower()

        if lower == "abstract":
            return i + 1

    # Last fallback
    return 0


# =========================================================
# DETECT REFERENCE / END SECTION
# =========================================================

def is_reference_heading(line):

    lower = normalize_line(line).lower()

    reference_patterns = [
        r"references",
        r"bibliography",
        r"works cited",
        r"reference list",
        r"\d+\.\s*references",
        r"\d+\.\s*bibliography",
        r"\d+\.\s*works cited",
    ]

    for pattern in reference_patterns:

        if re.fullmatch(pattern, lower):
            return True

    return False


# =========================================================
# REMOVE PAGE NUMBERS
# =========================================================

def is_page_number(line):

    line = normalize_line(line)

    if re.fullmatch(r"\d{1,4}", line):
        return True

    if re.fullmatch(
        r"page\s+\d{1,4}",
        line,
        re.IGNORECASE
    ):
        return True

    return False


# =========================================================
# REMOVE URL / EMAIL / DOI
# =========================================================

def contains_web_metadata(line):

    lower = line.lower()

    if re.search(
        r"https?://|www\.",
        lower
    ):
        return True

    if re.search(
        r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
        lower
    ):
        return True

    if "doi.org" in lower:
        return True

    if re.search(
        r"\bdoi\s*:",
        lower
    ):
        return True

    return False


# =========================================================
# REMOVE REFERENCE-STYLE LINES
# =========================================================

def looks_like_reference(line):

    clean = normalize_line(line)

    # [1] Reference
    if re.match(
        r"^\[\s*\d+\s*\]",
        clean
    ):
        return True

    # 1 Author, Title...
    if re.match(
        r"^\d{1,3}\s+[A-Z][A-Za-zÀ-ÿ'-]+,\s",
        clean
    ):
        return True

    # 1. Author...
    if re.match(
        r"^\d{1,3}\.\s+[A-Z][A-Za-zÀ-ÿ'-]+",
        clean
    ):
        return True

    return False


# =========================================================
# REMOVE FIGURE / TABLE CAPTIONS
# =========================================================

def looks_like_caption(line):

    lower = normalize_line(line).lower()

    if re.match(
        r"^(figure|fig\.?)\s*\d*",
        lower
    ):
        return True

    if re.match(
        r"^table\s*\d*",
        lower
    ):
        return True

    return False


# =========================================================
# REMOVE METADATA
# =========================================================

def looks_like_metadata(line):

    lower = normalize_line(line).lower()

    metadata_words = [
        "journal id",
        "article id",
        "issn",
        "e-issn",
        "impact factor",
        "view publication stats",
        "cite this article",
        "available online",
        "published by",
        "publication information",
        "copyright",
        "creative commons",
        "all rights reserved",
        "author information",
        "corresponding author",
        "supervisor",
        "assistant supervisor",
        "academic year",
        "graduand",
        "master's degree programme",
        "final thesis",
    ]

    for word in metadata_words:
        if word in lower:
            return True

    return False


# =========================================================
# REMOVE HEADINGS
# =========================================================

def looks_like_heading(line):

    clean = normalize_line(line)

    if not clean:
        return True

    # Numbered headings:
    #
    # 1. Introduction
    # 1.1 Research Context
    # 2.3 Platform Governance
    #
    if re.match(
        r"^\d+(?:\.\d+)*\.?\s+[A-Za-z]",
        clean
    ):
        return True

    # Common standalone headings
    heading_words = {
        "abstract",
        "introduction",
        "conclusion",
        "acknowledgements",
        "acknowledgments",
        "contents",
        "table of contents",
        "appendix",
    }

    if clean.lower() in heading_words:
        return True

    return False


# =========================================================
# REMOVE CITATION NUMBERS
# =========================================================

def remove_citation_numbers(text):

    # Examples:
    #
    # authenticity1.
    # regulation7
    # protection24.
    #
    # Remove small superscript-like numbers attached
    # to alphabetic text.

    text = re.sub(
        r"(?<=[A-Za-z\)])(\d{1,2})(?=[\.,;:\)])",
        "",
        text
    )

    # Citation immediately after a word before whitespace
    #
    # protection24 The
    #
    text = re.sub(
        r"(?<=[A-Za-z\)])(\d{1,2})(?=\s+[A-Z])",
        "",
        text
    )

    # Citation immediately before punctuation
    text = re.sub(
        r"(?<=[A-Za-z\)])\d{1,2}(?=[\.,;:])",
        "",
        text
    )

    return text


# =========================================================
# CLEAN BODY LINES
# =========================================================

def clean_body_lines(lines):

    cleaned = []

    for raw_line in lines:

        line = normalize_line(raw_line)

        if not line:
            continue

        # ---------------------------------------------
        # Page numbers
        # ---------------------------------------------

        if is_page_number(line):
            continue

        # ---------------------------------------------
        # URLs / emails / DOI
        # ---------------------------------------------

        if contains_web_metadata(line):
            continue

        # ---------------------------------------------
        # Reference-looking lines
        # ---------------------------------------------

        if looks_like_reference(line):
            continue

        # ---------------------------------------------
        # Figure/table captions
        # ---------------------------------------------

        if looks_like_caption(line):
            continue

        # ---------------------------------------------
        # Metadata
        # ---------------------------------------------

        if looks_like_metadata(line):
            continue

        # ---------------------------------------------
        # Remove obvious headings
        # ---------------------------------------------

        if looks_like_heading(line):
            continue

        # ---------------------------------------------
        # Citation numbers
        # ---------------------------------------------

        line = remove_citation_numbers(line)

        # ---------------------------------------------
        # Normalize again
        # ---------------------------------------------

        line = normalize_line(line)

        if line:
            cleaned.append(line)

    return cleaned


# =========================================================
# REMOVE REPEATED HEADERS / FOOTERS
# =========================================================

def remove_repeated_lines(lines):

    frequency = {}

    for line in lines:

        normalized = re.sub(
            r"\s+",
            " ",
            line.lower().strip()
        )

        # Don't count extremely short text
        if len(normalized) < 12:
            continue

        frequency[normalized] = (
            frequency.get(normalized, 0) + 1
        )

    result = []

    for line in lines:

        normalized = re.sub(
            r"\s+",
            " ",
            line.lower().strip()
        )

        # Repeated 4+ times is much safer than 3.
        if frequency.get(normalized, 0) >= 4:
            continue

        result.append(line)

    return result


# =========================================================
# REBUILD PARAGRAPHS
# =========================================================

def rebuild_paragraphs(lines):

    """
    PDF extraction produces visual lines.

    Example:

        The global expansion of e-commerce has not only
        transformed the way goods and services are exchanged
        but has also reshaped the institutional landscape.

    becomes:

        The global expansion of e-commerce has not only
        transformed the way goods and services are exchanged
        but has also reshaped the institutional landscape.

    as one continuous paragraph.
    """

    paragraphs = []

    current = []

    for line in lines:

        line = normalize_line(line)

        if not line:
            if current:
                paragraphs.append(
                    " ".join(current)
                )
                current = []

            continue

        current.append(line)

    if current:
        paragraphs.append(
            " ".join(current)
        )

    return paragraphs


# =========================================================
# SENTENCE TOKENIZATION
# =========================================================

def sentence_tokenize_text(paragraphs):

    sentences = []

    for paragraph in paragraphs:

        paragraph = normalize_text(paragraph)

        if not paragraph:
            continue

        try:
            parts = sent_tokenize(
                paragraph
            )
        except Exception:
            parts = [paragraph]

        for sentence in parts:

            sentence = sentence.strip()

            if len(sentence) < 3:
                continue

            sentences.append(sentence)

    return sentences


# =========================================================
# WORD TOKENIZATION
# =========================================================

def tokenize_sentence(sentence):

    # ---------------------------------------------
    # Replace separators
    # ---------------------------------------------

    sentence = re.sub(
        r"[-–—_/]",
        " ",
        sentence
    )

    # ---------------------------------------------
    # Remove citation numbers again
    # ---------------------------------------------

    sentence = remove_citation_numbers(
        sentence
    )

    # ---------------------------------------------
    # NLTK word tokenizer
    # ---------------------------------------------

    try:
        tokens = word_tokenize(
            sentence
        )
    except Exception:
        tokens = sentence.split()

    clean_tokens = []

    for token in tokens:

        # -----------------------------------------
        # Keep alphabetic words
        # -----------------------------------------

        if token.isalpha():
            clean_tokens.append(token)

        # -----------------------------------------
        # Keep integers
        # -----------------------------------------

        elif token.isdigit():
            clean_tokens.append(token)

        # -----------------------------------------
        # Keep decimal numbers
        # -----------------------------------------

        elif re.fullmatch(
            r"\d+\.\d+",
            token
        ):
            clean_tokens.append(token)

    return " ".join(
        clean_tokens
    )


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicate_lines(lines):

    result = []

    previous = None

    for line in lines:

        if line == previous:
            continue

        result.append(line)

        previous = line

    return result


# =========================================================
# MAIN EXTRACTION FUNCTION
# =========================================================

def func_extract(pdf_path):

    start_time = time.perf_counter()

    pdf_path = Path(pdf_path)

    # =====================================================
    # VALIDATION
    # =====================================================

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Input file must be a PDF."
        )

    # =====================================================
    # OUTPUT
    # =====================================================

    output_path = pdf_path.with_suffix(
        ".txt"
    )

    # =====================================================
    # EXTRACT PDF TEXT
    # =====================================================

    all_lines = []

    with pymupdf.open(pdf_path) as pdf:

        total_pages = len(pdf)

        for page in pdf:

            text = page.get_text(
                "text",
                sort=True
            )

            page_lines = text.splitlines()

            all_lines.extend(
                page_lines
            )

    print()
    print("Raw PDF lines:", len(all_lines))

    # =====================================================
    # REMOVE FOUR-QUOTE BLOCKS
    # =====================================================

    lines = remove_quote_blocks(
        all_lines
    )

    print(
        "After quote removal:",
        len(lines)
    )

    # =====================================================
    # FIND ACTUAL BODY
    # =====================================================

    body_start = find_body_start(
        lines
    )

    if body_start > 0:

        lines = lines[
            body_start:
        ]

    print(
        "Body starts at extracted line:",
        body_start
    )

    # =====================================================
    # REMOVE REFERENCE SECTION
    # =====================================================

    body_lines = []

    for line in lines:

        if is_reference_heading(line):
            break

        body_lines.append(line)

    lines = body_lines

    print(
        "After reference removal:",
        len(lines)
    )

    # =====================================================
    # CLEAN BODY
    # =====================================================

    lines = clean_body_lines(
        lines
    )

    print(
        "After cleaning:",
        len(lines)
    )

    # =====================================================
    # REMOVE REPEATED HEADERS / FOOTERS
    # =====================================================

    lines = remove_repeated_lines(
        lines
    )

    # =====================================================
    # REBUILD PARAGRAPHS
    # =====================================================

    paragraphs = rebuild_paragraphs(
        lines
    )

    print(
        "Paragraphs:",
        len(paragraphs)
    )

    # =====================================================
    # SENTENCE TOKENIZATION
    # =====================================================

    sentences = sentence_tokenize_text(
        paragraphs
    )

    print(
        "Sentences:",
        len(sentences)
    )

    # =====================================================
    # WORD TOKENIZATION
    # =====================================================

    final_lines = []

    for sentence in sentences:

        tokens = tokenize_sentence(
            sentence
        )

        if tokens:

            final_lines.append(
                tokens
            )

    # =====================================================
    # REMOVE DUPLICATE CONSECUTIVE SENTENCES
    # =====================================================

    final_lines = remove_duplicate_lines(
        final_lines
    )

    # =====================================================
    # WRITE OUTPUT
    # =====================================================

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as output:

        for line in final_lines:

            output.write(
                line
            )

            output.write(
                "\n"
            )

    # =====================================================
    # STATISTICS
    # =====================================================

    elapsed = (
        time.perf_counter()
        - start_time
    )

    token_count = sum(
        len(line.split())
        for line in final_lines
    )

    print()
    print(
        "======================================"
    )
    print(
        "PDF EXTRACTION COMPLETE"
    )
    print(
        "======================================"
    )
    print(
        f"PDF       : {pdf_path.name}"
    )
    print(
        f"Pages     : {total_pages}"
    )
    print(
        f"Sentences : {len(final_lines)}"
    )
    print(
        f"Tokens    : {token_count}"
    )
    print(
        f"Time      : {elapsed:.2f} seconds"
    )
    print(
        f"Output    : {output_path}"
    )
    print(
        "======================================"
    )
    print()

    return str(output_path)


# =========================================================
# DIRECT EXECUTION
# =========================================================

if __name__ == "__main__":

    pdf = input(
        "Enter PDF path: "
    ).strip()

    func_extract(pdf)