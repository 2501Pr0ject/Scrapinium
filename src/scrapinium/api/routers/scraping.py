"""Router pour les endpoints de scraping."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...models.schemas import APIResponse, ScrapingTaskCreate, BatchScrapingRequest, BatchScrapingResponse
from ...utils.logging import get_logger
from ..task_manager import get_task_manager
from ..services.scraping_service import get_scraping_task_service
from ..services.batch_service import get_batch_service

logger = get_logger("scraping_router")

router = APIRouter(
    prefix="/scrape",
    tags=["scraping"]
)


@router.post("", response_model=APIResponse)
async def start_scraping(
    task_data: ScrapingTaskCreate, background_tasks: BackgroundTasks
):
    """Démarre une nouvelle tâche de scraping."""
    try:
        scraping_service = get_scraping_task_service()
        task_id = scraping_service.create_task(task_data)

        # Lancer la tâche en arrière-plan
        background_tasks.add_task(
            scraping_service.execute_task,
            task_id,
            task_data,
        )

        return APIResponse.success_response(
            data={"task_id": task_id, "status": "pending"},
            message="Tâche de scraping créée",
        )

    except Exception as e:
        logger.error(f"Erreur création tâche: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la création de la tâche"
        )


@router.get("/batch", name="list_batch_jobs")
async def list_batch_jobs(limit: int = 20):
    """Lister les lots de scraping."""
    try:
        batch_service = get_batch_service()
        batches = batch_service.list_batch_jobs(limit=limit)
        
        return APIResponse.success_response(
            data={
                "batches": [batch.model_dump() for batch in batches],
                "total": len(batches),
                "limit": limit
            },
            message="Liste des batches récupérée"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur listage batches: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors du listage des batches"
        )


@router.get("/{task_id}")
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

    raise HTTPException(
        status_code=404, detail=f"Tâche {task_id} non trouvée"
    )


@router.get("/{task_id}/result")
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
            "result": completed_task["result"],
            "metadata": completed_task.get("metadata", {}),
        },
        message="Résultat récupéré avec succès",
    )


@router.delete("/{task_id}")
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

    return APIResponse.success_response(
        data={"task_id": task_id, "status": "cancelled"},
        message="Tâche annulée avec succès",
    )


@router.get("", name="list_tasks")
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
            "limit": limit
        },
        message="Liste des tâches récupérée"
    )


# === BATCH PROCESSING ENDPOINTS ===

@router.post("/batch", response_model=APIResponse)
async def create_batch_scraping(batch_request: BatchScrapingRequest, background_tasks: BackgroundTasks):
    """Créer et démarrer un lot de scraping."""
    try:
        batch_service = get_batch_service()
        
        # Créer le batch job
        batch_response = batch_service.create_batch_job(batch_request)
        
        # Démarrer le traitement en arrière-plan
        background_tasks.add_task(
            batch_service.start_batch_job,
            batch_response.batch_id
        )
        
        logger.info(f"📦 Batch scraping créé: {batch_response.batch_id} avec {batch_response.total_urls} URLs")
        
        return APIResponse.success_response(
            data=batch_response.model_dump(),
            message=f"Batch scraping créé avec {batch_response.total_urls} URLs"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur création batch scraping: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la création du batch scraping"
        )


@router.get("/batch/{batch_id}", response_model=APIResponse)
async def get_batch_status(batch_id: str):
    """Récupérer le statut d'un batch de scraping."""
    try:
        batch_service = get_batch_service()
        batch_info = batch_service.get_batch_job(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Batch {batch_id} non trouvé"
            )
        
        return APIResponse.success_response(
            data=batch_info.model_dump(),
            message="Statut du batch récupéré"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération batch {batch_id}: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la récupération du batch"
        )




@router.delete("/batch/{batch_id}", response_model=APIResponse)
async def cancel_batch_job(batch_id: str):
    """Annuler un batch de scraping."""
    try:
        batch_service = get_batch_service()
        success = await batch_service.cancel_batch_job(batch_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} non trouvé ou impossible à annuler"
            )
        
        return APIResponse.success_response(
            data={"batch_id": batch_id, "status": "cancelled"},
            message="Batch annulé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur annulation batch {batch_id}: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de l'annulation du batch"
        )


