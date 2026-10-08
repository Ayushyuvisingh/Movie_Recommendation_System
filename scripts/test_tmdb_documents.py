from src.tmdb_documents import (
    get_full_tmdb_movie,
    tmdb_movie_to_document,
)


def main():

    movie_id = 157336

    print("=" * 70)
    print("TMDB → RAG DOCUMENT TEST")
    print("=" * 70)

    print(f"Testing TMDB movie ID: {movie_id}")
    print("\nFetching full movie details...")

    full_movie = get_full_tmdb_movie(movie_id)

    if not full_movie:
        print("Failed to fetch full movie details.")
        return

    print("Full movie details received.")

    print("\nGenerated RAG document:")
    print("-" * 70)

    document = tmdb_movie_to_document(full_movie)

    print(document)

    print("-" * 70)


if __name__ == "__main__":
    main()