"""Router pour les endpoints de maintenance système."""

import gc
from fastapi import APIRouter
from ...models.schemas import APIResponse
from ...utils.logging import get_logger

logger = get_logger("maintenance_router")

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.post("/gc")
async def force_garbage_collection():
    """Force un garbage collection manuel."""
    try:
        # Récupérer les stats avant
        before_stats = {
            "objects_before": len(gc.get_objects()),
            "collections": gc.get_count(),
        }
        
        # Forcer le GC
        collected = gc.collect()
        
        # Stats après
        after_stats = {
            "objects_after": len(gc.get_objects()),
            "objects_collected": collected,
            "collections": gc.get_count(),
        }
        
        return APIResponse.success_response(
            data={
                "before": before_stats,
                "after": after_stats,
                "objects_freed": before_stats["objects_before"] - after_stats["objects_after"]
            },
            message=f"Garbage collection effectué - {collected} objets collectés"
        )
    except Exception as e:
        logger.error(f"Erreur lors du garbage collection: {e}")
        return APIResponse.error_response(
            message="Erreur lors du garbage collection",
            details=str(e)
        )


@router.post("/optimize")
async def optimize_memory():
    """Optimise l'utilisation mémoire du système."""
    try:
        from ...utils.memory import memory_monitor
        
        result = await memory_monitor.optimize_memory()
        
        return APIResponse.success_response(
            data=result,
            message="Optimisation mémoire effectuée"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation: {e}")
        return APIResponse.error_response(
            message="Erreur lors de l'optimisation mémoire",
            details=str(e)
        )


@router.post("/cleanup")
async def cleanup_resources():
    """Lance un nettoyage complet des ressources système."""
    try:
        from ...utils.cleanup import cleanup_manager
        
        result = await cleanup_manager.cleanup_all()
        
        return APIResponse.success_response(
            data=result,
            message="Nettoyage des ressources effectué"
        )
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
        return APIResponse.error_response(
            message="Erreur lors du nettoyage des ressources",
            details=str(e)
        )