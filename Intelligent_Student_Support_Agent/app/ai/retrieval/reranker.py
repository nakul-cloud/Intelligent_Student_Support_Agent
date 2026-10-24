"""Cross-Encoder Re-Ranker module for deep semantic relevance scoring.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for loading the CrossEncoder
  model, caching pairwise relevance scores, and re-ranking candidate retrieval chunks.
- Open/Closed (OCP): Configured flexibly via Settings with injectable model names,
  devices, and batch sizes without modifying class internals.
- High Performance:
  1. Thread-safe singleton pattern with double-checked locking preventing redundant loads.
  2. In-memory LRU caching on query-document hash pairs for instant repeat scoring.
  3. Batch inference with torch.inference_mode() on CPU.
  4. Graceful degradation: Falls back cleanly to initial bi-encoder scores on any failure.
"""

from functools import lru_cache
import hashlib
import threading
from typing import Any, Optional
from sentence_transformers import CrossEncoder
import torch

from app.config.settings import settings
from app.utils.logger import logger


class CrossEncoderReranker:
    """Thread-safe singleton Cross-Encoder re-ranker for query-candidate scoring."""

    _model: Optional[CrossEncoder] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
    ) -> None:
        """Initialize re-ranker configurations from settings or explicit arguments."""
        self.model_name = model_name or settings.reranker_model
        self.device = device or settings.reranker_device
        self.batch_size = batch_size or settings.reranker_batch_size

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if the CrossEncoder model is already resident in memory."""
        return cls._model is not None

    @classmethod
    def get_model(cls, model_name: str, device: str = "cpu") -> CrossEncoder:
        """Thread-safely load and cache the CrossEncoder model once in memory."""
        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    logger.info(
                        f"Loading Cross-Encoder re-ranker model: '{model_name}' on device '{device}'..."
                    )
                    model = CrossEncoder(model_name, device=device)
                    cls._model = model
                    logger.info(f"Cross-Encoder re-ranker '{model_name}' loaded successfully.")
        return cls._model

    @staticmethod
    @lru_cache(maxsize=2048)
    def _cached_score_pair(query: str, doc_digest: str, model_name: str, doc_text: str) -> float:
        """LRU cache helper for (query, doc) score pairs to avoid repeated forward passes."""
        model = CrossEncoderReranker.get_model(model_name, settings.reranker_device)
        with torch.inference_mode():
            scores = model.predict([(query, doc_text)], show_progress_bar=False)
            return float(scores[0])

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Re-score and re-rank candidate chunks using joint query-document cross-encoding.

        Args:
            query: Natural language user query.
            candidates: List of candidate chunk dicts, each with 'content', 'score', and 'metadata'.
            top_k: Number of highest scoring candidates to return. Defaults to settings.reranker_top_k.

        Returns:
            Sorted list of top_k candidates with updated 'score', preserving 'bi_encoder_score'.
        """
        if not candidates:
            return []

        k = top_k if top_k is not None else settings.reranker_top_k
        clean_query = query.strip()

        # If only 1 candidate or empty query, return sliced candidates directly
        if len(candidates) <= 1 or not clean_query:
            return candidates[:k]

        try:
            model = self.get_model(self.model_name, self.device)

            # Determine pairs to score and check in-memory cache
            pairs_to_predict: list[tuple[int, str]] = []  # (index, doc_text)
            scored_candidates: list[dict[str, Any]] = []

            for idx, item in enumerate(candidates):
                item_copy = dict(item)
                # Preserve original bi-encoder score
                item_copy["bi_encoder_score"] = item.get("score", 0.0)

                doc_text = item.get("content", "").strip()
                doc_digest = hashlib.sha256(doc_text.encode("utf-8")).hexdigest()

                # Check if this exact pair is already in LRU cache
                try:
                    score = self._cached_score_pair(clean_query, doc_digest, self.model_name, doc_text)
                    item_copy["score"] = round(score, 4)
                    item_copy["rerank_score"] = round(score, 4)
                    scored_candidates.append(item_copy)
                except Exception:
                    pairs_to_predict.append((idx, doc_text))
                    scored_candidates.append(item_copy)

            # If any uncached pairs exist, run batch inference
            if pairs_to_predict:
                indices, texts = zip(*pairs_to_predict)
                batch_pairs = [(clean_query, text) for text in texts]

                with torch.inference_mode():
                    raw_scores = model.predict(
                        batch_pairs,
                        batch_size=self.batch_size,
                        show_progress_bar=False,
                    )

                for item_idx, raw_score in zip(indices, raw_scores):
                    val = float(raw_score)
                    scored_candidates[item_idx]["score"] = round(val, 4)
                    scored_candidates[item_idx]["rerank_score"] = round(val, 4)

            # Sort descending by cross-encoder re-rank score
            scored_candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)

            logger.info(
                f"Re-ranked {len(candidates)} candidates -> top {min(k, len(scored_candidates))} "
                f"using '{self.model_name}' (best score: {scored_candidates[0]['score']:.4f})"
            )
            return scored_candidates[:k]

        except Exception as exc:
            logger.warning(
                f"Cross-encoder re-ranking failed ({exc}). Gracefully falling back to bi-encoder scores."
            )
            # Safe graceful degradation: return original candidates sorted by initial score
            sorted_by_original = sorted(
                candidates,
                key=lambda x: x.get("score", 0.0),
                reverse=True,
            )
            return sorted_by_original[:k]
