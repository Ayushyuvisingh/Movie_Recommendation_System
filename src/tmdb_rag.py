import time
from src.tmdb import TMDBTemporaryError
from src.tmdb import tmdb_request



# =========================================================
# GENRE CACHE
# =========================================================

_genre_cache = None


def get_tmdb_genres():
    """
    Get TMDB movie genre names and IDs.
    """
    global _genre_cache

    if _genre_cache is not None:
        return _genre_cache

    data = tmdb_request(
        "genre/movie/list",
        params={
            "language": "en-US",
        },
    )

    if not data:
        return {}

    _genre_cache = {
        genre["name"].lower(): genre["id"]
        for genre in data.get("genres", [])
    }

    return _genre_cache


# =========================================================
# PERSON SEARCH
# =========================================================

def search_tmdb_person(name):
    """
    Resolve a person name to the best matching TMDB person.
    """

    data = tmdb_request(
        "search/person",
        params={
            "query": name,
            "language": "en-US",
            "include_adult": False,
            "page": 1,
        },
    )

    if not data:
        return None

    results = data.get("results", [])

    if not results:
        return None

    search_name = name.strip().lower()

    # -----------------------------------------------------
    # EXACT NAME MATCH
    # -----------------------------------------------------

    for person in results:
        person_name = str(
            person.get("name", "")
        ).strip().lower()

        if person_name == search_name:
            return person

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    return results[0]


# =========================================================
# PERSON ID
# =========================================================

def get_person_id(name):
    person = search_tmdb_person(name)

    if not person:
        return None

    return person.get("id")


# =========================================================
# PERSON ROLE RESOLUTION
# =========================================================

def resolve_person_role(name):
    """
    Resolve a person's TMDB identity and determine whether
    they are primarily an actor or director.

    TMDB's known_for_department is preferred because a person
    can have both acting and directing credits.

    Returns:
        {
            "name": str,
            "person_id": int | None,
            "role": "actor" | "director" | None,
        }
    """

    person = search_tmdb_person(name)

    if not person:
        return {
            "name": name,
            "person_id": None,
            "role": None,
        }

    person_id = person.get("id")

    if not person_id:
        return {
            "name": person.get("name", name),
            "person_id": None,
            "role": None,
        }

    # ---------------------------------------------------------
    # PRIMARY ROLE — TMDB's known_for_department
    # ---------------------------------------------------------

    department = str(
        person.get("known_for_department", "")
    ).strip().lower()

    if department == "directing":
        return {
            "name": person.get("name", name),
            "person_id": person_id,
            "role": "director",
        }

    if department == "acting":
        return {
            "name": person.get("name", name),
            "person_id": person_id,
            "role": "actor",
        }

    # ---------------------------------------------------------
    # FALLBACK — inspect movie credits
    # ---------------------------------------------------------

    credits = get_person_movie_credits(person_id)

    cast_credits = credits.get("cast", [])
    crew_credits = credits.get("crew", [])

    director_count = 0
    actor_count = 0

    for credit in crew_credits:
        job = str(
            credit.get("job", "")
        ).strip().lower()

        if job == "director":
            director_count += 1

    for credit in cast_credits:
        if credit.get("character") is not None:
            actor_count += 1

    if director_count > actor_count:
        role = "director"
    elif actor_count > 0:
        role = "actor"
    else:
        role = None

    return {
        "name": person.get("name", name),
        "person_id": person_id,
        "role": role,
    }

# =========================================================
# PERSON MOVIE CREDITS
# =========================================================

def get_person_movie_credits(person_id):
    """
    Get all movie credits for a TMDB person.
    """
    data = tmdb_request(
        f"person/{person_id}/movie_credits",
        params={
            "language": "en-US",
        },
    )

    if not data:
        return {}

    return data


# =========================================================
# DIRECTOR MOVIE IDS
# =========================================================

def get_directed_movie_ids(person_id):
    """
    Return movie IDs where this person is explicitly credited
    as a Director.
    """

    credits = get_person_movie_credits(person_id)

    crew_credits = credits.get("crew", [])

    directed_movie_ids = set()

    for credit in crew_credits:

        job = str(
            credit.get("job", "")
        ).strip().lower()

        if job == "director":

            movie_id = credit.get("id")

            if movie_id:
                directed_movie_ids.add(
                    int(movie_id)
                )

    return directed_movie_ids




# =========================================================
# DISCOVER PERSON MOVIES
# =========================================================

