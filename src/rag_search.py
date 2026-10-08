import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.rag_filters import load_catalog, filter_movies
from src.query_parser import parse_query


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DOCUMENTS_FILE = DATA_DIR / "movie_documents.jsonl"
INDEX_FILE = DATA_DIR / "movie_index.faiss"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class RAGSearchEngine:

    def __init__(self):

        print("Loading movie documents...")
        self.documents = self._load_documents()
        print(f"Documents loaded: {len(self.documents)}")

        print("\nLoading FAISS index...")
        self.index = faiss.read_index(
            str(INDEX_FILE)
        )
        print(f"FAISS vectors: {self.index.ntotal}")


        print("\nLoading embeddings...")
        self.embeddings = np.load(
            DATA_DIR / "movie_embeddings.npy"
    )

        print("\nLoading embedding model...")

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        print("\nLoading movie catalog...")

        self.catalog = load_catalog()

        print(f"Catalog movies: {len(self.catalog)}")

    # =========================================================
    # LOAD DOCUMENTS
    # =========================================================

    def _load_documents(self):

        documents = []

        with open(
            DOCUMENTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if line.strip():

                    documents.append(
                        json.loads(line)
                    )

        return documents

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query,
        top_k=5,
        candidate_k=100
    ):

        print("\n" + "=" * 60)
        print("QUERY")
        print("=" * 60)

        print(query)

        # -----------------------------------------------------
        # 1. Parse query
        # -----------------------------------------------------

        parsed = parse_query(query)

        print("\nParsed query:")
        print(parsed)

        # -----------------------------------------------------
        # 2. Apply structured filters
        # -----------------------------------------------------

        filtered_catalog = filter_movies(
            self.catalog,

            min_year=parsed["min_year"],
            max_year=parsed["max_year"],

            min_rating=parsed["min_rating"],
            max_rating=parsed["max_rating"],

            max_runtime=parsed["max_runtime"],
            min_runtime=parsed["min_runtime"],

            genre=parsed["genre"],
            director=parsed["director"],
            actor=parsed["actor"],
        )

        print(
            f"\nMovies after structured filtering: "
            f"{len(filtered_catalog)}"
        )

        # -----------------------------------------------------
        # 3. Get allowed TMDB IDs
        # -----------------------------------------------------

        allowed_ids = set(
            filtered_catalog["tmdb_id"]
            .astype(int)
            .tolist()
        )

        # -----------------------------------------------------
        # 4. Semantic search
        # -----------------------------------------------------

        semantic_query = parsed["semantic_query"]

        # If structured filters consumed almost the entire
        # query, use the original query as fallback.
        if not semantic_query.strip():

            semantic_query = query

        query_embedding = self.model.encode(
            [semantic_query],
            normalize_embeddings=True
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        # -----------------------------------------------------
        # 5. Search larger candidate pool
        # -----------------------------------------------------

        # Get document indices that passed structured filtering
        allowed_indices = []

        for i, movie in enumerate(self.documents):
            tmdb_id = int(movie["metadata"]["tmdb_id"])

            if tmdb_id in allowed_ids:
                allowed_indices.append(i)

        if not allowed_indices:
            return []

        # Get embeddings only for allowed candidates
        candidate_embeddings = self.embeddings[allowed_indices]

        # Semantic similarity
        candidate_scores = np.dot(
            candidate_embeddings,
            query_embedding[0]
        )

        # Rank highest similarity first
        ranked_positions = np.argsort(
            candidate_scores
        )[::-1]

        results = []

        for position in ranked_positions[:top_k]:

            document_index = allowed_indices[position]

            movie = self.documents[document_index]

            results.append({
                "title": movie["title"],
                "tmdb_id": int(movie["metadata"]["tmdb_id"]),
                "score": float(candidate_scores[position]),
                "release_year": movie["metadata"].get("release_year"),
                "runtime": movie["metadata"].get("runtime"),
                "rating": movie["metadata"].get("vote_average"),
            })

        return results