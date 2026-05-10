import re
from typing import Optional, Dict, Any
from agents.base import BaseAgent
from agents.registry import registry
from services.map_service import find_shortcut, get_coords
from memory.route_memory import route_memory
from loguru import logger


class RouteAgent(BaseAgent):
    """
    Specialist agent for geocoding places and finding walking routes.
    Uses OpenStreetMap via osmnx and caches results in RouteMemory.
    """

    def __init__(self):
        super().__init__(name="RouteAgent")
        registry.register("route", self)

    # ── Instruction parsers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_route(msg: str):
        """ROUTE|start|end  →  (start, end)"""
        if msg.startswith("ROUTE|"):
            parts = msg.split("|", 2)
            if len(parts) == 3:
                start = parts[1].strip() or None
                end = parts[2].strip()
                return start, end
        return None, None

    @staticmethod
    def _parse_find(msg: str):
        """FIND|place  →  place"""
        if msg.startswith("FIND|"):
            parts = msg.split("|", 1)
            if len(parts) == 2:
                return parts[1].strip()
        return None

    # ── Core logic ───────────────────────────────────────────────────────────

    async def execute(self, instruction: str) -> Dict[str, Any]:
        logger.info(f"RouteAgent processing: {instruction}")

        # Try planner instruction formats first
        start, end = self._parse_route(instruction)
        if end:
            return await self._handle_route(start, end)

        place = self._parse_find(instruction)
        if place:
            return await self._handle_find(place)

        # Fallback: try naive keyword extraction
        from utils.text import extract_place_names
        places = extract_place_names(instruction)
        if len(places) >= 2:
            return await self._handle_route(places[0], places[1])
        if len(places) == 1:
            return await self._handle_find(places[0])

        return {
            "type": "chat",
            "content": "I couldn't figure out which places you want a route for. Could you rephrase?"
        }

    async def _handle_find(self, place: str) -> Dict[str, Any]:
        """Single-location lookup: geocode and return coords.

        If geocoding fails, attempts to split the string on common
        route separators (" to ", " and ") and retry as a two-location route.
        """
        logger.info(f"RouteAgent: looking up '{place}'")

        cached = route_memory.get(None, place)
        if cached and cached.get("end_coords"):
            return {
                "type": "route",
                "content": f"Showing cached location for {place}.",
                "data": cached
            }

        coords = get_coords(place)
        if coords:
            payload = {
                "success": True,
                "end_coords": coords,
                "route": []
            }
            route_memory.set(None, place, payload)
            return {
                "type": "route",
                "content": f"Showing location for {place}.",
                "data": payload
            }

        # Fallback: maybe the user said something like "bangalore to mumbai shortest route"
        # Treat it as a route if we can split on a separator and strip trailing noise.
        for sep in (" to ", " and "):
            if sep in place.lower():
                parts = place.lower().split(sep, 1)
                if len(parts) == 2:
                    start, end = parts[0].strip(), parts[1].strip()
                    # Strip common trailing route noise
                    end = re.sub(
                        r"\s*(shortest|fastest|quickest|best)?\s*(route|path|way|directions)\s*$",
                        "", end, flags=re.I
                    ).strip()
                    if start and end:
                        logger.info(f"RouteAgent: retrying '{place}' as route {start} → {end}")
                        return await self._handle_route(start, end)

        return {
            "type": "chat",
            "content": f"Sorry, I couldn't find coordinates for '{place}'."
        }

    async def _handle_route(self, start: Optional[str], end: str) -> Dict[str, Any]:
        """Two-location route: geocode both, find shortest path."""
        logger.info(f"RouteAgent: route from '{start}' to '{end}'")

        cached = route_memory.get(start, end)
        if cached and cached.get("route"):
            return {
                "type": "route",
                "content": f"Found a cached shortcut from {start} to {end}!",
                "data": cached
            }

        route_result = find_shortcut(start, end)
        if "error" in route_result:
            return {
                "type": "chat",
                "content": f"I tried to find a route, but: {route_result['error']}"
            }

        route_memory.set(start, end, route_result)
        return {
            "type": "route",
            "content": f"Found a shortcut from {start} to {end}!",
            "data": route_result
        }
