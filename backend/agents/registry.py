from typing import Any, Dict
from loguru import logger

class AgentRegistry:
    """Central registry for all agents in the Dari system.

    Usage:
        from agents.registry import registry
        dari = registry.get("dari")
        registry.register("planner", PlannerAgent())
    """

    def __init__(self):
        self._agents: Dict[str, Any] = {}

    def register(self, name: str, agent: Any):
        self._agents[name.lower()] = agent
        logger.info(f"AgentRegistry: registered '{name}'")

    def get(self, name: str) -> Any:
        agent = self._agents.get(name.lower())
        if agent is None:
            raise KeyError(f"No agent registered under name '{name}'")
        return agent

    def list(self) -> list[str]:
        return list(self._agents.keys())

    def has(self, name: str) -> bool:
        return name.lower() in self._agents


# Global singleton — import this everywhere
registry = AgentRegistry()
