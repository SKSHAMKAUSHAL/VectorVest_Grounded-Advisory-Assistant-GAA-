import re
from typing import List, Dict, Any

# Regex pattern matching standard legal/regulatory clause headers:
# - Section X.Y or Section X
# - Clause X.Y or Clause X
# - Article X.Y or Article X
# - Decimal numbered clauses like 1.1, 4.2.1
CLAUSE_PATTERN = r"(?=(?:^|\n)[ \t]*(?:Section|Clause|Article|\b[0-9]{1,2}\.[0-9]{1,2})\b)"

HEADER_MATCH_PATTERN = r"(?:^|\n)[ \t]*((?:Section|Clause|Article|\b[0-9]{1,2}\.[0-9]{1,2})\b[^\n:]*)"

def clean_text(text: str) -> str:
    """Normalizes whitespace, strips line margins, and removes empty blank runs."""
    if not text:
        return ""
    # Strip whitespace from each individual line to prevent indentation from breaking header detection
    lines = [line.strip() for line in text.splitlines()]
    normalized = "\n".join(lines)
    # Collapse 3+ consecutive newlines to 2
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()

def chunk_page_text_by_clause(
    text: str,
    page_number: int,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> List[Dict[str, Any]]:
    """
    Splits text from a single page into clause-bounded chunks.
    If a clause section exceeds max_tokens, applies sliding window overlap fallback.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    sections = re.split(CLAUSE_PATTERN, cleaned, flags=re.IGNORECASE)
    chunks: List[Dict[str, Any]] = []
    current_clause_id = f"Page {page_number}"

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract explicit header if present
        header_match = re.search(HEADER_MATCH_PATTERN, section, flags=re.IGNORECASE)
        if header_match:
            current_clause_id = header_match.group(1).strip()
            # Remove trailing dots or colons
            current_clause_id = current_clause_id.rstrip(".:-")

        words = section.split()
        if len(words) <= max_tokens:
            chunks.append({
                "clause_id": current_clause_id,
                "text": section,
                "page_number": page_number,
                "word_count": len(words),
            })
        else:
            # Fallback for large clause sections: sliding window
            step = max_tokens - overlap_tokens
            if step <= 0:
                step = max_tokens
            for i in range(0, len(words), step):
                window_words = words[i:i + max_tokens]
                sub_text = " ".join(window_words)
                sub_clause = current_clause_id if i == 0 else f"{current_clause_id} (Part {i // step + 1})"
                chunks.append({
                    "clause_id": sub_clause,
                    "text": sub_text,
                    "page_number": page_number,
                    "word_count": len(window_words),
                })

    return chunks

def chunk_document_pages(
    pages: List[Dict[str, Any]],
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> List[Dict[str, Any]]:
    """
    Takes a list of page dicts [{"page_number": 1, "text": "..."}] and
    generates a unified, ordered list of clause chunks with global chunk_index.
    """
    all_chunks: List[Dict[str, Any]] = []
    global_index = 0

    for page in pages:
        page_num = page.get("page_number", 1)
        raw_text = page.get("text", "")
        page_chunks = chunk_page_text_by_clause(
            text=raw_text,
            page_number=page_num,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )
        for chunk in page_chunks:
            chunk["chunk_index"] = global_index
            all_chunks.append(chunk)
            global_index += 1

    return all_chunks
