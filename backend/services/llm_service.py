import httpx
import json
from loguru import logger

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma4:31b:cloud"

SYSTEM_PROMPT = """You are Dari, an intelligent navigation assistant.
Your goal is to figure out what the user wants.

If the user is asking for directions, a route, or a shortcut between two places, you must extract the start and end locations and reply ONLY with a valid JSON object in this exact format:
{
    "intent": "route",
    "start": "extracted start location",
    "end": "extracted end location"
}

If the user is asking to find, navigate to, or locate a single place (e.g., "find Bangalore", "where is Paris", "navigate to Tokyo"), reply ONLY with a valid JSON object in this format:
{
    "intent": "route",
    "start": null,
    "end": "extracted location"
}

If the user is asking about documents, files, reading something, managing their library, OR asking to generate/update/refresh/create documentation for the codebase, reply ONLY with a valid JSON object in this format:
{
    "intent": "document",
    "query": "the user's request about documents or documentation"
}

If the user is just chatting or asking a general question, reply ONLY with a valid JSON object in this format:
{
    "intent": "chat",
    "message": "your helpful response"
}

Do not include any text outside the JSON object. Just return the JSON.
"""

async def analyze_user_query(user_message: str):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": {
            "temperature": 0.0 # Low temperature for reliable JSON output
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["message"]["content"]
            
            # Try to parse the JSON
            try:
                # Sometimes LLMs wrap JSON in markdown blocks
                if content.startswith("```json"):
                    content = content.strip("```json").strip("```").strip()
                
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {content}")
                return {
                    "intent": "chat",
                    "message": "I'm having trouble understanding. Can you rephrase that?"
                }
                
    except Exception as e:
        logger.error(f"Error communicating with Ollama: {e}")
        return {
            "intent": "error",
            "message": "My AI brain (Ollama) seems to be offline. Make sure the Ollama app is running!"
        }
