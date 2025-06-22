"""Router pour les endpoints core (/, /api, /health)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from ...models.schemas import APIResponse
from ...utils.logging import get_logger
from ..ml_manager import get_ml_manager
from ...config.database import db_manager
from ...llm.ollama import ollama_client

logger = get_logger("core_router")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Interface web principale."""
    # TODO: Servir l'interface HTML/JS depuis static/
    return HTMLResponse(content="""
    <html>
        <head><title>Scrapinium API</title></head>
        <body>
            <h1>🕸️ Scrapinium API</h1>
            <p>API de scraping intelligent avec LLMs</p>
            <p><a href="/docs">📚 Documentation API</a></p>
        </body>
    </html>
    """)


@router.get("/api")
async def api_info():
    """Information générale sur l'API."""
    return APIResponse.success_response(
        data={
            "name": "Scrapinium API",
            "version": "0.3.0",
            "description": "API de scraping intelligent avec LLMs et ML",
        },
        message="Informations API récupérées"
    )


@router.get("/health")
async def health_check():
    """Vérification de santé de l'API."""
    health_status = {
        "api": "healthy",
        "ollama": "unknown", 
        "database": "unknown",
        "ml_pipeline": "unknown",
    }

    # Vérifier Ollama
    try:
        ollama_healthy = await ollama_client.health_check()
        health_status["ollama"] = "healthy" if ollama_healthy else "unhealthy"
    except Exception:
        health_status["ollama"] = "error"

    # Vérifier la base de données
    try:
        async with db_manager.get_async_session() as session:
            await session.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception:
        health_status["database"] = "error"

    # Vérifier le pipeline ML
    try:
        ml_manager = get_ml_manager()
        if ml_manager.is_available():
            health_status["ml_pipeline"] = "healthy"
        else:
            error_msg = ml_manager.get_initialization_error()
            health_status["ml_pipeline"] = "unavailable"
            if error_msg:
                health_status["ml_pipeline_error"] = error_msg
    except Exception as e:
        health_status["ml_pipeline"] = "error"
        health_status["ml_pipeline_error"] = str(e)

    return health_status