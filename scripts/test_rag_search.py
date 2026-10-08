import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DOCUMENTS_FILE = DATA_DIR / "movie_documents.jsonl"
EMBEDDINGS_FILE = DATA_DIR / "movie_embeddings.npy"
INDEX_FILE = DATA_DIR / "movie_index.faiss"

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
    print("MovieVerse - RAG Semantic Search Test")
    print("=" * 60)

    print("\nLoading documents...")
    documents = load_documents()

    print(f"Documents: {len(documents)}")

    print("\nLoading FAISS index...")
    index = faiss.read_index(str(INDEX_FILE))

    print(f"FAISS vectors: {index.ntotal}")

    print("\nLoading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("\nRAG search is ready.")
    print("Type 'exit' to stop.\n")

    while True:

        query = input("Search: ").strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        query_embedding = model.encode(
            [query],
            normalize_embeddings=True
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        scores, indices = index.search(
            query_embedding,
            5
        )

        print("\nTop results:")
        print("-" * 60)

        for rank, (index_id, score) in enumerate(
            zip(indices[0], scores[0]),
            start=1
        ):

            movie = documents[index_id]

            print(
                f"{rank}. {movie['title']} "
                f"(score: {score:.4f})"
            )

        print()


if __name__ == "__main__":
    main()