import streamlit as st
from src.hybrid_rag import HybridRAG

from streamlit_searchbox import st_searchbox
from src.recommender import load_model
from src.tmdb import (
    TMDBTemporaryError,
    get_poster_url,
    search_movie,
    get_trending_movies,
    get_popular_movies,
    get_now_playing,
    get_upcoming_movies,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MovieVerse",
    page_icon="🎬",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background: #ffffff;
        color: #1f2937;
    }

    /* Sidebar */   
    [data-testid="stSidebar"] {
        background: #f8fafc;
    }

    /* Streamlit top header */
    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.95);
    }

    /* Main text */
    h1, h2, h3, h4, h5, h6,
    p, label {
        color: #1f2937;
    }

    /* Main title */
    .movieverse-title {
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 0;
    }

    .movieverse-subtitle {
        font-size: 1.15rem;
        color: #64748b;
        margin-top: -8px;
        margin-bottom: 30px;
    }

    /* Section headings */
    .section-title {
        font-size: 1.7rem;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* Movie title */
    .movie-title {
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 8px;
        line-height: 1.25;
    }

    /* Movie metadata */
    .movie-meta {
        color: #64748b;
        font-size: 0.82rem;
        margin-top: 4px;
    }

    /* Divider */
    hr {
        margin-top: 30px;
        margin-bottom: 30px;
    }



    /* AI result cards */
    .ai-card {
        padding: 0;
        background: transparent;
    }

    .ai-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1f2937;
        margin-top: 8px;
        line-height: 1.3;
        min-height: 2.5em;
    }

    .ai-card-meta {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 5px;
    }

    .ai-results-heading {
        font-size: 1.7rem;
        font-weight: 700;
        color: #1f2937;
        margin-top: 30px;
        margin-bottom: 20px;
    }

    .ai-results-heading span {
        color: #475569;
        font-weight: 500;
    }
    

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOAD ML MODEL
# =========================================================

@st.cache_resource
def get_recommender():
    return load_model()


movies, similarity = get_recommender()



# =========================================================
# LOAD HYBRID RAG
# =========================================================

@st.cache_resource
def get_hybrid_rag():
    return HybridRAG()


hybrid_rag = get_hybrid_rag()







# =========================================================
# MOVIE AUTOCOMPLETE SEARCH
# =========================================================

@st.cache_data(ttl=300, show_spinner=False)
def search_tmdb_cached(search_term):
    if not search_term or len(search_term.strip()) < 2:
        return []

    try:
        return search_movie(search_term.strip())[:8]
    except TMDBTemporaryError:
        return []


def movie_search(search_term):
    """
    Search MovieVerse using both:
    1. Local ML dataset
    2. Live TMDB data
    """

    if not search_term or len(search_term.strip()) < 2:
        return []

    search_term = search_term.strip().lower()

    results = []
    seen_ids = set()

    # -----------------------------------------------------
    # LOCAL ML DATASET
    # -----------------------------------------------------

    local_matches = movies[
        movies["title"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_term,
            na=False,
            regex=False,
        )
    ].head(5)

    for _, movie in local_matches.iterrows():

        movie_id = movie.get("movie_id")
        title = movie.get("title")

        if not title or movie_id is None:
            continue

        movie_id = int(movie_id)

        if movie_id in seen_ids:
            continue

        seen_ids.add(movie_id)

        results.append(
            (
                f"🎬 {title}",
                {
                    "id": movie_id,
                    "title": str(title),
                    "source": "ML",
                },
            )
        )

    # -----------------------------------------------------
    # LIVE TMDB SEARCH
    # -----------------------------------------------------

    tmdb_results = search_tmdb_cached(search_term)

    for movie in tmdb_results:

        movie_id = movie.get("id")
        title = movie.get("title")

        if not movie_id or not title:
            continue

        movie_id = int(movie_id)

        if movie_id in seen_ids:
            continue

        seen_ids.add(movie_id)

        release_date = movie.get(
            "release_date",
            "",
        )

        year = (
            release_date[:4]
            if release_date
            else ""
        )

        label = (
            f"🎬 {title} • {year}"
            if year
            else f"🎬 {title}"
        )

        results.append(
            (
                label,
                {
                    "id": movie_id,
                    "title": str(title),
                    "source": "TMDB",
                },
            )
        )

    return results[:10]


