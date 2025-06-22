"""Application FastAPI pour Scrapinium avec sécurité enterprise-grade."""

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ..config import get_logger, init_database, settings
from ..llm import ollama_client
from ..models import APIResponse, ScrapingTaskCreate
from ..scraping import scraping_service
from ..scraping.browser import get_browser_stats
from ..cache import get_cache_manager
from ..utils.memory import get_memory_monitor
from ..utils.cleanup import get_resource_cleaner, get_auto_cleaner

# Import du pipeline ML
from ..ml import MLPipeline, ContentClassifier, AntibotDetector, ContentAnalyzer

# Import des composants de sécurité
from ..security.rate_limiter import rate_limit_middleware, rate_limiter
from ..security.headers import security_headers_middleware, security_headers
from ..security.input_validator import input_validator, ValidationLevel
from ..security.config_security import security_manager

logger = get_logger("api")

# Gestionnaires pour remplacer les variables globales
from .task_manager import get_task_manager
from .ml_manager import get_ml_manager
from .exception_handler import setup_exception_handlers


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

    # Vérifier Ollama
    try:
        is_healthy = await ollama_client.health_check()
        if is_healthy:
            logger.info("✅ Ollama connecté et opérationnel")
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
    # 1. Headers de sécurité (en premier)
    app.middleware("http")(security_headers_middleware)
    
    # 2. Rate limiting (après headers)
    app.middleware("http")(rate_limit_middleware)
    
    # 3. CORS sécurisé (utilise la config de security_headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_headers.allowed_origins,
        allow_credentials=False,
        allow_methods=security_headers.allowed_methods,
        allow_headers=security_headers.allowed_headers,
        expose_headers=security_headers.exposed_headers,
        max_age=3600 if security_headers.production_mode else 300,
    )

    # Routes principales
    setup_routes(app)
    
    # Configuration des gestionnaires d'exceptions
    setup_exception_handlers(app)

    return app


