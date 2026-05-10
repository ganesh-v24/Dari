import json
import hashlib
from pathlib import Path
from typing import Optional, Tuple, List
from loguru import logger

ROUTE_MEMORY_PATH = Path(__file__).resolve().parents[1] / "data" / "route_memory.json"
ROUTE_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)

class RouteMemory:
    """
    Simple JSON-backed cache for geocoded coordinates and computed routes.
    Keyed by a hash of start_name + end_name so identical queries are instant.
    """

    def __init__(self, path: Path = ROUTE_MEMORY_PATH):
        self._path = path
        self._store: dict = self._load()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("RouteMemory: corrupt store, resetting")
        return {}

    def _save(self):
        self._path.write_text(json.dumps(self._store, indent=2), encoding="utf-8")

    @staticmethod
    def _key(start: Optional[str], end: str) -> str:
        """Deterministic hash key for a route query."""
        raw = f"{start or '__NONE__'}::{end}"
        return hashlib.md5(raw.encode()).hexdigest()

    # ── Public API ───────────────────────────────────────────────────────────

    def get(self, start: Optional[str], end: str) -> Optional[dict]:
        key = self._key(start, end)
        hit = self._store.get(key)
        if hit:
            logger.info(f"RouteMemory: cache hit for '{start}' → '{end}'")
        return hit

    def set(self, start: Optional[str], end: str, payload: dict):
        key = self._key(start, end)
        self._store[key] = payload
        self._save()
        logger.info(f"RouteMemory: cached route '{start}' → '{end}'")

    def forget(self, start: Optional[str], end: str) -> bool:
        key = self._key(start, end)
        if key in self._store:
            del self._store[key]
            self._save()
            return True
        return False

    def clear(self):
        self._store.clear()
        self._save()
        logger.info("RouteMemory: cleared all entries")

    def stats(self) -> dict:
        return {"entries": len(self._store), "path": str(self._path)}


# Global singleton
route_memory = RouteMemory()
