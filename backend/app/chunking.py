def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
):
    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        if end >= len(text):
            break

        start = end - overlap

    return chunks
