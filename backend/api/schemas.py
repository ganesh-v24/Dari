from pydantic import BaseModel, Field
from typing import Optional, Any

# ── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's natural-language message")

class ChatResponse(BaseModel):
    type: str = Field(..., description="'chat' | 'route' | 'document'")
    content: str = Field(..., description="Human-readable response text")
    data: Optional[dict] = Field(None, description="Structured payload (route coords, etc.)")

# ── Route / Navigation ────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    start_location: str = Field(..., description="Starting place name or address")
    end_location: str = Field(..., description="Destination place name or address")

class RouteResponse(BaseModel):
    success: bool
    start_coords: Optional[tuple[float, float]] = None
    end_coords: Optional[tuple[float, float]] = None
    route: list[list[float]] = Field(default_factory=list, description="[[lat, lon], ...]")
    error: Optional[str] = None

# ── Document ─────────────────────────────────────────────────────────────────

class DocumentRequest(BaseModel):
    query: str = Field(..., description="e.g. 'document all', 'update docs', 'document agents/dari_agent.py'")

class DocumentResponse(BaseModel):
    type: str = "chat"
    content: str

# ── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