def discover_tmdb_person_movies(
    person_id,
    role,
    min_year=None,
    max_year=None,
    min_rating=None,
    max_rating=None,
    min_runtime=None,
    max_runtime=None,
    genre=None,
    sort_by="popularity.desc",
):
    """
    Discover movies associated with a specific TMDB person.

    role:
        "actor" or "director"

    Uses the person's movie credits instead of relying on
    the first page of discover/movie.
    """

    credits = get_person_movie_credits(person_id)

    if not credits:
        return []

    # -----------------------------------------------------
    # SELECT RELEVANT CREDITS
    # -----------------------------------------------------

    if role == "actor":
        movie_credits = credits.get("cast", [])

    elif role == "director":
        movie_credits = [
            credit
            for credit in credits.get("crew", [])
            if str(
                credit.get("job", "")
            ).strip().lower() == "director"
        ]

    else:
        return []

    # -----------------------------------------------------
    # REMOVE DUPLICATES + FUTURE RELEASES
    # -----------------------------------------------------

    from datetime import date

    today = date.today().isoformat()

    unique_movies = {}

    for movie in movie_credits:

        movie_id = movie.get("id")

        if not movie_id:
            continue

        release_date = movie.get(
            "release_date",
            ""
        )

        # Ignore movies without a known release date.
        if not release_date:
            continue

        # Ignore future/unreleased movies.
        if release_date > today:
            continue

        unique_movies[int(movie_id)] = movie

    candidate_movies = list(
        unique_movies.values()
    )

    # -----------------------------------------------------
    # SORT BY RELEASE DATE
    # -----------------------------------------------------

    if sort_by == "release_date_desc":

        candidate_movies.sort(
            key=lambda movie: movie.get(
                "release_date",
                ""
            ),
            reverse=True,
        )

        # For a latest query, the credit data already
        # contains the movie information we need.
        return candidate_movies

    # -----------------------------------------------------
    # SORT BY POPULARITY
    # -----------------------------------------------------

    candidate_movies.sort(
        key=lambda movie: movie.get(
            "popularity",
            0
        ),
        reverse=True,
    )

    # -----------------------------------------------------
    # APPLY DETAILED FILTERS
    # -----------------------------------------------------

    genre_id = None

    if genre:
        genres = get_tmdb_genres()

        genre_id = genres.get(
            genre.lower()
        )

    results = []

    for movie in candidate_movies:

        movie_id = movie.get("id")

        try:
            full_movie = get_tmdb_movie_details(
                movie_id
            )
        except TMDBTemporaryError:
            print(
                f"Skipping movie {movie_id}: "
                f"temporary TMDB connection error."
            )
            continue

        if not full_movie:
            continue

        release_date = full_movie.get(
            "release_date",
            ""
        )

        if not release_date:
            continue

        year = int(
            release_date[:4]
        )

        # YEAR
        if (
            min_year is not None
            and year < min_year
        ):
            continue

        if (
            max_year is not None
            and year > max_year
        ):
            continue

        # RATING
        rating = full_movie.get(
            "vote_average"
        )

        if (
            min_rating is not None
            and (
                rating is None
                or rating < min_rating
            )
        ):
            continue

        if (
            max_rating is not None
            and (
                rating is None
                or rating > max_rating
            )
        ):
            continue

        # RUNTIME
        runtime = full_movie.get(
            "runtime"
        )

        if (
            min_runtime is not None
            and (
                runtime is None
                or runtime < min_runtime
            )
        ):
            continue

        if (
            max_runtime is not None
            and (
                runtime is None
                or runtime > max_runtime
            )
        ):
            continue

        # GENRE
        if genre_id is not None:

            movie_genres = full_movie.get(
                "genres",
                []
            )

            movie_genre_ids = {
                item.get("id")
                for item in movie_genres
            }

            if genre_id not in movie_genre_ids:
                continue

        results.append(
            full_movie
        )

        time.sleep(0.3)

    return results


# =========================================================
# MOVIE DETAILS
# =========================================================

def get_tmdb_movie_details(movie_id):
    """
    Get full details for a TMDB movie.
    """

    return tmdb_request(
        f"movie/{movie_id}",
        params={
            "language": "en-US",
        },
    )


# =========================================================
# DISCOVER DIRECTOR MOVIES
# =========================================================

