import pickle
from pathlib import Path

import pandas as pd
from src.tmdb import (
    get_similar_movies,
    get_movie_recommendations,
)

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_model():
    """
    Load the movie dataset and similarity matrix.
    """

    movie_path = DATA_DIR / "movie_dict.pkl"
    similarity_path = DATA_DIR / "similarity.pkl"

    with open(movie_path, "rb") as file:
        movies_dict = pickle.load(file)

    with open(similarity_path, "rb") as file:
        similarity = pickle.load(file)

    movies = pd.DataFrame(movies_dict)

    return movies, similarity


def recommend(
    movie_title,
    movies,
    similarity,
    number_of_recommendations=5
):
    """
    Return similar movies along with their TMDB IDs
    and similarity scores.
    """

    matches = movies[
        movies["title"].str.lower() == movie_title.lower()
    ]

    if matches.empty:
        return []

    movie_index = matches.index[0]

    distances = sorted(
        list(enumerate(similarity[movie_index])),
        reverse=True,
        key=lambda x: x[1]
    )

    recommendations = []

    for index, score in distances[
        1:number_of_recommendations + 1
    ]:

        recommendations.append({
            "title": movies.iloc[index]["title"],
            "movie_id": int(movies.iloc[index]["movie_id"]),
            "score": float(score)
        })

    return recommendations


def hybrid_recommend(
    movie_title,
    tmdb_movie_id,
    movies,
    similarity,
    number_of_recommendations=5,
):
    """
    Recommend movies using the local ML model when the movie
    exists in the training dataset. Otherwise use TMDB.
    """

    # =====================================================
    # CHECK LOCAL ML DATASET
    # =====================================================

    matches = movies[
        movies["title"].str.lower()
        == movie_title.strip().lower()
    ]

    # =====================================================
    # CASE 1: MOVIE EXISTS IN ML DATASET
    # =====================================================

    if not matches.empty:

        recommendations = recommend(
            movie_title,
            movies,
            similarity,
            number_of_recommendations,
        )

        return {
            "source": "ML",
            "recommendations": recommendations,
        }

    # =====================================================
    # CASE 2: MOVIE NOT IN ML DATASET
    # =====================================================

    if not tmdb_movie_id:

        return {
            "source": "TMDB",
            "recommendations": [],
        }

    # -----------------------------------------------------
    # First: TMDB Similar Movies
    # -----------------------------------------------------

    similar_movies = get_similar_movies(
        tmdb_movie_id
    )

    # -----------------------------------------------------
    # Then: TMDB Recommendations
    # -----------------------------------------------------

    tmdb_recommendations = get_movie_recommendations(
        tmdb_movie_id
    )

    # =====================================================
    # COMBINE RESULTS
    # =====================================================

    combined_movies = []

    seen_ids = set()

    for movie in (
        similar_movies
        + tmdb_recommendations
    ):

        movie_id = movie.get("id")

        if not movie_id:
            continue

        if movie_id in seen_ids:
            continue

        seen_ids.add(movie_id)

        combined_movies.append(movie)

        if len(combined_movies) >= number_of_recommendations:
            break

    return {
        "source": "TMDB",
        "recommendations": combined_movies,
    }