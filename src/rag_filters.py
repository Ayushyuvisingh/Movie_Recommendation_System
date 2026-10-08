from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CATALOG_FILE = DATA_DIR / "movie_catalog.csv"


def load_catalog():
    """Load the structured movie metadata."""

    return pd.read_csv(CATALOG_FILE)


def filter_movies(
    movies,
    min_year=None,
    max_year=None,
    min_rating=None,
    max_rating=None,
    max_runtime=None,
    min_runtime=None,
    genre=None,
    language=None,
    director=None,
    actor=None,
):
    """
    Apply structured filters to the movie catalog.

    All filters are optional.
    """

    filtered = movies.copy()

    # Release year
    if min_year is not None:
        filtered = filtered[
            filtered["release_year"] >= min_year
        ]

    if max_year is not None:
        filtered = filtered[
            filtered["release_year"] <= max_year
        ]

    # Rating
    if min_rating is not None:
        filtered = filtered[
            filtered["vote_average"] >= min_rating
        ]

    if max_rating is not None:
        filtered = filtered[
            filtered["vote_average"] <= max_rating
        ]

    # Runtime
    if max_runtime is not None:
        filtered = filtered[
            filtered["runtime"] <= max_runtime
        ]

    if min_runtime is not None:
        filtered = filtered[
            filtered["runtime"] >= min_runtime
        ]

    # Genre
    if genre:
        genre_mask = filtered["genres"].fillna("").str.contains(
            genre,
            case=False,
            na=False,
        )

        filtered = filtered[genre_mask]

    # Language
    if language:
        filtered = filtered[
            filtered["original_language"]
            .fillna("")
            .str.lower()
            == language.lower()
        ]

    # Director
    if director:
        director_mask = filtered["director"].fillna("").str.contains(
            director,
            case=False,
            na=False,
        )

        filtered = filtered[director_mask]

    # Actor
    if actor:
        actor_mask = filtered["cast"].fillna("").str.contains(
            actor,
            case=False,
            na=False,
        )

        filtered = filtered[actor_mask]

    return filtered.reset_index(drop=True)


def print_results(results, limit=10):
    """Print filtered movies for testing."""

    print(f"\nMovies found: {len(results)}")
    print("-" * 60)

    for _, movie in results.head(limit).iterrows():
        print(
            f"{movie['title']} | "
            f"{movie['release_year']} | "
            f"Rating: {movie['vote_average']} | "
            f"Runtime: {movie['runtime']} min"
        )