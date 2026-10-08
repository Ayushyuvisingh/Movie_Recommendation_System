import csv
import pickle
import time
from pathlib import Path

from tqdm import tqdm

from src.tmdb import get_movie_catalog_data


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MOVIE_DICT_PATH = BASE_DIR / "data" / "movie_dict.pkl"
OUTPUT_PATH = BASE_DIR / "data" / "movie_catalog.csv"
FAILED_PATH = BASE_DIR / "data" / "movie_catalog_failed.csv"


# ============================================================
# SETTINGS
# ============================================================

REQUEST_DELAY = 0.15

FIELDNAMES = [
    "tmdb_id",
    "title",
    "original_title",
    "overview",
    "tagline",
    "release_date",
    "release_year",
    "runtime",
    "vote_average",
    "vote_count",
    "popularity",
    "original_language",
    "genres",
    "cast",
    "director",
    "keywords",
    "existing_tags",
    "poster_path",
]


# ============================================================
# HELPERS
# ============================================================

def load_original_movies():
    """Load the existing MovieVerse dataset."""

    with open(MOVIE_DICT_PATH, "rb") as file:
        data = pickle.load(file)

    movie_ids = data["movie_id"]
    titles = data["title"]
    tags = data["tags"]

    movies = []

    for index in movie_ids:
        movies.append(
            {
                "tmdb_id": int(movie_ids[index]),
                "title": titles[index],
                "existing_tags": tags[index],
            }
        )

    return movies


def load_completed_ids():
    """Return TMDB IDs already successfully saved."""

    if not OUTPUT_PATH.exists():
        return set()

    completed_ids = set()

    with open(
        OUTPUT_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            try:
                completed_ids.add(int(row["tmdb_id"]))
            except (ValueError, TypeError):
                continue

    return completed_ids


def extract_movie_record(movie, original_movie):
    """Convert TMDB response into our MovieVerse catalog format."""

    release_date = movie.get("release_date") or ""

    release_year = ""

    if release_date:
        release_year = release_date[:4]

    # -------------------------
    # Genres
    # -------------------------

    genres = movie.get("genres", [])

    genre_names = [
        genre.get("name")
        for genre in genres
        if genre.get("name")
    ]

    # -------------------------
    # Cast
    # -------------------------

    credits = movie.get("credits", {})

    cast = credits.get("cast", [])

    cast_names = [
        person.get("name")
        for person in cast[:15]
        if person.get("name")
    ]

    # -------------------------
    # Director
    # -------------------------

    crew = credits.get("crew", [])

    directors = [
        person.get("name")
        for person in crew
        if person.get("job") == "Director"
        and person.get("name")
    ]

    # -------------------------
    # Keywords
    # -------------------------

    keyword_data = movie.get("keywords", {})

    keywords = keyword_data.get("keywords", [])

    keyword_names = [
        keyword.get("name")
        for keyword in keywords
        if keyword.get("name")
    ]

    # -------------------------
    # Final record
    # -------------------------

    return {
        "tmdb_id": movie.get("id"),
        "title": movie.get("title")
        or original_movie["title"],
        "original_title": movie.get("original_title", ""),
        "overview": movie.get("overview", ""),
        "tagline": movie.get("tagline", ""),
        "release_date": release_date,
        "release_year": release_year,
        "runtime": movie.get("runtime") or "",
        "vote_average": movie.get("vote_average") or "",
        "vote_count": movie.get("vote_count") or "",
        "popularity": movie.get("popularity") or "",
        "original_language": movie.get(
            "original_language",
            "",
        ),
        "genres": " | ".join(genre_names),
        "cast": " | ".join(cast_names),
        "director": " | ".join(directors),
        "keywords": " | ".join(keyword_names),
        "existing_tags": original_movie["existing_tags"],
        "poster_path": movie.get("poster_path") or "",
    }


def ensure_output_file():
    """Create the catalog file with headers if needed."""

    if OUTPUT_PATH.exists():
        return

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()


def save_failed_movie(tmdb_id, title, error):
    """Append a failed movie to the failure log."""

    file_exists = FAILED_PATH.exists()

    with open(
        FAILED_PATH,
        "a",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "tmdb_id",
                "title",
                "error",
            ],
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "tmdb_id": tmdb_id,
                "title": title,
                "error": str(error),
            }
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("MovieVerse - Movie Catalog Builder")
    print("=" * 60)

    print("\nLoading existing movie dataset...")

    movies = load_original_movies()

    print(f"Movies in original dataset: {len(movies)}")

    ensure_output_file()

    completed_ids = load_completed_ids()

    print(
        f"Already completed: "
        f"{len(completed_ids)}"
    )

    remaining_movies = [
        movie
        for movie in movies
        if movie["tmdb_id"] not in completed_ids
    ]

    print(
        f"Remaining to process: "
        f"{len(remaining_movies)}"
    )

    if not remaining_movies:
        print("\nEverything is already completed.")
        return

    print("\nStarting TMDB enrichment...")
    print(
        "The process is resumable. "
        "You can safely stop and restart it."
    )

    successful = 0
    failed = 0

    with open(
        OUTPUT_PATH,
        "a",
        encoding="utf-8",
        newline="",
    ) as output_file:

        writer = csv.DictWriter(
            output_file,
            fieldnames=FIELDNAMES,
        )

        progress = tqdm(
            remaining_movies,
            desc="Enriching movies",
            unit="movie",
        )

        for original_movie in progress:

            tmdb_id = original_movie["tmdb_id"]
            title = original_movie["title"]

            try:

                data = get_movie_catalog_data(
                    tmdb_id
                )

                if not data:

                    raise RuntimeError(
                        "TMDB returned no data"
                    )

                record = extract_movie_record(
                    data,
                    original_movie,
                )

                writer.writerow(record)

                # Make sure the row reaches disk
                # immediately.
                output_file.flush()

                successful += 1

                progress.set_postfix(
                    success=successful,
                    failed=failed,
                )

            except Exception as error:

                failed += 1

                save_failed_movie(
                    tmdb_id,
                    title,
                    error,
                )

                progress.set_postfix(
                    success=successful,
                    failed=failed,
                )

            # Be respectful of TMDB.
            time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 60)
    print("CATALOG BUILD COMPLETE")
    print("=" * 60)

    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")

    print(f"\nCatalog:")
    print(OUTPUT_PATH)

    if failed:
        print("\nFailed movies:")
        print(FAILED_PATH)


if __name__ == "__main__":
    main()