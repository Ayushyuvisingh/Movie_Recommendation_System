import numpy as np
import time

from src.rag_search import RAGSearchEngine
from src.tmdb import TMDBTemporaryError

from src.tmdb_documents import (
    get_full_tmdb_movie,
    tmdb_movie_to_document,
)

from src.tmdb_embeddings import (
    load_embedding_model,
    embed_tmdb_document,
)
from src.tmdb_rag import (
    discover_tmdb_movies,
    discover_tmdb_director_movies,
    discover_tmdb_person_movies,
    resolve_person_role,
)


class HybridRAG:
    """
    Hybrid MovieVerse RAG engine.

    Combines:
    - Local MovieVerse RAG
    - Live TMDB candidates
    """

    def __init__(self):

        print("Loading local RAG...")

        self.local_rag = RAGSearchEngine()

        print("\nLoading embedding model...")

        self.embedding_model = load_embedding_model()

        print("\nHybrid RAG ready.")



    def _get_tmdb_movie_with_retry(
        self,
        movie_id,
        movie_title="",
        attempts=5,
        delay=2.0,
    ):
        """
        Fetch full TMDB movie details.

        For important/latest queries, retry the same movie
        several times before giving up.
        """

        for attempt in range(1, attempts + 1):

            try:
                movie = get_full_tmdb_movie(movie_id)

                if movie:
                    return movie

            except TMDBTemporaryError as e:

                print(
                    f"TMDB temporary failure for "
                    f"{movie_title or movie_id}. "
                    f"Attempt {attempt}/{attempts}."
                )

                if attempt < attempts:
                    print(
                        f"Waiting {delay} seconds before retry..."
                    )
                    time.sleep(delay)

                continue

            except Exception as e:

                print(
                    f"TMDB error for "
                    f"{movie_title or movie_id}: {e}"
                )

                if attempt < attempts:
                    print(
                        f"Waiting {delay} seconds before retry..."
                    )
                    time.sleep(delay)

                continue

        print(
            f"Could not fetch full details for "
            f"{movie_title or movie_id} "
            f"after {attempts} attempts."
        )

        return None


    def search(self, query, top_k=10, progress_callback=None):

        def progress(message):
            if progress_callback:
                progress_callback(message)

        # -----------------------------------------------------
        # 1. PARSE QUERY
        # -----------------------------------------------------

        progress("🧠 Understanding your query...")

        parsed = self.local_rag.search(
            query,
            top_k=top_k,
        )

        progress("🔎 Searching MovieVerse's movie knowledge...")

        # -----------------------------------------------------
        # 2. PARSE QUERY AGAIN FOR TMDB
        # -----------------------------------------------------

        from src.query_parser import parse_query

        filters = parse_query(query)

        progress("🎯 Applying filters and understanding your intent...")

        print("\nTMDB filters:")
        print(filters)

        person = filters.get("person")

        # -----------------------------------------------------
        # 3. LOCAL RESULTS
        # -----------------------------------------------------

        if person:
            # Person-specific queries should use TMDB person results.
            # Generic local RAG results are not guaranteed to belong
            # to this actor/director.
            local_results = []
        else:
            local_results = parsed

        # -----------------------------------------------------
        # 4. TMDB LIVE SEARCH
        # -----------------------------------------------------

        

        if person:
            progress(
                f"🎭 Identifying {person}..."
            )
            print(f"\nResolving person: {person}")

            try:
                person_info = resolve_person_role(person)

            except TMDBTemporaryError as e:
                print(
                    f"\nTMDB is temporarily unavailable "
                    f"while resolving '{person}': {e}"
                )
                person_info = None
                tmdb_results = []

            if person_info is None:
                print(
                    "\nSkipping TMDB person search "
                    "because TMDB is temporarily unavailable."
                )

                tmdb_results = []

            else:
                print("Resolved person:")
                print(person_info)

                progress(
                    f"🎭 Identified {person_info['name']} "
                    f"as an {person_info['role']}."
                )

                if person_info["role"] in ("actor", "director"):
                    print(
                        f"Using TMDB person discovery "
                        f"for {person_info['role']}."
                    )

                    try:
                        tmdb_results = discover_tmdb_person_movies(
                            person_id=person_info["person_id"],
                            role=person_info["role"],
                            min_year=filters["min_year"],
                            max_year=filters["max_year"],
                            min_rating=filters["min_rating"],
                            max_rating=filters["max_rating"],
                            min_runtime=filters["min_runtime"],
                            max_runtime=filters["max_runtime"],
                            genre=filters["genre"],
                            sort_by=filters.get(
                                "sort_by",
                                "popularity.desc"
                            ),
                        )

                    except TMDBTemporaryError as e:
                        print(
                            f"\nTMDB is temporarily unavailable "
                            f"while finding movies for '{person}': {e}"
                        )

                        tmdb_results = []

                else:
                    print(
                        "Could not determine person's movie role."
                    )

                    tmdb_results = []



            




        else:
            # Explicit actor/director queries
            try:
                tmdb_results = discover_tmdb_movies(
                    min_year=filters["min_year"],
                    max_year=filters["max_year"],
                    min_rating=filters["min_rating"],
                    max_rating=filters["max_rating"],
                    min_runtime=filters["min_runtime"],
                    max_runtime=filters["max_runtime"],
                    genre=filters["genre"],
                    actor=filters["actor"],
                    director=filters["director"],
                )

            except TMDBTemporaryError:
                print(
                    "\nTMDB is temporarily unavailable."
                    "\nContinuing with local RAG results."
                )
                tmdb_results = []

        progress(
            "🌐 Checking live TMDB data..."
        )
        
        print(
            f"\nTMDB candidates found: "
            f"{len(tmdb_results)}"
        )

        progress(
            f"🎬 Found {len(tmdb_results)} live movie candidates."
        )


        # -----------------------------------------------------
        # 4B. HANDLE TEMPORAL INTENT
        # -----------------------------------------------------

        requested_k = top_k

        if person and filters.get("sort_by") == "release_date_desc":
            from datetime import date
            import re

            today = date.today().isoformat()

            # Keep only movies that have already been released.
            tmdb_results = [
                movie
                for movie in tmdb_results
                if movie.get("release_date")
                and movie.get("release_date") <= today
            ]

            # Latest released movie first.
            tmdb_results.sort(
                key=lambda movie: movie.get("release_date", ""),
                reverse=True
            )

            original_query = filters.get(
                "original_query",
                query,
            )

            if re.search(
                r"\blatest\s+movie\b",
                original_query,
                re.IGNORECASE,
            ):
                requested_k = 1

            elif re.search(
                r"\blatest\s+movies\b",
                original_query,
                re.IGNORECASE,
            ):
                requested_k = min(top_k, 10)

           
            # If "latest" also contains structured filters
            # such as rating, year, runtime or genre,
            # inspect more candidates because the newest movie
            # may not satisfy those filters.

            has_structured_filter = any(
                filters.get(key) is not None
                for key in [
                    "min_year",
                    "max_year",
                    "min_rating",
                    "max_rating",
                    "min_runtime",
                    "max_runtime",
                ]
            ) or filters.get("genre") is not None


            if has_structured_filter:
                candidate_limit = min(
                    len(tmdb_results),
                    max(requested_k + 3, 20),
                )
            else:
                candidate_limit = min(
                    len(tmdb_results),
                    requested_k + 3,
                )

            tmdb_results = tmdb_results[:candidate_limit]

            print(
                f"\nLatest intent detected."
                f" Requested results: {requested_k}"
            )

            print("\nLatest released movies:")
            for movie in tmdb_results:
                print(
                    f"  {movie.get('release_date')} - "
                    f"{movie.get('title')}"
                )

        # -----------------------------------------------------
        # 5. LOCAL MOVIE IDS
        # -----------------------------------------------------

        local_ids = set()

        for result in local_results:

            movie_id = result.get("tmdb_id")

            if movie_id is not None:
                local_ids.add(int(movie_id))

        # -----------------------------------------------------
        # 6. CREATE QUERY EMBEDDING
        # -----------------------------------------------------

        semantic_query = filters.get(
            "semantic_query",
            "",
        )

        if not semantic_query.strip():
            semantic_query = query

        query_embedding = self.embedding_model.encode(
            [semantic_query],
            normalize_embeddings=True,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        # -----------------------------------------------------
        # 7. START WITH LOCAL RESULTS
        # -----------------------------------------------------

        combined_results = []

        for result in local_results:

            movie_id = result.get("tmdb_id")

            # Start with the original RAG result
            movie_data = dict(result)

            # -------------------------------------------------
            # Add poster/details from local movie catalog
            # -------------------------------------------------

            if movie_id is not None:

                catalog_matches = self.local_rag.catalog[
                    self.local_rag.catalog["tmdb_id"]
                    == int(movie_id)
                ]

                if not catalog_matches.empty:

                    catalog_movie = catalog_matches.iloc[0]

                    movie_data["poster_path"] = (
                        catalog_movie.get("poster_path")
                    )

                    movie_data["release_date"] = (
                        catalog_movie.get("release_date")
                    )

                    movie_data["vote_average"] = (
                        catalog_movie.get("vote_average")
                    )

            combined_results.append(
                {
                    "title": result.get("title"),
                    "tmdb_id": result.get("tmdb_id"),
                    "score": float(
                        result.get("score", 0)
                    ),
                    "release_year": result.get(
                        "release_year"
                    ),
                    "runtime": result.get(
                        "runtime"
                    ),
                    "rating": result.get(
                        "rating"
                    ),
                    "source": "local",
                    "movie": movie_data,
                }
            )

        # -----------------------------------------------------
        # 8. PROCESS LIVE TMDB MOVIES
        # -----------------------------------------------------

        person_results_added = 0

        for movie in tmdb_results:

            movie_id = movie.get("id")

            if movie_id is None:
                continue

            movie_id = int(movie_id)

            # Skip duplicate local movies.
            if movie_id in local_ids:
                continue


            progress(
                f"🎬 Processing {movie.get('title')}..."
            )

            print(
                f"Embedding live movie: "
                f"{movie.get('title')}"
            )

            is_latest_person_query = (
                person
                and filters.get("sort_by")
                == "release_date_desc"
            )

            if is_latest_person_query:
                full_movie = self._get_tmdb_movie_with_retry(
                    movie_id=movie_id,
                    movie_title=movie.get("title"),
                    attempts=5,
                    delay=2.0,
                )
            else:
                full_movie = self._get_tmdb_movie_with_retry(
                    movie_id=movie_id,
                    movie_title=movie.get("title"),
                    attempts=3,
                    delay=1.0,
                )

            if not full_movie:
                print(
                    f"Full details unavailable for "
                    f"{movie.get('title')}. "
                    f"Trying next candidate."
                )
                continue

            


            # ---------------------------------------------------------
            # APPLY STRUCTURED FILTERS TO FULL TMDB DETAILS
            # ---------------------------------------------------------

            release_date = full_movie.get("release_date", "")
            rating = full_movie.get("vote_average")
            runtime = full_movie.get("runtime")


            # Year filter
            if release_date:
                movie_year = int(release_date[:4])

                if (
                    filters.get("min_year") is not None
                    and movie_year < filters["min_year"]
                ):
                    continue

                if (
                    filters.get("max_year") is not None
                    and movie_year > filters["max_year"]
                ):
                    continue


            # Rating filter
            if (
                filters.get("min_rating") is not None
                and (
                    rating is None
                    or rating < filters["min_rating"]
                )
            ):
                continue


            if (
                filters.get("max_rating") is not None
                and (
                    rating is None
                    or rating > filters["max_rating"]
                )
            ):
                continue


            # Runtime filter
            if (
                filters.get("min_runtime") is not None
                and (
                    runtime is None
                    or runtime < filters["min_runtime"]
                )
            ):
                continue


            if (
                filters.get("max_runtime") is not None
                and (
                    runtime is None
                    or runtime > filters["max_runtime"]
                )
            ):
                continue


            # Genre filter
            genre = filters.get("genre")

            if genre:
                movie_genres = full_movie.get("genres", [])

                genre_names = {
                    str(item.get("name", "")).strip().lower()
                    for item in movie_genres
                }

                if genre.lower() not in genre_names:
                    continue


            document = tmdb_movie_to_document(
                full_movie
            )




            embedding = embed_tmdb_document(
                document,
                model=self.embedding_model,
            )

            score = float(
                np.dot(
                    query_embedding[0],
                    embedding[0],
                )
            )

            combined_results.append(
                {
                    "title": full_movie.get(
                        "title"
                    ),
                    "tmdb_id": movie_id,
                    "score": score,
                    "release_year": (
                        full_movie.get(
                            "release_date",
                            ""
                        )[:4]
                    ),
                    "runtime": full_movie.get(
                        "runtime"
                    ),
                    "rating": full_movie.get(
                        "vote_average"
                    ),
                    "source": "tmdb",
                    "movie": full_movie,
                    "document": document,
                }
            )

            # Count successful results for person/latest queries.
            if person and filters.get(
                "sort_by"
            ) == "release_date_desc":

                person_results_added += 1

                # Stop as soon as we have enough results.
                if person_results_added >= requested_k:
                    break

        # -----------------------------------------------------
        # 9. FINAL RANKING
        # -----------------------------------------------------

        if person and filters.get("sort_by") == "release_date_desc":
            # For "latest" person queries, release date is the
            # primary ranking signal.
            combined_results.sort(
                key=lambda item: item["movie"].get(
                    "release_date",
                    ""
                ),
                reverse=True
            )
        else:
            # Normal RAG queries use semantic similarity.
            combined_results.sort(
                key=lambda item: item["score"],
                reverse=True
            )

        progress("🔍 Ranking the best matches...")

        progress(
            f"✨ Found {min(len(combined_results), requested_k)} relevant movies."
        )

        return combined_results[:requested_k]