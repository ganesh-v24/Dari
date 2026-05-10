import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from agents.base import BaseAgent
from agents.registry import registry
from loguru import logger

USER_MEMORY_PATH = Path(__file__).resolve().parents[1] / "data" / "user_memory.json"
USER_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)


class UserMemoryAgent(BaseAgent):
    """
    Specialist agent that remembers:
      • Routes the user has taken
      • User preferences (scenic, fastest, avoids highways, etc.)
      • Frequently searched places

    Answers queries like "Where did I go last week?" or "Remember I like scenic routes."
    """

    def __init__(self):
        super().__init__(name="UserMemoryAgent")
        registry.register("memory", self)
        self._store = self._load()

    # ── Persistence helpers ──────────────────────────────────────────────────

    def _load(self) -> dict:
        if USER_MEMORY_PATH.exists():
            try:
                return json.loads(USER_MEMORY_PATH.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("UserMemoryAgent: corrupt store, resetting")
        return {
            "route_history": [],
            "preferences": {},
            "favorite_places": [],
        }

    def _save(self):
        USER_MEMORY_PATH.write_text(json.dumps(self._store, indent=2, default=str), encoding="utf-8")

    # ── Public memory API ────────────────────────────────────────────────────

    def record_route(self, start: str, end: str, route_coords: list):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "start": start,
            "end": end,
            "num_nodes": len(route_coords),
        }
        self._store["route_history"].append(entry)
        # Keep only last 50 entries
        self._store["route_history"] = self._store["route_history"][-50:]
        # Add to favorites if new
        for place in (start, end):
            if place and place.lower() not in [p.lower() for p in self._store["favorite_places"]]:
                self._store["favorite_places"].append(place)
        self._save()
        logger.info(f"UserMemoryAgent: recorded route {start} → {end}")

    def set_preference(self, key: str, value: Any):
        self._store["preferences"][key] = value
        self._save()
        logger.info(f"UserMemoryAgent: set preference '{key}' = {value}")

    def get_preferences(self) -> dict:
        return dict(self._store["preferences"])

    def get_history(self, limit: int = 10) -> List[dict]:
        return list(reversed(self._store["route_history"][-limit:]))

    def get_favorites(self) -> List[str]:
        return list(self._store["favorite_places"])

    def clear_history(self):
        self._store["route_history"] = []
        self._save()

    # ── Instruction parsers ──────────────────────────────────────────────────

    _REMEMBER_RE = re.compile(
        r"remember\s+(?:that\s+)?(?:i\s+(?:like|prefer|want|hate|avoid)\s+)(.+)",
        re.IGNORECASE
    )

    # ── Main entry ───────────────────────────────────────────────────────────

    async def execute(self, instruction: str) -> Dict[str, Any]:
        logger.info(f"UserMemoryAgent processing: {instruction}")
        q = instruction.lower().strip()

        # ── Store preference ────────────────────────────────────────────────
        match = self._REMEMBER_RE.search(instruction)
        if match:
            pref = match.group(1).strip()
            # Naive key extraction: first word is usually the category
            words = pref.split()
            key = words[0] if words else "general"
            self.set_preference(key, pref)
            return {
                "type": "chat",
                "content": f"Got it! I'll remember that you {pref}."
            }

        # ── Retrieve history ────────────────────────────────────────────────
        if any(kw in q for kw in ("where did i go", "my history", "my routes", "past routes", "recent trips")):
            history = self.get_history(limit=5)
            if not history:
                return {
                    "type": "chat",
                    "content": "You haven't taken any routes yet. Once you start navigating, I'll keep a travel diary for you!"
                }
            lines = ["Here's your recent route history 🗺️", ""]
            for i, entry in enumerate(history, 1):
                ts = entry["timestamp"][:10]  # just the date
                lines.append(f"**{i}.** {ts}: {entry['start']} → {entry['end']}")
            return {
                "type": "chat",
                "content": "\n".join(lines)
            }

        # ── Retrieve preferences ────────────────────────────────────────────
        if any(kw in q for kw in ("my preferences", "what do i like", "my settings")):
            prefs = self.get_preferences()
            if not prefs:
                return {
                    "type": "chat",
                    "content": "I don't have any preferences saved yet. Tell me things like 'Remember I like scenic routes' and I'll store them!"
                }
            lines = ["Your saved preferences 💾", ""]
            for k, v in prefs.items():
                lines.append(f"• **{k}**: {v}")
            return {
                "type": "chat",
                "content": "\n".join(lines)
            }

        # ── Retrieve favorites ──────────────────────────────────────────────
        if any(kw in q for kw in ("my favorites", "favorite places", "places i like")):
            favs = self.get_favorites()
            if not favs:
                return {
                    "type": "chat",
                    "content": "You don't have any favorite places yet. I'll automatically add places you search for frequently!"
                }
            return {
                "type": "chat",
                "content": "Your favorite places ⭐\n\n" + "\n".join(f"• {p}" for p in favs)
            }

        # ── Clear / reset ───────────────────────────────────────────────────
        if any(kw in q for kw in ("clear history", "forget everything", "reset memory")):
            self.clear_history()
            return {
                "type": "chat",
                "content": "All route history cleared. Your preferences are still saved."
            }

        # ── Fallback ────────────────────────────────────────────────────────
        return {
            "type": "chat",
            "content": (
                "I'm your memory assistant. I can:\n"
                "• Show your **route history**\n"
                "• List your **favorite places**\n"
                "• Recall your **preferences**\n"
                "• **Remember** things you tell me\n\n"
                "What would you like to know?"
            )
        }
