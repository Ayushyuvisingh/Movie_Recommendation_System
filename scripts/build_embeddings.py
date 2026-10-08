import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DOCUMENTS_FILE = DATA_DIR / "movie_documents.jsonl"
EMBEDDINGS_FILE = DATA_DIR / "movie_embeddings.npy"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_documents():
    documents = []

    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                documents.append(json.loads(line))

    return documents


def main():
    print("=" * 60)
    print("MovieVerse - Embedding Builder")
    print("=" * 60)

    print("\nLoading movie documents...")

    documents = load_documents()

    print(f"Documents loaded: {len(documents)}")

    texts = [doc["text"] for doc in documents]

    print(f"\nLoading embedding model:")
    print(MODEL_NAME)

    model = SentenceTransformer(MODEL_NAME)

    print("\nGenerating embeddings...")
    print("This may take some time on the first run.")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    print("\nEmbedding generation complete.")

    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding dtype: {embeddings.dtype}")

    np.save(EMBEDDINGS_FILE, embeddings)

    print("\nEmbeddings saved to:")
    print(EMBEDDINGS_FILE)

    print("\n" + "=" * 60)
    print("EMBEDDING BUILD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()