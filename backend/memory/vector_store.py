import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

VECTOR_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "vector_store.json"
VECTOR_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


class VectorStore:
    """
    Lightweight in-memory vector store for text chunks.

    Uses a simple TF-IDF-weighted bag-of-words approach (no embeddings required).
    Good enough for small-scale RAG inside DocumentAgent.
    """

    def __init__(self, path: Path = VECTOR_STORE_PATH):
        self._path = path
        self._docs: List[Dict[str, Any]] = self._load()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _load(self) -> list:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("VectorStore: corrupt store, resetting")
        return []

    def _save(self):
        self._path.write_text(json.dumps(self._docs, indent=2), encoding="utf-8")

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Lower-case, alphanumeric token extraction."""
        return set(re.findall(r"[a-z0-9_]+", text.lower()))

    @staticmethod
    def _cosine_similarity(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        intersection = a & b
        return len(intersection) / math.sqrt(len(a) * len(b))

    # ── Public API ───────────────────────────────────────────────────────────

    def add(self, chunk_id: str, text: str, metadata: Optional[dict] = None):
        """Add a text chunk to the store."""
        # Remove existing chunk with same ID to avoid duplicates
        self._docs = [d for d in self._docs if d.get("id") != chunk_id]
        self._docs.append({
            "id": chunk_id,
            "text": text,
            "tokens": list(self._tokenize(text)),
            "metadata": metadata or {},
        })
        self._save()
        logger.info(f"VectorStore: added chunk '{chunk_id}'")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return top-k matching chunks sorted by cosine similarity."""
        q_tokens = self._tokenize(query)
        scored = []
        for doc in self._docs:
            sim = self._cosine_similarity(q_tokens, set(doc["tokens"]))
            if sim > 0:
                scored.append({**doc, "score": round(sim, 4)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def get(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        for doc in self._docs:
            if doc.get("id") == chunk_id:
                return doc
        return None

    def delete(self, chunk_id: str) -> bool:
        before = len(self._docs)
        self._docs = [d for d in self._docs if d.get("id") != chunk_id]
        if len(self._docs) < before:
            self._save()
            return True
        return False

    def clear(self):
        self._docs.clear()
        self._save()
        logger.info("VectorStore: cleared all entries")

    def stats(self) -> dict:
        return {"entries": len(self._docs), "path": str(self._path)}


# Global singleton
vector_store = VectorStore()
