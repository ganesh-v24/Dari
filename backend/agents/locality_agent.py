import httpx
import re
from typing import Dict, Any
from agents.base import BaseAgent
from agents.registry import registry
from services.map_service import get_coords
from loguru import logger

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma4:31b:cloud"

LOCALITY_PROMPT = """\
You are a witty local tour guide. The user just asked about a place.
Give 3-5 fun, surprising, or little-known facts about it.
Keep it short, conversational, and emoji-friendly.

Rules:
- One short paragraph per fact.
- Start each fact with a bold number (e.g., **1.**).
- End with a warm closing line.
- Do NOT use markdown code fences.
"""


class LocalityAgent(BaseAgent):
    """
    Specialist agent that serves fun facts, history, and cultural notes
    about any place the user mentions.
    """

    def __init__(self):
        super().__init__(name="LocalityAgent")
        registry.register("locality", self)

    _PLACE_RE = re.compile(
        r"(?:about|tell me about|fun facts? (?:about|on)|what's special (?:about|in)|where is|history of)\s+(.+?)(?:\?|$)",
        re.IGNORECASE
    )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_place(self, msg: str) -> str | None:
        match = self._PLACE_RE.search(msg)
        if match:
            return match.group(1).strip()
        # Fallback: capitalised sequences >3 chars
        from utils.text import extract_place_names
        places = extract_place_names(msg)
        return places[0] if places else None

    async def _ask_llm(self, place: str) -> str:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": LOCALITY_PROMPT},
                {"role": "user", "content": f"Tell me about {place}."}
            ],
            "stream": False,
            "options": {"temperature": 0.8},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    # ── Main entry ───────────────────────────────────────────────────────────

    async def execute(self, instruction: str) -> Dict[str, Any]:
        logger.info(f"LocalityAgent processing: {instruction}")

        place = self._extract_place(instruction)
        if not place:
            return {
                "type": "chat",
                "content": "I'd love to share fun facts, but which place are you asking about?"
            }

        # Verify the place exists by geocoding (optional, adds credibility)
        coords = get_coords(place)
        if coords:
            logger.info(f"LocalityAgent: verified '{place}' at {coords}")

        try:
            facts = await self._ask_llm(place)
        except Exception as exc:
            logger.warning(f"LocalityAgent LLM call failed: {exc}")
            # Graceful fallback without LLM
            facts = (
                f"**1.** {place} is a fascinating place with a rich cultural heritage.\n\n"
                f"**2.** It has been an important hub for trade and travel for centuries.\n\n"
                f"**3.** Local cuisine and traditions here are unique and worth exploring.\n\n"
                f"*(My AI brain is a bit sleepy right now — these are generic highlights!)*"
            )

        return {
            "type": "chat",
            "content": f"Here's what I know about **{place}** 🌍\n\n{facts}"
        }
