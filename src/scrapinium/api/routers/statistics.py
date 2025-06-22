"""Router pour les endpoints de statistiques et monitoring."""

from fastapi import APIRouter
from ...models.schemas import APIResponse
from ...utils.logging import get_logger
from ..task_manager import get_task_manager
from ...scraping.browser import get_browser_stats

logger = get_logger("statistics_router")

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("")
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


@router.get("/browser")
async def get_browser_stats_detailed():
    """Statistiques détaillées du pool de navigateurs."""
    try:
        browser_stats = await get_browser_stats()
        
        return APIResponse.success_response(
            data=browser_stats,
            message="Statistiques navigateurs récupérées"
        )
    except Exception as e:
        logger.error(f"Erreur récupération stats navigateurs: {e}")
        return APIResponse.error_response(
            message="Erreur lors de la récupération des statistiques",
            details=str(e)
        )


@router.get("/cache")
async def get_cache_statistics():
    """Statistiques du cache multi-niveau."""
    try:
        from ...cache.manager import cache_manager
        
        # Récupérer les stats du cache
        cache_stats = {
            "memory_cache": await cache_manager.get_memory_stats(),
            "redis_cache": await cache_manager.get_redis_stats(),
            "hit_rate": await cache_manager.get_hit_rate(),
            "total_requests": await cache_manager.get_total_requests()
        }
        
        return APIResponse.success_response(
            data=cache_stats,
            message="Statistiques cache récupérées"
        )
    except Exception as e:
        logger.error(f"Erreur récupération stats cache: {e}")
        return APIResponse.error_response(
            message="Erreur lors de la récupération des statistiques cache",
            details=str(e)
        )


@router.get("/memory")
async def get_memory_statistics():
    """Statistiques détaillées de la mémoire."""
    try:
        from ...utils.memory import memory_monitor
        
        memory_stats = memory_monitor.get_detailed_stats()
        
        return APIResponse.success_response(
            data=memory_stats,
            message="Statistiques mémoire récupérées"
        )
    except Exception as e:
        logger.error(f"Erreur récupération stats mémoire: {e}")
        return APIResponse.error_response(
            message="Erreur lors de la récupération des statistiques mémoire",
            details=str(e)
        )


@router.get("/cleanup")
async def get_cleanup_statistics():
    """Statistiques du système de nettoyage automatique."""
    try:
        from ...utils.cleanup import cleanup_manager
        
        cleanup_stats = cleanup_manager.get_stats()
        
        return APIResponse.success_response(
            data=cleanup_stats,
            message="Statistiques nettoyage récupérées"
        )
    except Exception as e:
        logger.error(f"Erreur récupération stats nettoyage: {e}")
        return APIResponse.error_response(
            message="Erreur lors de la récupération des statistiques nettoyage",
            details=str(e)
        )