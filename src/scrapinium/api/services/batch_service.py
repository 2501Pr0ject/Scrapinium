"""Service de traitement par lots (batch processing)."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ...models.schemas import BatchScrapingRequest, BatchScrapingResponse, ScrapingTaskCreate
from ...utils.logging import get_logger
from .scraping_service import get_scraping_task_service

logger = get_logger("batch_service")


@dataclass
class BatchJob:
    """Représente un travail en lot."""
    
    batch_id: str
    batch_name: Optional[str]
    urls: List[str]
    config: dict
    task_ids: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed, cancelled
    progress: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    results: Dict[str, dict] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)


class BatchProcessingService:
    """Service de traitement par lots."""
    
    def __init__(self):
        self.batch_jobs: Dict[str, BatchJob] = {}
        self.active_batches: Dict[str, asyncio.Task] = {}
        
    def create_batch_job(self, request: BatchScrapingRequest) -> BatchScrapingResponse:
        """Créer un nouveau travail en lot."""
        try:
            batch_id = str(uuid.uuid4())
            
            # Créer le job batch
            batch_job = BatchJob(
                batch_id=batch_id,
                batch_name=request.batch_name or f"Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                urls=[str(url) for url in request.urls],
                config={
                    "output_format": request.output_format.value,
                    "llm_provider": request.llm_provider.value,
                    "llm_model": request.llm_model,
                    "parallel_limit": request.parallel_limit,
                    "delay_between_requests": request.delay_between_requests,
                    "user_id": request.user_id
                }
            )
            
            # Calculer les tâches initiales
            batch_job.pending_tasks = len(batch_job.urls)
            
            # Stocker le job
            self.batch_jobs[batch_id] = batch_job
            
            logger.info(f"🚀 Batch job créé: {batch_id} avec {len(batch_job.urls)} URLs")
            
            return self._create_response(batch_job)
            
        except Exception as e:
            logger.error(f"❌ Erreur création batch job: {e}")
            raise
    
    async def start_batch_job(self, batch_id: str) -> bool:
        """Démarrer l'exécution d'un travail en lot."""
        try:
            if batch_id not in self.batch_jobs:
                logger.error(f"❌ Batch job non trouvé: {batch_id}")
                return False
                
            batch_job = self.batch_jobs[batch_id]
            
            if batch_job.status != "pending":
                logger.warning(f"⚠️ Batch job {batch_id} déjà démarré ou terminé")
                return False
            
            # Marquer comme démarré
            batch_job.status = "running"
            batch_job.started_at = datetime.now()
            
            # Créer la tâche asyncio pour le traitement
            task = asyncio.create_task(self._process_batch(batch_job))
            self.active_batches[batch_id] = task
            
            logger.info(f"📈 Batch job démarré: {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage batch job {batch_id}: {e}")
            return False
    
    async def _process_batch(self, batch_job: BatchJob):
        """Traiter un lot de façon asynchrone."""
        try:
            scraping_service = get_scraping_task_service()
            semaphore = asyncio.Semaphore(batch_job.config["parallel_limit"])
            
            # Estimer le temps de completion
            estimated_time_per_url = 10  # 10 secondes par URL en moyenne
            total_estimated_time = len(batch_job.urls) * estimated_time_per_url / batch_job.config["parallel_limit"]
            batch_job.estimated_completion = batch_job.started_at + timedelta(seconds=total_estimated_time)
            
            async def process_single_url(url: str):
                """Traiter une URL unique."""
                async with semaphore:
                    try:
                        # Créer la tâche de scraping
                        task_data = ScrapingTaskCreate(
                            url=url,
                            output_format=batch_job.config["output_format"],
                            llm_provider=batch_job.config["llm_provider"],
                            llm_model=batch_job.config["llm_model"],
                            user_id=batch_job.config["user_id"]
                        )
                        
                        # Créer et exécuter la tâche
                        task_id = scraping_service.create_task(task_data)
                        batch_job.task_ids.append(task_id)
                        
                        # Mettre à jour les compteurs
                        batch_job.pending_tasks -= 1
                        batch_job.running_tasks += 1
                        self._update_progress(batch_job)
                        
                        # Attendre la completion (simulation pour l'instant)
                        await asyncio.sleep(batch_job.config["delay_between_requests"])
                        
                        # Exécuter la tâche
                        await scraping_service.execute_task(task_id, task_data)
                        
                        # Marquer comme terminé
                        batch_job.running_tasks -= 1
                        batch_job.completed_tasks += 1
                        batch_job.results[url] = {"task_id": task_id, "status": "completed"}
                        
                        logger.info(f"✅ URL traitée: {url} (tâche {task_id})")
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur traitement URL {url}: {e}")
                        batch_job.running_tasks -= 1
                        batch_job.failed_tasks += 1
                        batch_job.errors[url] = str(e)
                    
                    finally:
                        self._update_progress(batch_job)
            
            # Traiter toutes les URLs
            tasks = [process_single_url(url) for url in batch_job.urls]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Marquer le batch comme terminé
            batch_job.status = "completed" if batch_job.failed_tasks == 0 else "completed_with_errors"
            batch_job.completed_at = datetime.now()
            batch_job.progress = 100
            
            logger.info(f"🎉 Batch job terminé: {batch_job.batch_id} - {batch_job.completed_tasks}/{len(batch_job.urls)} succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur critique batch job {batch_job.batch_id}: {e}")
            batch_job.status = "failed"
            batch_job.completed_at = datetime.now()
        
        finally:
            # Nettoyer la tâche active
            if batch_job.batch_id in self.active_batches:
                del self.active_batches[batch_job.batch_id]
    
    def _update_progress(self, batch_job: BatchJob):
        """Mettre à jour la progression du batch."""
        total_processed = batch_job.completed_tasks + batch_job.failed_tasks
        if len(batch_job.urls) > 0:
            batch_job.progress = int((total_processed / len(batch_job.urls)) * 100)
    
    def get_batch_job(self, batch_id: str) -> Optional[BatchScrapingResponse]:
        """Récupérer un travail en lot."""
        if batch_id not in self.batch_jobs:
            return None
        
        batch_job = self.batch_jobs[batch_id]
        return self._create_response(batch_job)
    
    def list_batch_jobs(self, limit: int = 20) -> List[BatchScrapingResponse]:
        """Lister les travaux en lot."""
        jobs = list(self.batch_jobs.values())
        # Trier par date de création (plus récent en premier)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        return [self._create_response(job) for job in jobs[:limit]]
    
    async def cancel_batch_job(self, batch_id: str) -> bool:
        """Annuler un travail en lot."""
        try:
            if batch_id not in self.batch_jobs:
                return False
            
            batch_job = self.batch_jobs[batch_id]
            
            # Annuler la tâche si elle est active
            if batch_id in self.active_batches:
                task = self.active_batches[batch_id]
                task.cancel()
                del self.active_batches[batch_id]
            
            # Marquer comme annulé
            batch_job.status = "cancelled"
            batch_job.completed_at = datetime.now()
            
            logger.info(f"🛑 Batch job annulé: {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur annulation batch job {batch_id}: {e}")
            return False
    
    def _create_response(self, batch_job: BatchJob) -> BatchScrapingResponse:
        """Créer une réponse à partir d'un BatchJob."""
        return BatchScrapingResponse(
            batch_id=batch_job.batch_id,
            batch_name=batch_job.batch_name,
            total_urls=len(batch_job.urls),
            status=batch_job.status,
            progress=batch_job.progress,
            completed_tasks=batch_job.completed_tasks,
            failed_tasks=batch_job.failed_tasks,
            running_tasks=batch_job.running_tasks,
            pending_tasks=batch_job.pending_tasks,
            task_ids=batch_job.task_ids,
            created_at=batch_job.created_at,
            started_at=batch_job.started_at,
            completed_at=batch_job.completed_at,
            estimated_completion=batch_job.estimated_completion,
            results_summary={
                "total": len(batch_job.urls),
                "completed": batch_job.completed_tasks,
                "failed": batch_job.failed_tasks,
                "errors": batch_job.errors if batch_job.failed_tasks > 0 else None
            }
        )
    
    def cleanup_old_jobs(self, days: int = 7):
        """Nettoyer les anciens jobs (plus de N jours)."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for batch_id, job in self.batch_jobs.items():
            if job.created_at < cutoff_date and job.status in ["completed", "failed", "cancelled"]:
                to_remove.append(batch_id)
        
        for batch_id in to_remove:
            del self.batch_jobs[batch_id]
            logger.info(f"🧹 Ancien batch job supprimé: {batch_id}")
        
        if to_remove:
            logger.info(f"🧹 {len(to_remove)} anciens batch jobs nettoyés")


# Instance globale du service
_batch_service = None

def get_batch_service() -> BatchProcessingService:
    """Récupérer l'instance du service de batch processing."""
    global _batch_service
    if _batch_service is None:
        _batch_service = BatchProcessingService()
        logger.info("📦 Service de batch processing initialisé")
    return _batch_service