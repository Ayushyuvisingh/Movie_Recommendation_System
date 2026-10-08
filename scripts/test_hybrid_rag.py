from src.hybrid_rag import HybridRAG


def main():

    print("=" * 70)
    print("MOVIEVERSE HYBRID RAG TEST")
    print("=" * 70)

    rag = HybridRAG()

    queries = [
        "Yash latest movie",
        "Yash latest movies",
        "Yash latest movie rated above 7",
        "Yash movies after 2018",
        "movies starring Tamanna Bhatia",
        "Christopher Nolan movies",
        "science fiction movies after 2020",
        "action movies rated above 7",
    ]

    for query in queries:

        print("\nQuery:")
        print(query)

        print("\nSearching...")

        results = rag.search(
            query,
            top_k=10,
        )

        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("=" * 70)

        for rank, result in enumerate(results, start=1):

            print(
                f"{rank}. "
                f"{result.get('title')} | "
                f"Score: {result.get('score'):.4f} | "
                f"Source: {result.get('source')}"
            )


if __name__ == "__main__":
    main()