"""Version refactorisée de app.py avec routers modulaires."""

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..config.settings import get_settings
from ..config.database import init_database
from ..llm.ollama import ollama_client
from ..scraping.service import scraping_service
from ..models.schemas import APIResponse, ScrapingTaskCreate
from ..security.headers import security_headers_middleware, security_headers
from ..security.rate_limiter import rate_limit_middleware
from ..utils.logging import get_logger

# Gestionnaires
from .task_manager import get_task_manager
from .ml_manager import get_ml_manager
from .exception_handler import setup_exception_handlers

# Routers modulaires
from .routers import core, statistics, cache, maintenance, scraping, performance, websocket, templates

logger = get_logger("api")
settings = get_settings()


def get_ml_pipeline_or_raise():
    """Helper pour récupérer le pipeline ML ou lever une exception."""
    ml_manager = get_ml_manager()
    ml_pipeline_instance = ml_manager.get_pipeline()
    
    if not ml_pipeline_instance:
        error_msg = ml_manager.get_initialization_error() or "Pipeline ML non disponible"
        raise HTTPException(status_code=503, detail=error_msg)
    
    return ml_pipeline_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application."""
    # Startup
    logger.info("🚀 Démarrage de l'API Scrapinium...")

    # Initialiser la base de données
    try:
        init_database()
        logger.info("✅ Base de données initialisée")
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation BDD: {e}")

    # Test de connexion Ollama
    try:
        if await ollama_client.health_check():
            logger.info("✅ Ollama connecté")
        else:
            logger.warning("⚠️ Ollama non accessible - fonctionnalités LLM désactivées")
    except Exception as e:
        logger.warning(f"⚠️ Erreur de connexion Ollama: {e}")

    # Initialiser le pipeline ML
    ml_manager = get_ml_manager()
    await ml_manager.initialize()

    logger.info("🎯 API Scrapinium prête!")

    yield

    # Shutdown
    logger.info("🛑 Arrêt de l'API Scrapinium...")

    # Nettoyer les ressources ML
    try:
        await ml_manager.shutdown()
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du ML manager: {e}")

    # Nettoyer les ressources de scraping
    try:
        await scraping_service.cleanup()
        await ollama_client.cleanup()
        logger.info("✅ Ressources nettoyées")
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")

    logger.info("👋 API Scrapinium arrêtée")


def create_app() -> FastAPI:
    """Crée l'application FastAPI."""

    app = FastAPI(
        title="Scrapinium API",
        description="API de scraping intelligent avec LLMs",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configuration des middlewares de sécurité (ordre important)
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(rate_limit_middleware)  # Ajusté pour mode dev/prod
    
    # CORS sécurisé
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_headers.allowed_origins,
        allow_credentials=False,
        allow_methods=security_headers.allowed_methods,
        allow_headers=security_headers.allowed_headers,
        expose_headers=security_headers.exposed_headers,
        max_age=3600 if security_headers.production_mode else 300,
    )

    # Fichiers statiques (CSS, JS, images)
    import os
    # Trouver le dossier racine du projet (4 niveaux au-dessus de ce fichier)
    current_dir = os.path.dirname(__file__)  # /src/scrapinium/api/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # /
    static_dir = os.path.join(project_root, "static")
    
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"✅ Fichiers statiques montés depuis: {static_dir}")
    else:
        logger.warning(f"⚠️ Dossier static non trouvé: {static_dir}")
    
    # Routes modulaires
    app.include_router(core.router)
    app.include_router(statistics.router)
    app.include_router(cache.router)
    app.include_router(maintenance.router)
    app.include_router(scraping.router)
    app.include_router(templates.router)
    app.include_router(performance.router)
    app.include_router(websocket.router)
    
    # Configuration des gestionnaires d'exceptions
    setup_exception_handlers(app)

    return app




# Créer l'instance de l'application pour uvicorn
app = create_app()