import streamlit as st
from src.recommender import load_model, hybrid_recommend
from src.tmdb import (
    TMDBTemporaryError,
    get_movie_details,
    get_poster_url,
)




# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Movie Details | MovieVerse",
    page_icon="🎬",
    layout="wide",
)


# =========================================================
# LOAD ML MODEL
# =========================================================

@st.cache_resource
def get_recommender():
    return load_model()


movies, similarity = get_recommender()


# =========================================================
# GET MOVIE ID FROM URL
# =========================================================

movie_id = st.query_params.get("movie_id")


if not movie_id:
    st.warning("No movie selected.")

    if st.button("🏠 ← Back to MovieVerse"):
        st.switch_page("app.py")

    st.stop()


try:
    movie_id = int(movie_id)

except ValueError:
    st.error("Invalid movie ID.")

    if st.button("🏠 ← Back to MovieVerse"):
        st.switch_page("app.py")

    st.stop()







# =========================================================
# BACK BUTTON
# =========================================================

if st.button("🏠 ← Back to MovieVerse"):
    st.switch_page("app.py")


# =========================================================
# LOAD MOVIE DETAILS
# =========================================================

try:

    details = get_movie_details(movie_id)

except TMDBTemporaryError:

    st.error(
        "TMDB is temporarily unavailable. "
        "Please try again in a moment."
    )
    st.stop()


if not details:

    st.error("Movie details could not be found.")
    st.stop()


# =========================================================
# MOVIE DETAILS
# =========================================================

st.divider()

st.markdown("## 🎬 Movie Details")


poster_url = get_poster_url(
    details.get("poster_path")
)


left, right = st.columns(
    [1, 2],
    gap="large",
)


# =========================================================
# POSTER
# =========================================================

with left:

    if poster_url:

        st.image(
            poster_url,
            width="stretch",
        )

    else:

        st.info("Poster unavailable")


# =========================================================
# INFORMATION
# =========================================================

with right:

    title = details.get(
        "title",
        "Unknown Movie",
    )

    st.title(title)

    metadata = []

    rating = details.get("vote_average")

    if rating is not None:

        metadata.append(
            f"⭐ {rating:.1f}/10"
        )


    release_date = details.get(
        "release_date"
    )

    if release_date:

        metadata.append(
            f"📅 {release_date[:4]}"
        )


    runtime = details.get(
        "runtime"
    )

    if runtime:

        metadata.append(
            f"⏱️ {runtime} min"
        )


    if metadata:

        st.markdown(
            " • ".join(metadata)
        )


    # -----------------------------------------------------
    # GENRES
    # -----------------------------------------------------

    genres = details.get(
        "genres",
        []
    )

    if genres:

        genre_names = [
            genre.get("name")
            for genre in genres
            if genre.get("name")
        ]

        if genre_names:

            st.caption(
                " • ".join(genre_names)
            )


    # -----------------------------------------------------
    # OVERVIEW
    # -----------------------------------------------------

    st.markdown("### Overview")

    overview = details.get(
        "overview"
    )

    if overview:

        st.write(overview)

    else:

        st.caption(
            "No overview available."
        )


# =========================================================
# RECOMMENDATIONS
# =========================================================

st.divider()

st.markdown(
    "## ✨ Movies You May Like"
)

st.write(
    "MovieVerse automatically chooses the best "
    "recommendation engine for this movie."
)


# =========================================================
# RUN HYBRID ENGINE AUTOMATICALLY
# =========================================================

with st.spinner(
    "Finding movies you may like..."
):

    try:

        result = hybrid_recommend(
            movie_title=details.get(
                "title",
                "Unknown Movie",
            ),
            tmdb_movie_id=details.get(
                "id",
                movie_id,
            ),
            movies=movies,
            similarity=similarity,
            number_of_recommendations=5,
        )

    except TMDBTemporaryError:

        st.error(
            "Movie recommendations are "
            "temporarily unavailable."
        )

        st.stop()


# =========================================================
# SHOW ENGINE
# =========================================================

source = result.get(
    "source"
)

recommendations = result.get(
    "recommendations",
    []
)


if source == "ML":

    st.caption(
        "🧠 Recommendations powered by "
        "MovieVerse's ML model"
    )

else:

    st.caption(
        "🌐 Recommendations powered by "
        "live TMDB data"
    )


# =========================================================
# RECOMMENDATION CARDS
# =========================================================

if not recommendations:

    st.info(
        "No recommendations found for this movie."
    )

else:

    columns = st.columns(5)

    for column, movie in zip(
        columns,
        recommendations[:5],
    ):

        with column:

            # ---------------------------------------------
            # NORMALIZE DATA
            # ---------------------------------------------

            if source == "ML":

                title = movie.get(
                    "title",
                    "Unknown Movie",
                )

                tmdb_id = movie.get(
                    "movie_id"
                )

                
                

                try:

                    movie_details = get_movie_details(
                        tmdb_id
                    )

                except TMDBTemporaryError:

                    movie_details = None

                if movie_details:

                    poster_path = movie_details.get(
                        "poster_path"
                    )

                    rating = movie_details.get(
                        "vote_average"
                    )

                    release_date = movie_details.get(
                        "release_date"
                    )

                else:

                    poster_path = None
                    rating = None
                    release_date = None


            else:

                title = movie.get(
                    "title",
                    "Unknown Movie",
                )

                tmdb_id = movie.get(
                    "id"
                )

                poster_path = movie.get(
                    "poster_path"
                )

                rating = movie.get(
                    "vote_average"
                )

                release_date = movie.get(
                    "release_date"
                )

                


            # ---------------------------------------------
            # POSTER
            # ---------------------------------------------

            poster_url = get_poster_url(
                poster_path
            )


            if poster_url:

                st.image(
                    poster_url,
                    width="stretch",
                )

            else:

                st.info("Poster unavailable")


            # ---------------------------------------------
            # TITLE
            # ---------------------------------------------

            st.markdown(
                f"**{title}**"
            )


            # ---------------------------------------------
            # RATING
            # ---------------------------------------------

            if rating is not None:

                st.caption(
                    f"⭐ {rating:.1f}/10"
                )


            # ---------------------------------------------
            # YEAR
            # ---------------------------------------------

            if release_date:

                st.caption(
                    f"📅 {release_date[:4]}"
                )

            if tmdb_id:
                if st.button(
                    "🎬 Details",
                    key=f"recommendation_details_{tmdb_id}",
                    width="stretch",
                ):
                    st.switch_page(
                        "pages/movie.py",
                        query_params={
                            "movie_id": str(tmdb_id)
                        },
                    )


            


            