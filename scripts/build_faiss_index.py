from pathlib import Path

import faiss
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

EMBEDDINGS_FILE = DATA_DIR / "movie_embeddings.npy"
INDEX_FILE = DATA_DIR / "movie_index.faiss"


def main():
    print("=" * 60)
    print("MovieVerse - FAISS Index Builder")
    print("=" * 60)

    print("\nLoading embeddings...")

    embeddings = np.load(EMBEDDINGS_FILE)

    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Embeddings dtype: {embeddings.dtype}")

    # Number of dimensions in each embedding
    dimension = embeddings.shape[1]

    print(f"\nVector dimension: {dimension}")

    # Because our embeddings were normalized during encoding,
    # inner product is equivalent to cosine similarity.
    index = faiss.IndexFlatIP(dimension)

    print("\nBuilding FAISS index...")

    index.add(embeddings)

    print(f"Vectors added: {index.ntotal}")

    faiss.write_index(index, str(INDEX_FILE))

    print("\nFAISS index saved to:")
    print(INDEX_FILE)

    print("\n" + "=" * 60)
    print("FAISS INDEX BUILD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()