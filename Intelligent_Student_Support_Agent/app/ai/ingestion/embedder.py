"""Local vector embedder utilizing Hugging Face SentenceTransformer models."""

from typing import Optional
from sentence_transformers import SentenceTransformer
from app.config.settings import settings
from app.utils.logger import logger


class LocalEmbedder:
    """Singleton embedding generator using local Hugging Face SentenceTransformer models."""

    _model: Optional[SentenceTransformer] = None

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.embedding_model

    @classmethod
    def get_model(cls, model_name: str) -> SentenceTransformer:
        """Lazily load and cache the embedding model in memory."""
        if cls._model is None:
            logger.info(f"Loading local embedding model: '{model_name}' (this may take a few moments on first run)...")
            cls._model = SentenceTransformer(model_name, trust_remote_code=True)
            logger.info(f"Embedding model '{model_name}' loaded successfully into memory.")
        return cls._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Compute 1536-dimensional embeddings for a batch of text chunks."""
        if not texts:
            return []
        model = self.get_model(self.model_name)
        logger.info(f"Embedding batch of {len(texts)} document chunks...")
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Compute embedding vector for a single search query string."""
        model = self.get_model(self.model_name)
        embedding = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
        return embedding.tolist()
