"""Service pour la logique métier du scraping."""

import uuid
from typing import Any, Dict, Callable, Awaitable

from ...models.schemas import ScrapingTaskCreate
from ...utils.logging import get_logger
from ...scraping.service import scraping_service
from ..task_manager import get_task_manager
from ..ml_manager import get_ml_manager

logger = get_logger("scraping_service")


class ScrapingTaskService:
    """Service de gestion des tâches de scraping."""
    
    def __init__(self):
        self.task_manager = get_task_manager()
        self.ml_manager = get_ml_manager()
    
    def create_task(self, task_data: ScrapingTaskCreate) -> str:
        """Crée une nouvelle tâche de scraping."""
        task_id = str(uuid.uuid4())

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

        self.task_manager.add_task(task_id, task_entry)
        return task_id
    
    async def execute_task(
        self, 
        task_id: str, 
        task_data: ScrapingTaskCreate,
        progress_callback: Callable[[str, float, str], Awaitable[None]] = None
    ) -> Dict[str, Any]:
        """Exécute une tâche de scraping."""
        try:
            logger.info(f"▶️ Début d'exécution de la tâche {task_id}")

            # Callback par défaut si non fourni
            if progress_callback is None:
                async def default_progress_callback(tid: str, progress: float, message: str):
                    self.task_manager.update_task(tid, {
                        "progress": progress,
                        "message": message,
                        "status": "running"
                    })
                    logger.debug(f"📊 Tâche {tid}: {progress}% - {message}")
                
                progress_callback = default_progress_callback

            # Marquer comme en cours
            self.task_manager.update_task(task_id, {
                "status": "running",
                "message": "Scraping en cours..."
            })

            # Exécuter le scraping
            result = await scraping_service.scrape_url(
                task_data=task_data,
                task_id=task_id,
                progress_callback=progress_callback,
            )

            # Traitement ML si disponible
            ml_analysis = await self._process_ml_analysis(
                task_id, result, task_data, progress_callback
            )

            # Finaliser la tâche
            if result["status"] == "completed":
                await self._complete_task(task_id, result, task_data, ml_analysis)
            else:
                error_msg = result.get("error_message", "Erreur inconnue")
                self.task_manager.fail_task(task_id, error_msg)
                logger.error(f"❌ Tâche {task_id} échouée: {error_msg}")

            return result

        except Exception as e:
            logger.error(f"💥 Erreur critique dans la tâche {task_id}: {e}")
            self.task_manager.fail_task(task_id, f"Erreur système: {str(e)}")
            raise
    
    async def _process_ml_analysis(
        self, 
        task_id: str, 
        result: Dict[str, Any], 
        task_data: ScrapingTaskCreate,
        progress_callback: Callable[[str, float, str], Awaitable[None]]
    ) -> Any:
        """Traite l'analyse ML si disponible."""
        ml_analysis = None
        
        if (result["status"] == "completed" and 
            self.ml_manager.is_available() and 
            result.get("html_content")):
            
            try:
                await progress_callback(task_id, 90, "Analyse ML en cours...")
                
                ml_pipeline = self.ml_manager.get_pipeline()
                ml_analysis = await ml_pipeline.analyze_page(
                    html=result["html_content"],
                    url=str(task_data.url),
                    headers=result.get("response_headers", {}),
                    response_time=result.get("response_time"),
                    metadata={"task_id": task_id}
                )
                
                await progress_callback(task_id, 95, "Analyse ML terminée")
                logger.info(f"✅ Analyse ML terminée pour la tâche {task_id}")
                
            except Exception as e:
                logger.error(f"❌ Erreur analyse ML pour {task_id}: {e}")
                # Ne pas faire échouer le scraping si ML échoue
        
        return ml_analysis
    
    async def _complete_task(
        self, 
        task_id: str, 
        result: Dict[str, Any], 
        task_data: ScrapingTaskCreate, 
        ml_analysis: Any
    ):
        """Finalise une tâche de scraping réussie."""
        task_metadata = {
            "url": str(task_data.url),
            "output_format": task_data.output_format,
            "word_count": result.get("word_count", 0),
            "reading_time": result.get("reading_time", 0),
        }
        
        # Ajouter métadonnées ML si disponibles
        if ml_analysis:
            task_metadata["ml_analysis"] = {
                "content_type": ml_analysis.classification.content_type,
                "quality": ml_analysis.classification.quality_score,
                "language": ml_analysis.classification.language,
                "bot_challenges": len(ml_analysis.bot_detection.challenges),
                "sentiment_score": ml_analysis.content_features.sentiment_score,
            }
        
        # Marquer la tâche comme terminée
        self.task_manager.complete_task(task_id, {
            "progress": 100,
            "message": "Terminé avec succès" + (" + analyse ML" if ml_analysis else ""),
            "result": result["structured_content"],
            "metadata": task_metadata,
            "execution_time_ms": result.get("execution_time_ms", 0),
            "tokens_used": result.get("tokens_used", 0),
        })

        logger.info(f"✅ Tâche {task_id} terminée avec succès")


# Instance singleton
_scraping_task_service = None

def get_scraping_task_service() -> ScrapingTaskService:
    """Récupère l'instance du service de tâches de scraping."""
    global _scraping_task_service
    if _scraping_task_service is None:
        _scraping_task_service = ScrapingTaskService()
    return _scraping_task_service