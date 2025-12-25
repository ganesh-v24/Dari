from fastapi import FastAPI
from core.config import settings
from core.logging import setup_logging
from api.routes import router

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Daari API",
        version="0.1.0",
        description="Agentic AI-powered navigation reasoning system"
    )
    
    app.include_router(router)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app

app = create_app()