# =========================================================
# MOVIE CARD FUNCTION
# =========================================================

def display_movie_row(movie_list, section_name, limit=5):

    if not movie_list:
        st.info("No movies available right now.")
        return

    columns = st.columns(limit)

    for column, movie in zip(columns, movie_list[:limit]):

        movie_id = movie.get("id") or movie.get("movie_id")

        with column:

            poster_path = movie.get("poster_path")

            if poster_path:

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

            else:
                st.info("Poster unavailable")

            title = movie.get(
                "title",
                "Unknown Movie",
            )

            st.markdown(
                f'<div class="movie-title">{title}</div>',
                unsafe_allow_html=True,
            )

            rating = movie.get("vote_average")

            release_date = movie.get(
                "release_date"
            )

            metadata = []

            if rating is not None:
                metadata.append(
                    f"⭐ {rating:.1f}"
                )

            if release_date:
                metadata.append(
                    f"📅 {release_date[:4]}"
                )

            if metadata:

                st.markdown(
                    '<div class="movie-meta">'
                    + " • ".join(metadata)
                    + "</div>",
                    unsafe_allow_html=True,
                )

            if movie_id:
                if st.button(
                    "🎬 Details",
                    key=f"{section_name}_details_{movie_id}",
                    width="stretch",
                ):
                    st.switch_page(
                        "pages/movie.py",
                        query_params={
                            "movie_id": str(movie_id)
                        },
                    )




# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="movieverse-title">🎬 MovieVerse</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="movieverse-subtitle">'
    'Discover movies you will love — from timeless favorites '
    'to what is trending right now.'
    '</div>',
    unsafe_allow_html=True,
)



# =========================================================
# AI MOVIE SEARCH
# =========================================================

st.markdown(
    '<div class="section-title">🧠 Ask MovieVerse</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Ask naturally using actors, directors, years, ratings, genres, "
    "or phrases like 'latest movie'."
)

ai_query = st.text_input(
    "Ask MovieVerse",
    placeholder="e.g. Yash latest movie",
    label_visibility="collapsed",
)

if st.button(
    "🔍 Search with AI",
    type="primary",
    key="ai_search_button",
):

    if not ai_query.strip():

        st.warning("Please enter a movie query.")

    else:

        # -----------------------------------------------------
        # SEARCH PROGRESS
        # -----------------------------------------------------

        status_box = st.status(
            "🔎 Searching MovieVerse...",
            expanded=True,
        )


        def update_progress(message):

            status_box.write(message)


        try:

            ai_results = hybrid_rag.search(
                ai_query.strip(),
                top_k=10,
                progress_callback=update_progress,
            )

            status_box.update(
                label="✅ Search complete",
                state="complete",
                expanded=False,
            )

            if ai_results:

                    st.session_state["ai_results"] = ai_results
                    st.session_state["ai_query"] = ai_query.strip()

            else:

                    st.session_state["ai_results"] = []
                    st.info(
                        "No matching movies found. "
                        "Try a different query."
                    )

        except Exception as e:
            status_box.update(
                label="❌ Search failed",
                state="error",
                expanded=False,
            )

            st.error(
                f"Something went wrong while searching: {e}"
            )


# =========================================================
# AI RESULTS
# =========================================================

