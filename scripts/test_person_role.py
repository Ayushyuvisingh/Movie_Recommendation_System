from src.tmdb_rag import resolve_person_role


def main():
    names = [
        "Yash",
        "Tamanna Bhatia",
        "Christopher Nolan",
    ]

    for name in names:
        print("=" * 60)
        print(f"Testing: {name}")

        try:
            result = resolve_person_role(name)
            print(result)

        except Exception as e:
            print(f"Temporary TMDB error: {e}")
            print("Skipping this person and continuing...")


if __name__ == "__main__":
    main()