from src.rag_filters import load_catalog, filter_movies, print_results


def main():

    print("=" * 60)
    print("MovieVerse - Structured Filter Test")
    print("=" * 60)

    movies = load_catalog()

    print(f"\nTotal movies: {len(movies)}")

    # Test 1
    print("\n\nTEST 1: Movies after 2018")
    results = filter_movies(
        movies,
        min_year=2019,
    )
    print_results(results)

    # Test 2
    print("\n\nTEST 2: Movies rated 8 or higher")
    results = filter_movies(
        movies,
        min_rating=8,
    )
    print_results(results)

    # Test 3
    print("\n\nTEST 3: Movies under 120 minutes")
    results = filter_movies(
        movies,
        max_runtime=120,
    )
    print_results(results)

    # Test 4
    print("\n\nTEST 4: Action movies after 2020")
    results = filter_movies(
        movies,
        min_year=2021,
        genre="Action",
    )
    print_results(results)

    # Test 5
    print("\n\nTEST 5: Movies after 2010, rating >= 7.5, under 150 minutes")
    results = filter_movies(
        movies,
        min_year=2011,
        min_rating=7.5,
        max_runtime=150,
    )
    print_results(results)


if __name__ == "__main__":
    main()