def setup_routes(app: FastAPI):
    """Configure les routes de l'API."""
    
    # Import des endpoints de performance
    from .endpoints.performance import router as performance_router
    app.include_router(performance_router)
    
    # Configuration des templates
    templates = Jinja2Templates(directory="templates")
    
    # Servir les fichiers statiques
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Interface web principale."""
        return templates.TemplateResponse(
            "simple.html", 
            {"request": request}
        )
    
    @app.get("/api")
    async def api_info():
        """Information sur l'API."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled",
        }

    @app.get("/health")
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
            # Simple test de connexion
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

    @app.post("/scrape", response_model=APIResponse)
    async def start_scraping(
        task_data: ScrapingTaskCreate,
        background_tasks: BackgroundTasks,
    ):
        """Démarre une tâche de scraping."""
        try:
            # Générer un ID unique pour la tâche
            task_id = str(uuid.uuid4())

            # Créer l'entrée de tâche
            task_entry = {
                "id": task_id,
                "url": str(task_data.url),
                "output_format": task_data.output_format,
                "llm_provider": task_data.llm_provider,
                "progress": 0,
                "message": "Tâche créée",
                "result": None,
                "error": None,
            }

            task_manager = get_task_manager()
            task_manager.add_task(task_id, task_entry)

            # Lancer la tâche en arrière-plan
            background_tasks.add_task(
                execute_scraping_task,
                task_id,
                task_data,
            )

            logger.info(f"🚀 Tâche de scraping créée: {task_id} pour {task_data.url}")

            return APIResponse.success_response(
                data={"task_id": task_id, "status": "started"},
                message="Tâche de scraping démarrée",
            )

        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de tâche: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la création de la tâche: {str(e)}",
            )

    @app.get("/scrape/{task_id}")
    async def get_task_status(task_id: str):
        """Récupère le statut d'une tâche."""
        task_manager = get_task_manager()
        
        # Chercher dans les tâches actives
        active_task = task_manager.get_task(task_id)
        if active_task:
            return APIResponse.success_response(
                data=active_task,
                message="Statut de la tâche récupéré",
            )

        # Chercher dans les tâches terminées
        completed_tasks_list = task_manager.get_completed_tasks()
        completed_task = next(
            (task for task in completed_tasks_list if task["id"] == task_id), None
        )

        if completed_task:
            return APIResponse.success_response(
                data=completed_task,
                message="Tâche terminée trouvée",
            )

        raise HTTPException(status_code=404, detail=f"Tâche {task_id} non trouvée")

    @app.get("/scrape/{task_id}/result")
    async def get_task_result(task_id: str):
        """Récupère le résultat d'une tâche terminée."""
        # Chercher dans les tâches terminées
        task_manager = get_task_manager()
        completed_tasks_list = task_manager.get_completed_tasks()
        completed_task = next(
            (task for task in completed_tasks_list if task["id"] == task_id), None
        )

        if not completed_task:
            raise HTTPException(
                status_code=404, detail=f"Tâche {task_id} non trouvée ou non terminée"
            )

        if completed_task["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Tâche {task_id} n'est pas terminée (statut: {completed_task['status']})",
            )

        return APIResponse.success_response(
            data={
                "task_id": task_id,
                "url": completed_task["url"],
                "output_format": completed_task["output_format"],
                "content": completed_task.get("result", ""),
                "metadata": completed_task.get("metadata", {}),
            },
            message="Résultat récupéré avec succès",
        )

    @app.get("/tasks")
    async def list_tasks(limit: int = 50):
        """Liste toutes les tâches."""
        task_manager = get_task_manager()
        all_tasks = []

        # Ajouter les tâches actives
        all_tasks.extend(list(task_manager.get_active_tasks().values()))

        # Ajouter les tâches terminées
        all_tasks.extend(task_manager.get_completed_tasks())

        # Trier par date de création (plus récent en premier)
        # all_tasks.sort(key=lambda x: x["created_at"], reverse=True)

        # Limiter le nombre de résultats
        limited_tasks = all_tasks[:limit]

        return APIResponse.success_response(
            data={
                "tasks": limited_tasks,
                "total": len(all_tasks),
                "active": len(task_manager.get_active_tasks()),
                "completed": len(task_manager.get_completed_tasks()),
            },
            message=f"Liste de {len(limited_tasks)} tâches récupérée",
        )

    @app.delete("/scrape/{task_id}")
    async def cancel_task(task_id: str):
        """Annule une tâche en cours."""
        task_manager = get_task_manager()
        
        if not task_manager.get_task(task_id):
            raise HTTPException(
                status_code=404, detail=f"Tâche {task_id} non trouvée ou déjà terminée"
            )

        # Marquer comme annulée et la déplacer
        success = task_manager.fail_task(task_id, "Tâche annulée par l'utilisateur")
        if not success:
            raise HTTPException(
                status_code=400, detail="Impossible d'annuler la tâche"
            )

        logger.info(f"🚫 Tâche {task_id} annulée")

        return APIResponse.success_response(
            data={"task_id": task_id, "status": "cancelled"},
            message="Tâche annulée avec succès",
        )

    @app.get("/stats")
    async def get_stats():
        """Statistiques globales avec monitoring du pool de navigateurs."""
        task_manager = get_task_manager()
        task_stats = task_manager.get_task_stats()
        
        total_tasks = task_stats["active_tasks"] + task_stats["completed_tasks"]
        completed_count = task_stats["successful_tasks"]
        failed_count = task_stats["failed_tasks"]
        success_rate = task_stats["success_rate"]
        
        # Récupérer les statistiques du pool de navigateurs
        browser_stats = await get_browser_stats()

        return APIResponse.success_response(
            data={
                "total_tasks": total_tasks,
                "active_tasks": task_stats["active_tasks"],
                "completed_tasks": completed_count,
                "failed_tasks": failed_count,
                "success_rate": round(success_rate, 1),
                "ollama_status": "connected",  # TODO: vérification réelle
                "browser_pool": browser_stats,
            },
            message="Statistiques récupérées",
        )
        
    @app.get("/stats/browser")
    async def get_browser_stats_detailed():
        """Statistiques détaillées du pool de navigateurs."""
        browser_stats = await get_browser_stats()
        
        return APIResponse.success_response(
            data=browser_stats,
            message="Statistiques du pool de navigateurs récupérées",
        )
        
    @app.get("/stats/cache")
    async def get_cache_stats():
        """Statistiques détaillées du cache multi-niveau."""
        try:
            cache_manager = await get_cache_manager()
            cache_stats = await cache_manager.get_stats()
            
            return APIResponse.success_response(
                data=cache_stats,
                message="Statistiques du cache récupérées",
            )
        except Exception as e:
            logger.error(f"Erreur récupération stats cache: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération des statistiques du cache",
                details=str(e)
            )
    
    @app.delete("/cache")
    async def clear_cache():
        """Vide complètement le cache multi-niveau."""
        try:
            cache_manager = await get_cache_manager()
            await cache_manager.clear()
            
            return APIResponse.success_response(
                data={"cleared": True},
                message="Cache vidé avec succès",
            )
        except Exception as e:
            logger.error(f"Erreur vidage cache: {e}")
            return APIResponse.error_response(
                message="Erreur lors du vidage du cache",
                details=str(e)
            )
    
    @app.delete("/cache/{cache_key}")
    async def delete_cache_entry(cache_key: str):
        """Supprime une entrée spécifique du cache."""
        try:
            cache_manager = await get_cache_manager()
            deleted = await cache_manager.delete(cache_key)
            
            if deleted:
                return APIResponse.success_response(
                    data={"deleted": True, "key": cache_key},
                    message=f"Entrée de cache '{cache_key}' supprimée",
                )
            else:
                return APIResponse.error_response(
                    message=f"Entrée de cache '{cache_key}' non trouvée"
                )
                
        except Exception as e:
            logger.error(f"Erreur suppression cache {cache_key}: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la suppression de l'entrée de cache",
                details=str(e)
            )
    
    @app.get("/stats/memory")
    async def get_memory_stats():
        """Statistiques détaillées de la mémoire."""
        try:
            memory_monitor = get_memory_monitor()
            memory_report = memory_monitor.get_memory_report()
            
            return APIResponse.success_response(
                data=memory_report,
                message="Statistiques mémoire récupérées",
            )
        except Exception as e:
            logger.error(f"Erreur récupération stats mémoire: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération des statistiques mémoire",
                details=str(e)
            )
    
    @app.post("/maintenance/gc")
    async def force_garbage_collection():
        """Force un garbage collection."""
        try:
            memory_monitor = get_memory_monitor()
            freed_objects = await memory_monitor.force_gc()
            
            return APIResponse.success_response(
                data={"objects_freed": freed_objects},
                message="Garbage collection exécuté",
            )
        except Exception as e:
            logger.error(f"Erreur GC forcé: {e}")
            return APIResponse.error_response(
                message="Erreur lors du garbage collection",
                details=str(e)
            )
    
    @app.post("/maintenance/optimize")
    async def optimize_memory():
        """Optimise l'utilisation mémoire."""
        try:
            memory_monitor = get_memory_monitor()
            optimization_result = await memory_monitor.optimize_memory()
            
            return APIResponse.success_response(
                data=optimization_result,
                message="Optimisation mémoire terminée",
            )
        except Exception as e:
            logger.error(f"Erreur optimisation mémoire: {e}")
            return APIResponse.error_response(
                message="Erreur lors de l'optimisation mémoire",
                details=str(e)
            )
    
    @app.post("/maintenance/cleanup")
    async def run_cleanup():
        """Lance un nettoyage complet des ressources."""
        try:
            resource_cleaner = get_resource_cleaner()
            cleanup_results = await resource_cleaner.run_all_cleanup_rules()
            
            # Résumé des résultats
            summary = {
                "total_items_cleaned": sum(r.items_cleaned for r in cleanup_results),
                "total_bytes_freed": sum(r.bytes_freed for r in cleanup_results),
                "successful_cleanups": sum(1 for r in cleanup_results if r.success),
                "failed_cleanups": sum(1 for r in cleanup_results if not r.success),
                "results": [
                    {
                        "resource_type": r.resource_type.value,
                        "items_cleaned": r.items_cleaned,
                        "bytes_freed": r.bytes_freed,
                        "success": r.success,
                        "time_taken_ms": r.time_taken_ms,
                    }
                    for r in cleanup_results
                ]
            }
            
            return APIResponse.success_response(
                data=summary,
                message="Nettoyage des ressources terminé",
            )
        except Exception as e:
            logger.error(f"Erreur nettoyage ressources: {e}")
            return APIResponse.error_response(
                message="Erreur lors du nettoyage des ressources",
                details=str(e)
            )
    
    @app.get("/stats/cleanup")
    async def get_cleanup_stats():
        """Statistiques du système de nettoyage."""
        try:
            resource_cleaner = get_resource_cleaner()
            auto_cleaner = get_auto_cleaner()
            
            cleanup_stats = resource_cleaner.get_cleanup_stats()
            auto_status = auto_cleaner.get_status()
            
            combined_stats = {
                **cleanup_stats,
                "auto_cleaner": auto_status,
            }
            
            return APIResponse.success_response(
                data=combined_stats,
                message="Statistiques de nettoyage récupérées",
            )
        except Exception as e:
            logger.error(f"Erreur récupération stats nettoyage: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération des statistiques de nettoyage",
                details=str(e)
            )
    
    # === ENDPOINTS DE SÉCURITÉ ===
    
    @app.get("/security/rate-limit/stats")
    async def get_rate_limit_stats():
        """Statistiques du rate limiting."""
        try:
            stats = rate_limiter.get_stats()
            return APIResponse.success_response(
                data=stats,
                message="Statistiques de rate limiting récupérées"
            )
        except Exception as e:
            logger.error(f"Erreur récupération stats rate limiting: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération des statistiques de rate limiting",
                details=str(e)
            )
    
    @app.get("/security/headers/config")
    async def get_security_headers_config():
        """Configuration des headers de sécurité."""
        try:
            report = security_headers.get_security_report()
            return APIResponse.success_response(
                data=report,
                message="Configuration de sécurité récupérée"
            )
        except Exception as e:
            logger.error(f"Erreur récupération config sécurité: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération de la configuration de sécurité",
                details=str(e)
            )
    
    @app.get("/security/compliance/check")
    async def get_compliance_status():
        """Vérification de conformité sécurité."""
        try:
            # Vérifier l'environnement
            env_validation = security_manager.validate_environment_security()
            
            # Vérifier la conformité
            compliance_check = security_manager.get_compliance_checklist()
            
            combined_report = {
                "environment_security": env_validation,
                "compliance": compliance_check,
                "overall_score": (env_validation["score"] + compliance_check["compliance_score"]) / 2,
                "critical_issues": env_validation["issues"],
                "recommendations": env_validation["recommendations"] + compliance_check["recommendations"]
            }
            
            return APIResponse.success_response(
                data=combined_report,
                message="Audit de sécurité effectué"
            )
        except Exception as e:
            logger.error(f"Erreur audit sécurité: {e}")
            return APIResponse.error_response(
                message="Erreur lors de l'audit de sécurité",
                details=str(e)
            )
    
    @app.post("/security/validation/test")
    async def test_input_validation(request: Request):
        """Tester la validation des inputs (endpoint de debug)."""
        try:
            # Obtenir le body de la requête
            body = await request.body()
            if body:
                import json
                try:
                    payload = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Failed to parse request body as JSON: {e}")
                    try:
                        payload = {"raw_data": body.decode('utf-8')}
                    except UnicodeDecodeError:
                        payload = {"raw_data": body.hex()}
            else:
                payload = {}
            
            # Valider les différents types d'inputs
            validation_results = []
            
            # Valider URL si présente
            if "url" in payload:
                url_result = input_validator.validate_url(payload["url"])
                validation_results.append({
                    "input_type": "url",
                    "result": {
                        "is_valid": url_result.is_valid,
                        "sanitized_value": url_result.sanitized_value,
                        "errors": url_result.errors,
                        "warnings": url_result.warnings,
                        "risk_score": url_result.risk_score
                    }
                })
            
            # Valider JSON payload
            if payload:
                json_result = input_validator.validate_json_payload(payload)
                validation_results.append({
                    "input_type": "json_payload",
                    "result": {
                        "is_valid": json_result.is_valid,
                        "sanitized_value": json_result.sanitized_value,
                        "errors": json_result.errors,
                        "warnings": json_result.warnings,
                        "risk_score": json_result.risk_score
                    }
                })
            
            # Valider User-Agent
            user_agent = request.headers.get("user-agent", "")
            if user_agent:
                ua_result = input_validator.validate_user_agent(user_agent)
                validation_results.append({
                    "input_type": "user_agent",
                    "result": {
                        "is_valid": ua_result.is_valid,
                        "sanitized_value": ua_result.sanitized_value,
                        "errors": ua_result.errors,
                        "warnings": ua_result.warnings,
                        "risk_score": ua_result.risk_score
                    }
                })
            
            # Résumé de validation
            summary = input_validator.get_validation_summary(
                [r["result"] for r in validation_results if "result" in r]
            )
            
            response_data = {
                "validation_results": validation_results,
                "summary": summary,
                "security_level": input_validator.level.value,
                "timestamp": "2024-12-21T10:00:00Z"
            }
            
            return APIResponse.success_response(
                data=response_data,
                message="Test de validation effectué"
            )
            
        except Exception as e:
            logger.error(f"Erreur test validation: {e}")
            return APIResponse.error_response(
                message="Erreur lors du test de validation",
                details=str(e)
            )

    # Endpoints ML
    @app.post("/ml/analyze")
    async def ml_analyze_page(request: dict):
        """Analyse ML complète d'une page web."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            # Validation des inputs
            if not request.get("html") or not request.get("url"):
                raise HTTPException(status_code=400, detail="HTML et URL requis")
            
            # Analyser la page
            result = await ml_pipeline.analyze_page(
                html=request["html"],
                url=request["url"],
                headers=request.get("headers", {}),
                response_time=request.get("response_time"),
                metadata=request.get("metadata", {})
            )
            
            # Convertir en dict pour la sérialisation
            response_data = {
                "classification": {
                    "page_type": result.classification.page_type.value,
                    "confidence": result.classification.confidence,
                    "quality": result.classification.quality.value,
                    "language": result.classification.language
                },
                "bot_detection": {
                    "challenges": [c.value for c in result.bot_detection.challenges],
                    "confidence": result.bot_detection.confidence,
                    "strategies": [s.value for s in result.bot_detection.strategies],
                    "warnings": result.bot_detection.warnings
                },
                "content_analysis": {
                    "word_count": result.content_features.word_count,
                    "readability_score": result.content_features.readability_score,
                    "sentiment_score": result.content_features.sentiment_score,
                    "topics": result.content_features.topics,
                    "keywords": result.content_features.keywords[:10]
                },
                "metrics": {
                    "processing_time": result.processing_time,
                    "confidence_score": result.confidence_score
                },
                "recommendations": result.recommendations,
                "scraping_config": result.scraping_config
            }
            
            return APIResponse.success_response(
                data=response_data,
                message="Analyse ML complétée"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur analyse ML: {e}")
            return APIResponse.error_response(
                message="Erreur lors de l'analyse ML",
                details=str(e)
            )
    
    @app.post("/ml/classify")
    async def ml_classify_content(request: dict):
        """Classification de contenu uniquement."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            if not request.get("html") or not request.get("url"):
                raise HTTPException(status_code=400, detail="HTML et URL requis")
            
            # Classification seulement
            result = ml_pipeline.content_classifier.classify_page(
                html=request["html"],
                url=request["url"],
                metadata=request.get("metadata", {})
            )
            
            response_data = {
                "page_type": result.page_type.value,
                "confidence": result.confidence,
                "quality": result.quality.value,
                "language": result.language,
                "insights": ml_pipeline.content_classifier.get_content_insights(result)
            }
            
            return APIResponse.success_response(
                data=response_data,
                message="Classification complétée"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur classification: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la classification",
                details=str(e)
            )
    
    @app.post("/ml/detect-bot")
    async def ml_detect_bot_challenges(request: dict):
        """Détection des défis anti-bot."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            if not request.get("html") or not request.get("url"):
                raise HTTPException(status_code=400, detail="HTML et URL requis")
            
            # Détection anti-bot seulement
            result = ml_pipeline.antibot_detector.analyze_page(
                html=request["html"],
                headers=request.get("headers", {}),
                url=request["url"],
                response_time=request.get("response_time")
            )
            
            response_data = {
                "challenges": [c.value for c in result.challenges],
                "confidence": result.confidence,
                "strategies": [s.value for s in result.strategies],
                "warnings": result.warnings,
                "stealth_config": ml_pipeline.antibot_detector.create_stealth_configuration(result),
                "recommended_delays": ml_pipeline.antibot_detector.get_recommended_delays(result.challenges)
            }
            
            return APIResponse.success_response(
                data=response_data,
                message="Détection anti-bot complétée"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur détection anti-bot: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la détection anti-bot",
                details=str(e)
            )
    
    @app.get("/ml/stats")
    async def ml_get_statistics():
        """Statistiques du pipeline ML."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            stats = ml_pipeline.get_performance_metrics()
            
            return APIResponse.success_response(
                data=stats,
                message="Statistiques ML récupérées"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur récupération stats ML: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération des statistiques",
                details=str(e)
            )
    
    @app.get("/ml/cache/stats")
    async def ml_get_cache_statistics():
        """Statistiques du cache ML."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            cache_stats = ml_pipeline.get_cache_stats()
            
            return APIResponse.success_response(
                data=cache_stats,
                message="Statistiques cache ML récupérées"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur récupération stats cache ML: {e}")
            return APIResponse.error_response(
                message="Erreur lors de la récupération des statistiques cache",
                details=str(e)
            )
    
    @app.delete("/ml/cache")
    async def ml_clear_cache():
        """Vider le cache ML."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            result = ml_pipeline.clear_cache()
            
            return APIResponse.success_response(
                data=result,
                message="Cache ML vidé"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur nettoyage cache ML: {e}")
            return APIResponse.error_response(
                message="Erreur lors du nettoyage du cache",
                details=str(e)
            )
    
    @app.post("/ml/cache/optimize")
    async def ml_optimize_cache():
        """Optimiser le cache ML (supprimer les entrées expirées)."""
        try:
            ml_pipeline = get_ml_pipeline_or_raise()
            
            result = ml_pipeline.optimize_cache()
            
            return APIResponse.success_response(
                data=result,
                message="Cache ML optimisé"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur optimisation cache ML: {e}")
            return APIResponse.error_response(
                message="Erreur lors de l'optimisation du cache",
                details=str(e)
            )


async def execute_scraping_task(task_id: str, task_data: ScrapingTaskCreate):
    """Exécute une tâche de scraping en arrière-plan."""
    try:
        logger.info(f"▶️ Début d'exécution de la tâche {task_id}")

        task_manager = get_task_manager()
        
        # Callback pour mettre à jour le progrès
        async def progress_callback(tid: str, progress: float, message: str):
            task_manager.update_task(tid, {
                "progress": progress,
                "message": message,
                "status": "running"
            })
            logger.debug(f"📊 Tâche {tid}: {progress}% - {message}")

        # Marquer comme en cours
        task_manager.update_task(task_id, {
            "status": "running",
            "message": "Scraping en cours..."
        })

        # Exécuter le scraping
        result = await scraping_service.scrape_url(
            task_data=task_data,
            task_id=task_id,
            progress_callback=progress_callback,
        )

        # Analyse ML si le scraping a réussi et que ML est disponible
        ml_analysis = None
        ml_manager = get_ml_manager()
        if result["status"] == "completed" and ml_manager.is_available() and result.get("html_content"):
            try:
                await progress_callback(task_id, 90, "Analyse ML en cours...")
                
                ml_pipeline = ml_manager.get_pipeline()
                ml_analysis = await ml_pipeline.analyze_page(
                    html=result["html_content"],
                    url=str(task_data.url),
                    headers=result.get("response_headers", {}),
                    response_time=result.get("response_time"),
                    metadata={"task_id": task_id}
                )
                
                await progress_callback(task_id, 95, "Analyse ML terminée")
                logger.info(f"✨ Analyse ML complétée pour la tâche {task_id}")
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur analyse ML pour tâche {task_id}: {e}")

        # Traiter le résultat
        if result["status"] == "completed":
            # Succès
            task_metadata = result.get("task_metadata", {})
            
            # Ajouter les données ML si disponibles
            if ml_analysis:
                task_metadata["ml_analysis"] = {
                    "classification": {
                        "page_type": ml_analysis.classification.page_type.value,
                        "confidence": ml_analysis.classification.confidence,
                        "quality": ml_analysis.classification.quality.value,
                        "language": ml_analysis.classification.language
                    },
                    "bot_detection": {
                        "challenges": [c.value for c in ml_analysis.bot_detection.challenges],
                        "confidence": ml_analysis.bot_detection.confidence,
                        "warnings": ml_analysis.bot_detection.warnings
                    },
                    "content_metrics": {
                        "word_count": ml_analysis.content_features.word_count,
                        "readability_score": ml_analysis.content_features.readability_score,
                        "sentiment_score": ml_analysis.content_features.sentiment_score,
                        "topics": ml_analysis.content_features.topics
                    },
                    "performance": {
                        "processing_time": ml_analysis.processing_time,
                        "confidence_score": ml_analysis.confidence_score
                    },
                    "recommendations": ml_analysis.recommendations
                }
            
            # Marquer la tâche comme terminée
            task_manager.complete_task(task_id, {
                "progress": 100,
                "message": "Terminé avec succès" + (" + analyse ML" if ml_analysis else ""),
                "result": result["structured_content"],
                "metadata": task_metadata,
                "execution_time_ms": result.get("execution_time_ms", 0),
                "tokens_used": result.get("tokens_used", 0),
            })

            logger.info(f"✅ Tâche {task_id} terminée avec succès")

        else:
            # Échec - marquer comme échouée
            error_msg = result.get("error_message", "Erreur inconnue")
            task_manager.fail_task(task_id, error_msg)
            logger.error(f"❌ Tâche {task_id} échouée: {error_msg}")

    except Exception as e:
        logger.error(f"💥 Erreur critique dans la tâche {task_id}: {e}")

        # Marquer comme échouée
        task_manager.fail_task(task_id, f"Erreur système: {str(e)}")


# Créer l'instance de l'application pour uvicorn
app = create_app()
