# Dari

Agentic AI-powered navigation reasoning system using LLMs and geospatial data.

Daari (Kannada: route/path) is an AI-powered navigation reasoning system that uses agentic AI and advanced retrieval-augmented generation to interpret geospatial routes and provide human-friendly, context-aware directions.

## Vision

Traditional navigation systems provide routes. Daari explains, reasons, and adapts routes using AI agents.

## Key Concepts

- **Agentic AI** — Planner–executor pattern with specialized agents
- **Advanced RAG** over structured geospatial data
- **LLM reasoning** over routes, localities, and user preferences
- **Multi-agent orchestration** — Route, Locality, Memory, Document, and Chat agents

## Tech Stack

- **Backend:** Python, FastAPI
- **AI:** Ollama LLMs, agent-based orchestration
- **Frontend:** React + Vite
- **Maps:** OpenStreetMap (osmnx, geopy)
- **Deployment:** Free-tier cloud services

## Agents

| Agent | Purpose |
|-------|---------|
| `PlannerAgent` | Decomposes user queries and dispatches to specialist agents |
| `RouteAgent` | Geocoding and street-level routing via OSM |
| `LocalityAgent` | Fun facts and cultural notes about places |
| `UserMemoryAgent` | Remembers route history and preferences |
| `DocumentAgent` | Auto-generates codebase documentation |
| `DariAgent` | General chat fallback and greetings |

## Status

🚧 In active development
