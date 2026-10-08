import re


KNOWN_GENRES = [
    "science fiction",
    "action",
    "adventure",
    "animation",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "family",
    "fantasy",
    "history",
    "horror",
    "music",
    "mystery",
    "romance",
    "thriller",
    "war",
    "western",
]


def parse_query(query):
    original_query = query
    semantic_query = query

    result = {
        "original_query": original_query,
        "semantic_query": "",
        "min_year": None,
        "max_year": None,
        "min_rating": None,
        "max_rating": None,
        "min_runtime": None,
        "max_runtime": None,
        "director": None,
        "actor": None,
        "person": None,
        "genre": None,
        "sort_by": None,
    }

    # =========================================================
    # YEAR
    # =========================================================

    match = re.search(
        r"\bafter\s+(?:the\s+year\s+)?(19\d{2}|20\d{2})\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["min_year"] = int(match.group(1)) + 1
        semantic_query = semantic_query.replace(match.group(0), "")

    match = re.search(
        r"\bbefore\s+(?:the\s+year\s+)?(19\d{2}|20\d{2})\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["max_year"] = int(match.group(1)) - 1
        semantic_query = semantic_query.replace(match.group(0), "")

    match = re.search(
        r"\b(?:from|since)\s+(?:the\s+year\s+)?(19\d{2}|20\d{2})\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["min_year"] = int(match.group(1))
        semantic_query = semantic_query.replace(match.group(0), "")

    match = re.search(
        r"\bin\s+(19\d{2}|20\d{2})\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match and result["min_year"] is None:
        year = int(match.group(1))
        result["min_year"] = year
        result["max_year"] = year
        semantic_query = semantic_query.replace(match.group(0), "")

    # =========================================================
    # RATING
    # =========================================================

    match = re.search(
        r"\b(?:rated|rating)\s+"
        r"(?:above|over|higher\s+than)\s+"
        r"(\d+(?:\.\d+)?)\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["min_rating"] = float(match.group(1))
        semantic_query = semantic_query.replace(match.group(0), "")

    match = re.search(
        r"\babove\s+(\d+(?:\.\d+)?)\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match and result["min_rating"] is None:
        result["min_rating"] = float(match.group(1))
        semantic_query = semantic_query.replace(match.group(0), "")

    match = re.search(
        r"\b(?:rated|rating)\s+"
        r"(?:below|under|lower\s+than)\s+"
        r"(\d+(?:\.\d+)?)\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["max_rating"] = float(match.group(1))
        semantic_query = semantic_query.replace(match.group(0), "")

    # =========================================================
    # RUNTIME — HOURS
    # =========================================================

    match = re.search(
        r"\b(?:under|less\s+than|below)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:hours?|hrs?)\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["max_runtime"] = float(match.group(1)) * 60
        semantic_query = semantic_query.replace(match.group(0), "")

    # =========================================================
    # RUNTIME — MINUTES
    # =========================================================

    match = re.search(
        r"\b(?:under|less\s+than|below)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:minutes?|mins?)\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["max_runtime"] = float(match.group(1))
        semantic_query = semantic_query.replace(match.group(0), "")

    # =========================================================
    # MINIMUM RUNTIME
    # =========================================================

    match = re.search(
        r"\b(?:at\s+least|minimum|more\s+than|over)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:minutes?|mins?)\b",
        semantic_query,
        re.IGNORECASE,
    )
    if match:
        result["min_runtime"] = float(match.group(1))
        semantic_query = semantic_query.replace(match.group(0), "")



    # ---------------------------------------------------------
    # Temporal intent
    # ---------------------------------------------------------
    latest_match = re.search(
        r"\b(latest|newest|most recent|recent)\b",
        semantic_query,
        re.IGNORECASE
    )

    if latest_match:
        result["sort_by"] = "release_date_desc"

        semantic_query = re.sub(
            r"\b(latest|newest|most recent|recent)\b",
            "",
            semantic_query,
            flags=re.IGNORECASE
        )

    # =========================================================
    # GENRE
    # IMPORTANT: detect this BEFORE person/director parsing
    # =========================================================

    for genre in sorted(KNOWN_GENRES, key=len, reverse=True):
        pattern = rf"\b{re.escape(genre)}\b"

        match = re.search(
            pattern,
            semantic_query,
            re.IGNORECASE,
        )

        if match:
            result["genre"] = genre
            semantic_query = (
                semantic_query[:match.start()]
                + " "
                + semantic_query[match.end():]
            )
            break

    # =========================================================
    # ACTOR — explicit phrases
    # =========================================================

    match = re.search(
        r"\b(?:movies?|films?)\s+"
        r"(?:starring)\s+"
        r"([A-Za-z][A-Za-z .'-]*[A-Za-z])"
        r"(?=\s+(?:after|before|from|since|in)\s+\d{4}\b|$)",
        semantic_query,
        re.IGNORECASE,
    )

    if match:
        result["actor"] = match.group(1).strip()
        semantic_query = semantic_query.replace(match.group(0), "")

    # =========================================================
    # PERSON — "[name] movies" / "[name] latest movie"
    #
    # We do not guess actor vs director here.
    # TMDB will resolve the person's profession later.
    #
    # Examples:
    # Yash latest movie
    # Tamanna Bhatia latest movie
    # Yash movies after 2020
    # Tamanna Bhatia movies after 2020
    # Christopher Nolan movies after 2010
    # =========================================================

    if result["actor"] is None and result["director"] is None:
        match = re.search(
            r"^\s*("
            r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            r")"
            r"(?=\s+(?:latest|newest|recent)\s+movies?\b"
            r"|\s+movies?\b)",
            semantic_query,
        )

        if match:
            result["person"] = match.group(1).strip()
            semantic_query = semantic_query.replace(
                match.group(0),
                "",
                1,
            )


    # =========================================================
    # DIRECTOR — explicit phrases
    # =========================================================

    match = re.search(
        r"\b(?:movies?|films?)\s+"
        r"(?:directed\s+by|directed\s+from|by)\s+"
        r"([A-Za-z][A-Za-z .'-]*[A-Za-z])"
        r"(?=\s+(?:after|before|from|since|in)\s+\d{4}\b|$)",
        semantic_query,
        re.IGNORECASE,
    )

    if match:
        result["director"] = match.group(1).strip()
        semantic_query = semantic_query.replace(match.group(0), "")



    # =========================================================
    # CLEAN SEMANTIC QUERY
    # =========================================================

    semantic_query = re.sub(
        r"\b(?:give me|show me|find me|i want|i need|looking for)\b",
        "",
        semantic_query,
        flags=re.IGNORECASE,
    )

    semantic_query = re.sub(
        r"\bmovies?\b",
        "",
        semantic_query,
        flags=re.IGNORECASE,
    )

    semantic_query = re.sub(
        r"\s+",
        " ",
        semantic_query,
    )

    semantic_query = re.sub(
        r"[,.]+",
        " ",
        semantic_query,
    )

    semantic_query = re.sub(
        r"\s+",
        " ",
        semantic_query,
    )

    semantic_query = semantic_query.strip(" ,.-")

    result["semantic_query"] = semantic_query

    return result