if st.session_state.get("ai_results"):

    st.markdown(
        f'<div class="ai-results-heading">'
        f'🎬 Results for '
        f'<span>{st.session_state.get("ai_query", "")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    ai_results = st.session_state["ai_results"]

    # Display 5 movies per row
    for row_start in range(0, len(ai_results), 5):

        row_results = ai_results[
            row_start:row_start + 5
        ]

        columns = st.columns(5)

        for column, result in zip(
            columns,
            row_results,
        ):

            movie = result.get("movie", {})

            movie_id = result.get(
                "tmdb_id"
            )

            title = result.get(
                "title",
                "Unknown Movie",
            )

            release_year = result.get(
                "release_year",
                "N/A",
            )

            rating = result.get(
                "rating"
            )

            

            poster_path = movie.get(
                "poster_path"
            )

            with column:

                st.markdown(
                    '<div class="ai-card">',
                    unsafe_allow_html=True,
                )

                if poster_path:

                    poster_url = get_poster_url(
                        poster_path
                    )

                    if poster_url:

                        st.image(
                            poster_url,
                            width="stretch",
                        )

                    else:

                        st.info(
                            "Poster unavailable"
                        )

                else:

                    st.info(
                        "Poster unavailable"
                    )

                st.markdown(
                    f'<div class="ai-card-title">'
                    f'{title}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                metadata = (
                    f"📅 {release_year}"
                )

                if rating is not None:
                    try:
                        rating_value = float(rating)
                        metadata += f" • ⭐ {rating_value:.1f}"
                    except (TypeError, ValueError):
                        pass

                st.markdown(
                    f'<div class="ai-card-meta">'
                    f'{metadata}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                

                if movie_id:

                    if st.button(
                        "🎬 Details",
                        key=f"ai_details_{movie_id}",
                        width="stretch",
                    ):

                        st.switch_page(
                            "pages/movie.py",
                            query_params={
                                "movie_id": str(movie_id)
                            },
                        )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True,
                )




# =========================================================
# MOVIE SEARCH
# =========================================================

st.markdown(
    '<div class="section-title">🔎 Find Any Movie</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Search thousands of movies — including the latest releases."
)


# Create a fresh searchbox identity after every selection.
if "searchbox_version" not in st.session_state:
    st.session_state["searchbox_version"] = 0


def handle_movie_selection(selected_movie):
    """Store selected movie and reset the searchbox for the next search."""

    if selected_movie:
        st.session_state["selected_movie_id"] = selected_movie.get("id")

        # Force a fresh searchbox when we return to Home.
        st.session_state["searchbox_version"] += 1


st_searchbox(
    search_function=movie_search,
    placeholder="Search for a movie...",
    label="",
    key=f"movie_searchbox_{st.session_state['searchbox_version']}",
    debounce=300,
    clear_on_submit=True,
    edit_after_submit="disabled",
    submit_function=handle_movie_selection,
)





# =========================================================
# OPEN SELECTED MOVIE
# =========================================================

selected_movie_id = st.session_state.pop(
    "selected_movie_id",
    None,
)

if selected_movie_id:
    st.switch_page(
        "pages/movie.py",
        query_params={
            "movie_id": str(selected_movie_id)
        },
    )


# =========================================================
# TRENDING
# =========================================================

st.markdown(
    '<div class="section-title">🔥 Trending This Week</div>',
    unsafe_allow_html=True,
)

try:

    trending_movies = get_trending_movies(
        "week"
    )

    display_movie_row(
        trending_movies,
        section_name="trending",
        limit=5,
    )

except TMDBTemporaryError:

    st.warning(
        "Trending movies are temporarily unavailable."
    )


# =========================================================
# POPULAR
# =========================================================

st.markdown(
    '<div class="section-title">⭐ Popular Movies</div>',
    unsafe_allow_html=True,
)

try:

    popular_movies = get_popular_movies()

    display_movie_row(
        popular_movies,
        section_name="popular",
        limit=5,
    )

except TMDBTemporaryError:

    st.warning(
        "Popular movies are temporarily unavailable."
    )


# =========================================================
# NOW PLAYING
# =========================================================

st.markdown(
    '<div class="section-title">🎥 Now Playing in India</div>',
    unsafe_allow_html=True,
)

try:

    now_playing_movies = get_now_playing()

    display_movie_row(
        now_playing_movies,
        section_name="now_playing",
        limit=5,
    )

except TMDBTemporaryError:

    st.warning(
        "Now Playing movies are temporarily unavailable."
    )


# =========================================================
# UPCOMING
# =========================================================

st.markdown(
    '<div class="section-title">🔜 Coming Soon</div>',
    unsafe_allow_html=True,
)

try:

    upcoming_movies = get_upcoming_movies()

    display_movie_row(
        upcoming_movies,
        section_name="upcoming",
        limit=5,
    )

except TMDBTemporaryError:

    st.warning(
        "Upcoming movies are temporarily unavailable."
    )



# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "MovieVerse • Machine Learning + TMDB"
)