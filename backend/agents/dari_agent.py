from agents.base import BaseAgent
from agents.registry import registry
from loguru import logger

class DariAgent(BaseAgent):
    """
    General-purpose chat agent — the friendly face of Daari.

    Handles small talk, greetings, and any query that doesn't match
    a specialist agent (route, locality, memory, document).
    """

    def __init__(self):
        super().__init__(name="DariAgent")
        registry.register("dari", self)

    async def execute(self, instruction: str) -> dict:
        logger.info(f"DariAgent processing: {instruction}")

        # Strip CHAT| prefix if sent by PlannerAgent
        if instruction.startswith("CHAT|"):
            msg = instruction.split("|", 1)[1] if "|" in instruction else instruction
        else:
            msg = instruction

        msg_lower = msg.lower().strip()

        # Greetings
        if msg_lower in ("hi", "hello", "hey", "namaste", "hola"):
            return {
                "type": "chat",
                "content": (
                    "Hey there! I'm **Daari** 🧭\n\n"
                    "I can help you with:\n"
                    "• **Routes** — *\"from Bangalore to Mumbai\"*\n"
                    "• **Locality facts** — *\"tell me about Bangalore\"*\n"
                    "• **Memory** — *\"where did I go last week?\"*\n"
                    "• **Docs** — *\"document all\"*\n\n"
                    "What would you like to explore?"
                )
            }

        # Goodbyes
        if any(kw in msg_lower for kw in ("bye", "goodbye", "see you", "cya")):
            return {
                "type": "chat",
                "content": "Take care and safe travels! 🚗✨"
            }

        # Help / what can you do
        if any(kw in msg_lower for kw in ("help", "what can you do", "commands", "options")):
            return {
                "type": "chat",
                "content": (
                    "Here's what I can do:\n\n"
                    "🗺️ **Route** — `\"from X to Y\"` or `\"find Bangalore\"`\n"
                    "🌍 **Locality** — `\"tell me about Bangalore\"` or `\"fun facts about Paris\"`\n"
                    "🧠 **Memory** — `\"where did I go?\"` or `\"remember I like scenic routes\"`\n"
                    "📚 **Docs** — `\"document all\"` or `\"update docs\"`\n\n"
                    "Just type naturally and I'll route you to the right agent!"
                )
            }

        # Default friendly fallback
        return {
            "type": "chat",
            "content": (
                "I'm not sure I understood that perfectly, but I'm learning!\n\n"
                "Try asking me for a **route**, **fun facts** about a place, "
                "or ask about your **travel history**."
            )
        }
