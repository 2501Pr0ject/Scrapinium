"""Router pour la gestion du cache."""

from fastapi import APIRouter
from ...models.schemas import APIResponse
from ...utils.logging import get_logger

logger = get_logger("cache_router")

router = APIRouter(prefix="/cache", tags=["Cache"])


@router.delete("")
async def clear_cache():
    """Vide complètement le cache multi-niveau."""
    try:
        from ...cache.manager import cache_manager
        
        result = await cache_manager.clear_all()
        
        return APIResponse.success_response(
            data={
                "cleared_entries": result.get("cleared_entries", 0),
                "memory_freed_mb": result.get("memory_freed_mb", 0),
                "timestamp": result.get("timestamp")
            },
            message="Cache vidé avec succès"
        )
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du cache: {e}")
        return APIResponse.error_response(
            message="Erreur lors du nettoyage du cache",
            details=str(e)
        )


@router.delete("/{key}")
async def delete_cache_entry(key: str):
    """Supprime une entrée spécifique du cache."""
    try:
        from ...cache.manager import cache_manager
        
        result = await cache_manager.delete(key)
        
        if result:
            return APIResponse.success_response(
                data={"key": key, "deleted": True},
                message=f"Entrée '{key}' supprimée du cache"
            )
        else:
            return APIResponse.success_response(
                data={"key": key, "deleted": False},
                message=f"Entrée '{key}' non trouvée dans le cache"
            )
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'entrée {key}: {e}")
        return APIResponse.error_response(
            message=f"Erreur lors de la suppression de l'entrée '{key}'",
            details=str(e)
        )