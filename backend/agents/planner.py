import re
from typing import List, Dict, Any
from agents.base import BaseAgent
from agents.registry import registry
from loguru import logger

class Task:
    """A single sub-task produced by the Planner."""
    def __init__(self, agent_name: str, instruction: str, depends_on: list[str] | None = None):
        self.agent_name = agent_name
        self.instruction = instruction
        self.depends_on = depends_on or []
        self.result: Any = None

class PlannerAgent(BaseAgent):
    """
    Decomposes complex user requests into a sequence of sub-tasks
    dispatched to specialist agents (route, locality, memory, document, chat).

    Keyword-driven — no LLM call needed for planning.
    """

    def __init__(self):
        super().__init__(name="PlannerAgent")

    # ── Keyword sets ─────────────────────────────────────────────────────────

    _ROUTE_PATTERNS = (
        re.compile(r"(?:from|between)\s+(.+?)\s+(?:to|and)\s+(.+?)(?:\?|$)", re.I),
        re.compile(r"(?:shortcut|route|directions|navigate)\s+(?:from|to)?\s*(.+?)(?:\?|$)", re.I),
    )

    _DOC_KEYWORDS = ("document all", "update docs", "generate docs", "refresh docs", "create docs")
    _FIND_KEYWORDS = ("find", "locate", "where is", "show me", "go to", "take me to")

    _LOCALITY_KEYWORDS = (
        "tell me about", "fun facts", "what's special", "history of",
        "about ", "things to do in", "know about",
    )
    _LOCALITY_PLACE_RE = re.compile(
        r"(?:tell me about|fun facts? (?:about|on)|what's special (?:about|in)|history of|about|things to do in|know about)\s+(.+?)(?:\?|$)",
        re.IGNORECASE
    )

    _MEMORY_KEYWORDS = (
        "where did i go", "my history", "my routes", "recent trips",
        "my preferences", "what do i like", "my settings",
        "my favorites", "favorite places", "places i like",
        "remember ", "forget everything", "clear history", "reset memory",
    )

    # ── Planning ─────────────────────────────────────────────────────────────

    def plan(self, user_message: str) -> List[Task]:
        """Return a list of tasks derived from the user message."""
        msg_lower = user_message.lower()
        tasks: List[Task] = []

        # 1. Route / navigation
        start, end = self._extract_route(user_message)
        if end:
            tasks.append(Task(
                agent_name="route",
                instruction=f"ROUTE|{start or ''}|{end}"
            ))

        # 2. Single-location find
        if not end and any(kw in msg_lower for kw in self._FIND_KEYWORDS):
            match = re.search(r"(?:find|locate|where is|show me|go to|take me to)\s+(.+?)(?:\?|$)", user_message, re.I)
            if match:
                tasks.append(Task(
                    agent_name="route",
                    instruction=f"FIND|{match.group(1).strip()}"
                ))

        # 3. Locality / fun facts
        if any(kw in msg_lower for kw in self._LOCALITY_KEYWORDS):
            tasks.append(Task(
                agent_name="locality",
                instruction=user_message
            ))

        # 4. User memory
        if any(kw in msg_lower for kw in self._MEMORY_KEYWORDS):
            tasks.append(Task(
                agent_name="memory",
                instruction=user_message
            ))

        # 5. Documentation
        if any(kw in msg_lower for kw in self._DOC_KEYWORDS):
            tasks.append(Task(
                agent_name="document",
                instruction=user_message
            ))

        # 6. Fallback chat
        if not tasks:
            tasks.append(Task(
                agent_name="dari",
                instruction=f"CHAT|{user_message}"
            ))

        logger.info(f"PlannerAgent: planned {len(tasks)} task(s) → {[t.agent_name for t in tasks]}")
        return tasks

    def _extract_route(self, msg: str):
        """Try to pull (start, end) from message. Either may be None."""
        for pattern in self._ROUTE_PATTERNS:
            match = pattern.search(msg)
            if match:
                if len(match.groups()) == 2:
                    start = match.group(1).strip()
                    end = match.group(2).strip()
                    # Strip trailing route noise (e.g., "mumbai shortest route")
                    end = re.sub(
                        r"\s*(shortest|fastest|quickest|best)?\s*(route|path|way|directions)\s*$",
                        "", end, flags=re.I
                    ).strip()
                    return start, end
                return None, match.group(1).strip()
        return None, None

    # ── Execution ────────────────────────────────────────────────────────────

    async def execute(self, user_message: str) -> Dict[str, Any]:
        tasks = self.plan(user_message)
        results: List[Dict[str, Any]] = []

        for task in tasks:
            try:
                agent = registry.get(task.agent_name)
            except KeyError:
                logger.error(f"PlannerAgent: agent '{task.agent_name}' not found in registry")
                results.append({
                    "type": "chat",
                    "content": f"Oops — the '{task.agent_name}' agent isn't available right now."
                })
                continue

            task.result = await agent.execute(task.instruction)
            results.append(task.result)

            # Side-effect: record successful routes in user memory
            if task.agent_name == "route" and isinstance(task.result, dict):
                data = task.result.get("data", {})
                if data and data.get("success"):
                    try:
                        mem = registry.get("memory")
                        # Extract start/end from instruction for memory
                        parts = task.instruction.split("|")
                        if len(parts) == 3:
                            s, e = parts[1], parts[2]
                            route_coords = data.get("route", [])
                            mem.record_route(s or "unknown", e, route_coords)
                    except KeyError:
                        pass  # memory agent not registered yet

        # Single task → direct result
        if len(results) == 1:
            return results[0]

        # Multi-task → merge into chat
        merged = []
        for r in results:
            if isinstance(r, dict) and "content" in r:
                merged.append(r["content"])
            else:
                merged.append(str(r))

        return {
            "type": "chat",
            "content": "\n\n".join(merged)
        }
