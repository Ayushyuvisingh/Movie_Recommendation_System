import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

CATALOG_PATH = DATA_DIR / "movie_catalog.csv"
OUTPUT_PATH = DATA_DIR / "movie_documents.jsonl"


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """Convert missing values to an empty string."""

    if pd.isna(value):
        return ""

    return str(value).strip()


def build_movie_document(row):
    """
    Convert one catalog row into a semantic movie document.
    """

    title = clean_value(row["title"])
    original_title = clean_value(row["original_title"])
    overview = clean_value(row["overview"])
    tagline = clean_value(row["tagline"])
    release_year = clean_value(row["release_year"])
    runtime = clean_value(row["runtime"])
    rating = clean_value(row["vote_average"])
    language = clean_value(row["original_language"])

    genres = clean_value(row["genres"])
    cast = clean_value(row["cast"])
    director = clean_value(row["director"])
    keywords = clean_value(row["keywords"])
    existing_tags = clean_value(row["existing_tags"])

    # --------------------------------------------------------
    # Semantic text
    # --------------------------------------------------------

    sections = []

    if title:
        sections.append(f"Title: {title}")

    if original_title and original_title.lower() != title.lower():
        sections.append(
            f"Original title: {original_title}"
        )

    if release_year:
        sections.append(
            f"Release year: {release_year}"
        )

    if runtime:
        sections.append(
            f"Runtime: {runtime} minutes"
        )

    if rating:
        sections.append(
            f"Rating: {rating} out of 10"
        )

    if language:
        sections.append(
            f"Original language: {language}"
        )

    if genres:
        sections.append(
            f"Genres: {genres}"
        )

    if director:
        sections.append(
            f"Director: {director}"
        )

    if cast:
        sections.append(
            f"Cast: {cast}"
        )

    if keywords:
        sections.append(
            f"Keywords: {keywords}"
        )

    if tagline:
        sections.append(
            f"Tagline: {tagline}"
        )

    if overview:
        sections.append(
            f"Overview: {overview}"
        )

    if existing_tags:
        sections.append(
            f"Additional movie tags: {existing_tags}"
        )

    semantic_text = "\n".join(sections)

    # --------------------------------------------------------
    # Structured metadata
    # --------------------------------------------------------

    metadata = {
        "tmdb_id": int(row["tmdb_id"]),
        "title": title,
        "release_year": release_year,
        "runtime": runtime,
        "vote_average": rating,
        "original_language": language,
        "genres": genres,
        "director": director,
        "cast": cast,
        "keywords": keywords,
    }

    return {
        "tmdb_id": int(row["tmdb_id"]),
        "title": title,
        "text": semantic_text,
        "metadata": metadata,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("MovieVerse - RAG Document Builder")
    print("=" * 60)

    # --------------------------------------------------------
    # Load catalog
    # --------------------------------------------------------

    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Catalog not found:\n{CATALOG_PATH}"
        )

    print("\nLoading movie catalog...")

    df = pd.read_csv(CATALOG_PATH)

    print(f"Movies loaded: {len(df)}")

    # --------------------------------------------------------
    # Validate TMDB IDs
    # --------------------------------------------------------

    if df["tmdb_id"].duplicated().any():

        duplicate_count = (
            df["tmdb_id"]
            .duplicated()
            .sum()
        )

        raise ValueError(
            f"Found {duplicate_count} "
            "duplicate TMDB IDs.\n"
            "Clean movie_catalog.csv before "
            "building RAG documents."
        )

    # --------------------------------------------------------
    # Build documents
    # --------------------------------------------------------

    print("\nBuilding movie documents...")

    documents = []

    for _, row in df.iterrows():

        document = build_movie_document(row)

        documents.append(document)

    # --------------------------------------------------------
    # Save JSONL
    # --------------------------------------------------------

    print("\nSaving documents...")

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        for document in documents:

            file.write(
                json.dumps(
                    document,
                    ensure_ascii=False,
                )
                + "\n"
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RAG DOCUMENT BUILD COMPLETE")
    print("=" * 60)

    print(f"Documents created: {len(documents)}")
    print(f"Output file:")
    print(OUTPUT_PATH)

    # --------------------------------------------------------
    # Preview first 3
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DOCUMENT PREVIEW")
    print("=" * 60)

    for document in documents[:3]:

        print("\n" + "-" * 60)

        print(
            f"TMDB ID: {document['tmdb_id']}"
        )

        print(
            f"Title: {document['title']}"
        )

        print("\nSemantic text:")

        print(document["text"])


if __name__ == "__main__":
    main()