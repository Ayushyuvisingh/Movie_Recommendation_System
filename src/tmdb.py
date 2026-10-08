import time

import requests
import streamlit as st


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


class TMDBTemporaryError(Exception):
    """Temporary TMDB or network problem."""


def get_api_key():
    return st.secrets["TMDB_API_KEY"]


# =========================================================
# CORE REQUEST FUNCTION
# =========================================================

def tmdb_request(endpoint, params=None, retries=3):
    """
    Reliable TMDB request with retry handling.
    """

    url = f"{TMDB_BASE_URL}/{endpoint}"

    request_params = dict(params or {})
    request_params["api_key"] = get_api_key()

    for attempt in range(retries):

        try:

            response = requests.get(
                url,
                params=request_params,
                timeout=8,
            )

            # -----------------------------------------
            # SUCCESS
            # -----------------------------------------

            if response.status_code == 200:
                return response.json()

            # -----------------------------------------
            # NOT FOUND
            # -----------------------------------------

            if response.status_code == 404:
                return None

            # -----------------------------------------
            # RATE LIMIT
            # -----------------------------------------

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:
                    wait_time = min(
                        float(retry_after),
                        5
                    )
                else:
                    wait_time = 1.5

                if attempt < retries - 1:
                    time.sleep(wait_time)
                    continue

                raise TMDBTemporaryError(
                    "TMDB rate limit reached."
                )

            # -----------------------------------------
            # SERVER ERROR
            # -----------------------------------------

            if response.status_code in (
                500,
                502,
                503,
                504,
            ):

                if attempt < retries - 1:

                    time.sleep(
                        0.5 * (2 ** attempt)
                    )

                    continue

                raise TMDBTemporaryError(
                    f"TMDB server error: "
                    f"{response.status_code}"
                )

            # -----------------------------------------
            # OTHER ERROR
            # -----------------------------------------

            response.raise_for_status()

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as error:

            if attempt < retries - 1:

                time.sleep(
                    0.5 * (2 ** attempt)
                )

                continue

            raise TMDBTemporaryError(
                "TMDB connection failed."
            ) from error

        except requests.exceptions.RequestException as error:

            raise TMDBTemporaryError(
                f"TMDB request failed: {error}"
            ) from error

    raise TMDBTemporaryError(
        "TMDB request failed."
    )


# =========================================================
# MOVIE DETAILS
# =========================================================

@st.cache_data(
    ttl="1d",
    show_spinner=False,
)
def get_movie_details(movie_id):

    return tmdb_request(
        f"movie/{movie_id}",
        params={
            "language": "en-US",
        },
    )

def get_movie_catalog_data(movie_id):
    """
    Fetch movie details needed for the MovieVerse RAG catalog.

    Includes:
    - Basic movie details
    - Credits
    - Keywords
    """

    return tmdb_request(
        f"movie/{movie_id}",
        params={
            "append_to_response": "credits,keywords"
        }
    )


# =========================================================
# SEARCH
# =========================================================

@st.cache_data(
    ttl="1d",
    show_spinner=False,
)
def search_movie(title):

    data = tmdb_request(
        "search/movie",
        params={
            "query": title,
            "language": "en-US",
            "include_adult": False,
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# SIMILAR MOVIES
# =========================================================

@st.cache_data(
    ttl="6h",
    show_spinner=False,
)
def get_similar_movies(movie_id):

    data = tmdb_request(
        f"movie/{movie_id}/similar",
        params={
            "language": "en-US",
            "page": 1,
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# TMDB RECOMMENDATIONS
# =========================================================

@st.cache_data(
    ttl="6h",
    show_spinner=False,
)
def get_movie_recommendations(movie_id):

    data = tmdb_request(
        f"movie/{movie_id}/recommendations",
        params={
            "language": "en-US",
            "page": 1,
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# TRENDING
# =========================================================

@st.cache_data(
    ttl="1h",
    show_spinner=False,
)
def get_trending_movies(
    time_window="week"
):

    data = tmdb_request(
        f"trending/movie/{time_window}",
        params={
            "language": "en-US",
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# POPULAR
# =========================================================

@st.cache_data(
    ttl="6h",
    show_spinner=False,
)
def get_popular_movies():

    data = tmdb_request(
        "movie/popular",
        params={
            "language": "en-US",
            "page": 1,
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# NOW PLAYING
# =========================================================

@st.cache_data(
    ttl="6h",
    show_spinner=False,
)
def get_now_playing():

    data = tmdb_request(
        "movie/now_playing",
        params={
            "language": "en-US",
            "page": 1,
            "region": "IN",
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# UPCOMING
# =========================================================

@st.cache_data(
    ttl="6h",
    show_spinner=False,
)
def get_upcoming_movies():

    data = tmdb_request(
        "movie/upcoming",
        params={
            "language": "en-US",
            "page": 1,
            "region": "IN",
        },
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# DISCOVER
# =========================================================

@st.cache_data(
    ttl="6h",
    show_spinner=False,
)
def discover_movies(
    page=1,
    sort_by="popularity.desc",
    genre_id=None,
    min_rating=None,
    release_year=None,
):

    params = {
        "language": "en-US",
        "page": page,
        "sort_by": sort_by,
        "include_adult": False,
        "include_video": False,
    }

    if genre_id is not None:
        params["with_genres"] = genre_id

    if min_rating is not None:
        params["vote_average.gte"] = min_rating

    if release_year is not None:
        params["primary_release_year"] = release_year

    data = tmdb_request(
        "discover/movie",
        params=params,
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# =========================================================
# MOVIE DATA FALLBACK
# =========================================================

@st.cache_data(
    ttl="1d",
    show_spinner=False,
)
def get_movie_data(
    movie_id,
    title,
):

    # First try original dataset ID
    try:

        details = get_movie_details(
            movie_id
        )

        if details is not None:
            return details

    except TMDBTemporaryError:
        pass

    # Fallback to title search
    try:

        results = search_movie(
            title
        )

        if results:

            # Exact title match first
            title_lower = title.strip().lower()

            for movie in results:

                tmdb_title = movie.get(
                    "title",
                    ""
                ).strip().lower()

                if tmdb_title == title_lower:
                    return movie

            return results[0]

    except TMDBTemporaryError:
        pass

    return None


# =========================================================
# IMAGE URLS
# =========================================================

def get_poster_url(
    poster_path
):

    if not poster_path:
        return None

    return (
        f"{TMDB_IMAGE_BASE_URL}"
        f"/w500{poster_path}"
    )


def get_backdrop_url(
    backdrop_path
):

    if not backdrop_path:
        return None

    return (
        f"{TMDB_IMAGE_BASE_URL}"
        f"/w1280{backdrop_path}"
    )