from fastapi import APIRouter, HTTPException
from services.map_service import find_shortcut
from api.schemas import ChatRequest, ChatResponse, RouteRequest, RouteResponse
from agents.planner import PlannerAgent
from agents.registry import registry

# PlannerAgent is the orchestrator — it decomposes queries and dispatches to specialist agents
planner = PlannerAgent()

router = APIRouter()

@router.get("/info")
def info():
    return {
        "service": "Daari",
        "purpose": "Agentic navigation reasoning",
        "agents": registry.list(),
    }

@router.get("/agents")
def list_agents():
    return {
        "registered_agents": registry.list(),
        "total": len(registry.list()),
    }

@router.post("/shortcut", response_model=RouteResponse)
def get_shortcut(req: RouteRequest):
    result = find_shortcut(req.start_location, req.end_location)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return RouteResponse(**result)

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    response = await planner.execute(req.message)
    return ChatResponse(**response)