def discover_tmdb_director_movies(
    director,
    min_year=None,
    max_year=None,
    min_rating=None,
    max_rating=None,
    min_runtime=None,
    max_runtime=None,
    genre=None,
):
    """
    Find movies explicitly directed by a person and apply
    structured filters.
    """

    person_id = get_person_id(director)

    if not person_id:
        return []

    directed_movie_ids = get_directed_movie_ids(
        person_id
    )

    if not directed_movie_ids:
        return []

    genre_ids = {}

    if genre:
        genre_ids = get_tmdb_genres()

    genre_id = (
        genre_ids.get(genre.lower())
        if genre
        else None
    )

    results = []

    for movie_id in directed_movie_ids:
        try:
            movie = get_tmdb_movie_details(movie_id)
        except TMDBTemporaryError:
            print(f"Skipping movie {movie_id}: temporary TMDB connection error.")
            continue

        if not movie:
            continue

        time.sleep(0.3)

        # -------------------------------------------------
        # YEAR
        # -------------------------------------------------

        release_date = movie.get(
            "release_date",
            ""
        )

        if not release_date:
            continue

        year = int(
            release_date[:4]
        )

        if (
            min_year is not None
            and year < min_year
        ):
            continue

        if (
            max_year is not None
            and year > max_year
        ):
            continue

        # -------------------------------------------------
        # RATING
        # -------------------------------------------------

        rating = movie.get(
            "vote_average"
        )

        if (
            min_rating is not None
            and (
                rating is None
                or rating < min_rating
            )
        ):
            continue

        if (
            max_rating is not None
            and (
                rating is None
                or rating > max_rating
            )
        ):
            continue

        # -------------------------------------------------
        # RUNTIME
        # -------------------------------------------------

        runtime = movie.get(
            "runtime"
        )

        if (
            min_runtime is not None
            and (
                runtime is None
                or runtime < min_runtime
            )
        ):
            continue

        if (
            max_runtime is not None
            and (
                runtime is None
                or runtime > max_runtime
            )
        ):
            continue

        # -------------------------------------------------
        # GENRE
        # -------------------------------------------------

        if genre_id is not None:

            movie_genres = movie.get(
                "genres",
                []
            )

            movie_genre_ids = {
                item.get("id")
                for item in movie_genres
            }

            if genre_id not in movie_genre_ids:
                continue

        results.append(movie)

    # Most popular first
    results.sort(
        key=lambda movie: movie.get(
            "popularity",
            0
        ),
        reverse=True,
    )

    return results



# =========================================================
# DISCOVER MOVIES
# =========================================================

def discover_tmdb_movies(
    min_year=None,
    max_year=None,
    min_rating=None,
    max_rating=None,
    min_runtime=None,
    max_runtime=None,
    genre=None,
    actor=None,
    director=None,
    page=1,
):
    """
    Retrieve live movie candidates from TMDB using
    structured filters.
    """

    params = {
        "language": "en-US",
        "include_adult": False,
        "include_video": False,
        "page": page,
        "sort_by": "popularity.desc",
    }

    # -----------------------------------------------------
    # YEAR
    # -----------------------------------------------------

    if min_year is not None:
        params["primary_release_date.gte"] = (
            f"{int(min_year)}-01-01"
        )

    if max_year is not None:
        params["primary_release_date.lte"] = (
            f"{int(max_year)}-12-31"
        )

    # -----------------------------------------------------
    # RATING
    # -----------------------------------------------------

    if min_rating is not None:
        params["vote_average.gte"] = float(min_rating)

    if max_rating is not None:
        params["vote_average.lte"] = float(max_rating)

    # -----------------------------------------------------
    # RUNTIME
    # -----------------------------------------------------

    if min_runtime is not None:
        params["with_runtime.gte"] = int(min_runtime)

    if max_runtime is not None:
        params["with_runtime.lte"] = int(max_runtime)

    # -----------------------------------------------------
    # GENRE
    # -----------------------------------------------------

    if genre:
        genres = get_tmdb_genres()

        genre_id = genres.get(
            genre.lower()
        )

        if genre_id:
            params["with_genres"] = genre_id

    # -----------------------------------------------------
    # ACTOR
    # -----------------------------------------------------

    if actor:
        person_id = get_person_id(actor)

        if person_id:
            params["with_cast"] = person_id

    # -----------------------------------------------------
    # DIRECTOR
    # -----------------------------------------------------

    if director:

        return discover_tmdb_director_movies(
            director=director,
            min_year=min_year,
            max_year=max_year,
            min_rating=min_rating,
            max_rating=max_rating,
            min_runtime=min_runtime,
            max_runtime=max_runtime,
            genre=genre,
        )

    # -----------------------------------------------------
    # REQUEST
    # -----------------------------------------------------

    data = tmdb_request(
        "discover/movie",
        params=params,
    )

    if not data:
        return []

    results = data.get(
        "results",
        []
    )

    # -----------------------------------------------------
    # DEFENSIVE FILTERING
    # -----------------------------------------------------

    filtered_results = []

    for movie in results:

        rating = movie.get("vote_average")

        if min_rating is not None:
            if rating is None or rating < min_rating:
                continue

        if max_rating is not None:
            if rating is None or rating > max_rating:
                continue

        release_date = movie.get(
            "release_date",
            ""
        )

        if release_date:

            year = int(
                release_date[:4]
            )

            if min_year is not None and year < min_year:
                continue

            if max_year is not None and year > max_year:
                continue

        filtered_results.append(movie)

    return filtered_results