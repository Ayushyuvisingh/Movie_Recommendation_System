import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_embedding_model():
    """
    Load the same embedding model used for the local MovieVerse RAG system.
    """
    return SentenceTransformer(MODEL_NAME)


def embed_tmdb_document(document, model=None):
    """
    Convert one TMDB RAG document into a normalized embedding.
    """

    if model is None:
        model = load_embedding_model()

    embedding = model.encode(
        [document],
        normalize_embeddings=True,
    )

    return np.asarray(embedding, dtype=np.float32)