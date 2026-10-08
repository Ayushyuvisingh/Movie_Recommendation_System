import numpy as np

from src.tmdb_documents import (
    get_full_tmdb_movie,
    tmdb_movie_to_document,
)

from src.tmdb_embeddings import (
    load_embedding_model,
    embed_tmdb_document,
)


def main():

    movie_id = 157336  # Interstellar

    print("=" * 70)
    print("TMDB → EMBEDDING TEST")
    print("=" * 70)

    print("\nFetching movie details...")

    movie = get_full_tmdb_movie(movie_id)

    if not movie:
        print("Failed to fetch movie.")
        return

    document = tmdb_movie_to_document(movie)

    print(f"Movie: {movie.get('title')}")
    print("Document created successfully.")

    print("\nLoading embedding model...")

    model = load_embedding_model()

    print("Embedding model loaded.")

    print("\nCreating embedding...")

    embedding = embed_tmdb_document(
        document,
        model=model,
    )

    print("\nEmbedding created successfully.")

    print("Shape:", embedding.shape)
    print("Dtype:", embedding.dtype)

    norm = np.linalg.norm(embedding[0])

    print("Vector norm:", norm)

    print("\nFirst 10 values:")
    print(embedding[0][:10])


if __name__ == "__main__":
    main()