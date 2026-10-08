from src.tmdb import tmdb_request


def get_full_tmdb_movie(movie_id):
    """
    Fetch complete movie information needed for RAG.

    Includes:
    - Basic movie details
    - Credits
    - Keywords
    """

    return tmdb_request(
        f"movie/{movie_id}",
        params={
            "language": "en-US",
            "append_to_response": "credits,keywords",
        },
    )


def tmdb_movie_to_document(movie):
    """
    Convert a full TMDB movie response into the text format
    used by MovieVerse RAG.
    """

    title = movie.get("title", "")
    release_date = movie.get("release_date", "")
    release_year = release_date[:4] if release_date else ""

    runtime = movie.get("runtime")
    vote_average = movie.get("vote_average")
    original_language = movie.get("original_language", "")

    # ---------------------------------------------------------
    # GENRES
    # ---------------------------------------------------------

    genres = movie.get("genres", [])

    genre_text = " | ".join(
        genre.get("name", "")
        for genre in genres
        if genre.get("name")
    )

    # ---------------------------------------------------------
    # CREDITS
    # ---------------------------------------------------------

    credits = movie.get("credits", {})

    cast = credits.get("cast", [])
    crew = credits.get("crew", [])

    cast_text = " | ".join(
        person.get("name", "")
        for person in cast[:10]
        if person.get("name")
    )

    directors = [
        person.get("name", "")
        for person in crew
        if person.get("job") == "Director"
        and person.get("name")
    ]

    director_text = " | ".join(directors)

    # ---------------------------------------------------------
    # KEYWORDS
    # ---------------------------------------------------------

    keywords_data = movie.get("keywords", {})

    keywords = keywords_data.get("keywords", [])

    keyword_text = " | ".join(
        keyword.get("name", "")
        for keyword in keywords
        if keyword.get("name")
    )

    # ---------------------------------------------------------
    # OTHER FIELDS
    # ---------------------------------------------------------

    tagline = movie.get("tagline", "")
    overview = movie.get("overview", "")

    # ---------------------------------------------------------
    # FINAL RAG DOCUMENT
    # ---------------------------------------------------------

    return f"""
Title: {title}
Year: {release_year}
Runtime: {runtime} minutes
Rating: {vote_average}
Language: {original_language}
Genres: {genre_text}
Director: {director_text}
Cast: {cast_text}
Keywords: {keyword_text}
Tagline: {tagline}
Overview: {overview}
""".strip()