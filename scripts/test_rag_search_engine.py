from src.rag_search import RAGSearchEngine


def print_results(results):

    print("\nFINAL RESULTS")
    print("=" * 60)

    if not results:

        print("No matching movies found.")

        return

    for rank, movie in enumerate(
        results,
        start=1
    ):

        print(
            f"{rank}. {movie['title']}"
        )

        print(
            f"   Year: {movie['release_year']} | "
            f"Runtime: {movie['runtime']} min | "
            f"Rating: {movie['rating']} | "
            f"Semantic score: {movie['score']:.4f}"
        )


def main():

    print("=" * 60)
    print("MovieVerse - Hybrid RAG Search Test")
    print("=" * 60)

    engine = RAGSearchEngine()

    queries = [
        # Semantic + genre
        "funny adventure movie with pirates and treasure",

        # Semantic + genre
        "emotional family movie",

        # Director + year
        "Christopher Nolan movies after 2010",

        # Explicit director
        "movies directed by Christopher Nolan",

        # Actor
        "movies starring Leonardo DiCaprio",

        # Genre + year
        "action movies after 2010",

        # Pure structured filters
        "movies rated above 8",

        # No local results expected because dataset is old
        "Give me movies after 2018, under 2 hours, rated above 7, that feel like a dark psychological thriller",
    ]

    for query in queries:

        results = engine.search(
            query,
            top_k=5,
            candidate_k=100
        )

        print_results(results)

        print("\n")


if __name__ == "__main__":
    main()