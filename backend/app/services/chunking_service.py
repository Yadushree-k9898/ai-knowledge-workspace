def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: The full document text.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if not text or not text.strip():
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If this is not the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for the last period, newline, or question mark within the chunk
            for sep in ["\n\n", "\n", ". ", "? ", "! "]:
                last_break = text.rfind(sep, start, end)
                if last_break != -1:
                    end = last_break + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, accounting for overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks
