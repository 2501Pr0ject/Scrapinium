"""Router pour les endpoints de scraping."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...models.schemas import APIResponse, ScrapingTaskCreate
from ...utils.logging import get_logger
from ..task_manager import get_task_manager
from ..services.scraping_service import get_scraping_task_service

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
            message="Erreur lors de la création de la tâche",
            details=str(e)
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


