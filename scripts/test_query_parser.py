from src.query_parser import parse_query


def main():

    queries = [
        "Give me movies after 2018, under 2 hours, rated above 7, that feel like a dark psychological thriller",
        "funny adventure movie with pirates and treasure",
        "Christopher Nolan movies after 2010",
        "movies directed by Christopher Nolan",
        "movies starring Yash",
        "Yash movies after 2020",
        "action movies after 2015",
        "science fiction movies",
        "movies before 2000",
        "movies from 2015",
        "movies under 120 minutes",
        "movies rated above 8",
        "emotional family movie after 2015",
        "Yash latest movie",
        "Tamanna Bhatia latest movie",
    ]

    print("=" * 70)
    print("MovieVerse - Query Parser Test")
    print("=" * 70)

    for query in queries:

        result = parse_query(query)

        print("\nQuery:")
        print(query)

        print("\nParsed:")
        print(f"Semantic query : {result['semantic_query']}")
        print(f"Min year       : {result['min_year']}")
        print(f"Max year       : {result['max_year']}")
        print(f"Min rating     : {result['min_rating']}")
        print(f"Max rating     : {result['max_rating']}")
        print(f"Min runtime    : {result['min_runtime']}")
        print(f"Max runtime    : {result['max_runtime']}")
        print(f"Director       : {result['director']}")
        print(f"Actor          : {result['actor']}")
        print(f"Genre          : {result['genre']}")
        print(f"Person         : {result.get('person')}")
        print(f"Sort by        : {result.get('sort_by')}")

        print("-" * 70)


if __name__ == "__main__":
    main()