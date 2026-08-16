import os

import httpx


EMBEDDING_PROVIDER = os.getenv(
    "EMBEDDING_PROVIDER",
    "huggingface",
).lower()

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

HF_EMBEDDING_URL = (
    "https://router.huggingface.co/"
    "hf-inference/models/"
    f"{EMBEDDING_MODEL}/pipeline/feature-extraction"
)


def _create_huggingface_embedding(text: str) -> list[float]:
    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is required when "
            "EMBEDDING_PROVIDER=huggingface"
        )

    response = httpx.post(
        HF_EMBEDDING_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "inputs": [text],
            "normalize": True,
            "truncate": True,
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Hugging Face embedding failed: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    if not data:
        raise RuntimeError(
            "Hugging Face returned an empty embedding"
        )

    # API normally returns [[...384 values...]]
    embedding = data[0] if isinstance(data[0], list) else data

    if len(embedding) != 384:
        raise RuntimeError(
            "Unexpected embedding dimension. "
            f"Expected 384, got {len(embedding)}"
        )

    return [float(value) for value in embedding]


def _create_local_embedding(text: str) -> list[float]:
    # Import ONLY when local embeddings are requested.
    # This prevents PyTorch / sentence-transformers from
    # loading into Render's memory.
    from sentence_transformers import SentenceTransformer

    if not hasattr(_create_local_embedding, "_model"):
        _create_local_embedding._model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    embedding = _create_local_embedding._model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()


def create_embedding(text: str) -> list[float]:
    text = (text or "").strip()

    if not text:
        raise ValueError(
            "Cannot create embedding for empty text"
        )

    if EMBEDDING_PROVIDER == "local":
        return _create_local_embedding(text)

    if EMBEDDING_PROVIDER == "huggingface":
        return _create_huggingface_embedding(text)

    raise RuntimeError(
        f"Unsupported EMBEDDING_PROVIDER: "
        f"{EMBEDDING_PROVIDER}"
    )