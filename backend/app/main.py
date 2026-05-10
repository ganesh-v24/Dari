from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import setup_logging
from api.routes import router
from loguru import logger


def _register_agents():
    """Instantiate and register every agent into the global AgentRegistry."""
    from agents.dari_agent import DariAgent
    from agents.document_agent import DocumentAgent
    from agents.route_agent import RouteAgent
    from agents.locality_agent import LocalityAgent
    from agents.user_memory_agent import UserMemoryAgent
    from agents.planner import PlannerAgent
    from agents.registry import registry

    DariAgent()          # auto-registers as "dari"
    DocumentAgent()      # auto-registers as "document"
    RouteAgent()         # auto-registers as "route"
    LocalityAgent()      # auto-registers as "locality"
    UserMemoryAgent()    # auto-registers as "memory"
    registry.register("planner", PlannerAgent())
    logger.info(f"🤖 AgentRegistry: {registry.list()}")

async def _run_document_agent_on_startup():
    """Run DocumentAgent in the background on every backend startup."""
    try:
        # Small delay so the server finishes booting before we start heavy work
        await asyncio.sleep(3)
        logger.info("🔄 DocumentAgent: auto-run on startup (update docs)…")
        from agents.registry import registry
        agent = registry.get("document")
        result = await agent.execute("update docs")
        logger.info(f"✅ DocumentAgent startup run complete: {result.get('content', '')[:120]}")
    except Exception as exc:
        logger.error(f"❌ DocumentAgent startup run failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    setup_logging()
    logger.info("🚀 Dari backend starting up…")
    _register_agents()
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("🛑 Dari backend shutting down…")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Daari API",
        version="0.1.0",
        description="Agentic AI-powered navigation reasoning system",
        lifespan=lifespan,
    )

    app.include_router(router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app

app = create_app()

