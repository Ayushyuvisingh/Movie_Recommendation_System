from src.tmdb import TMDBTemporaryError
from src.tmdb_rag import discover_tmdb_movies


def print_results(title, results):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    print(f"Results: {len(results)}")

    if not results:
        print("No results found.")
        return

    for rank, movie in enumerate(results[:10], start=1):

        print(
            f"{rank}. "
            f"{movie.get('title')} | "
            f"Year: {movie.get('release_date', '')[:4]} | "
            f"Rating: {movie.get('vote_average')} | "
            f"Popularity: {movie.get('popularity')}"
        )


def run_test(title, **filters):

    try:

        results = discover_tmdb_movies(
            **filters
        )

        print_results(
            title,
            results,
        )

    except TMDBTemporaryError as error:

        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)

        print(
            f"TMDB temporarily unavailable: {error}"
        )


def main():

    print("=" * 70)
    print("MovieVerse - TMDB Director Test")
    print("=" * 70)

    run_test(
        "Christopher Nolan movies after 2010",

        min_year=2011,
        director="Christopher Nolan",
    )


if __name__ == "__main__":
    main()