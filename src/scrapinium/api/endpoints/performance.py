"""
Endpoints API pour la gestion des performances.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional

from ...performance import (
    performance_profiler,
    PerformanceOptimizer,
    BenchmarkSuite
)
from ...cache import get_cache_manager
from ...scraping.browser import get_browser_pool
from ...utils.memory import get_memory_monitor
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])

# Instance globale de l'optimiseur (sera initialisée à la première utilisation)
optimizer = None

async def get_optimizer():
    """Obtient l'instance de l'optimiseur (lazy loading)."""
    global optimizer
    if optimizer is None:
        cache_manager = await get_cache_manager()
        browser_pool = get_browser_pool()
        memory_monitor = get_memory_monitor()
        
        optimizer = PerformanceOptimizer(
            profiler=performance_profiler,
            cache_manager=cache_manager,
            browser_pool=browser_pool, 
            memory_monitor=memory_monitor
        )
    return optimizer

benchmark_suite = BenchmarkSuite(performance_profiler)


@router.get("/report")
async def get_performance_report() -> Dict[str, Any]:
    """
    Génère un rapport de performance détaillé.
    
    Returns:
        Rapport complet avec métriques et suggestions d'optimisation
    """
    try:
        detailed_report = performance_profiler.export_detailed_report()
        
        return {
            "success": True,
            "data": detailed_report,
            "message": "Rapport de performance généré avec succès"
        }
        
    except Exception as e:
        logger.error(f"Erreur génération rapport performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


@router.get("/metrics/live")
async def get_live_metrics() -> Dict[str, Any]:
    """
    Obtient les métriques de performance en temps réel.
    
    Returns:
        Métriques actuelles du système
    """
    try:
        # Obtenir l'instance de l'optimiseur
        opt = await get_optimizer()
        
        # Capture d'un snapshot de performance
        snapshot = await opt._capture_performance_snapshot()
        
        # Statistiques du profiler
        report = performance_profiler.get_performance_report()
        
        return {
            "success": True,
            "data": {
                "current_metrics": snapshot,
                "performance_summary": {
                    "total_operations": report.total_operations,
                    "average_duration_ms": report.average_duration_ms,
                    "p95_duration_ms": report.p95_duration_ms,
                    "p99_duration_ms": report.p99_duration_ms,
                    "active_bottlenecks": len(report.bottlenecks),
                    "optimization_suggestions": len(report.optimization_suggestions)
                },
                "system_health": {
                    "memory_usage_ok": snapshot.get("memory_usage_mb", 0) < 1024,
                    "cache_performance_ok": snapshot.get("cache_hit_rate", 0) > 0.7,
                    "response_time_ok": report.average_duration_ms < 3000
                }
            },
            "message": "Métriques en temps réel récupérées"
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération métriques live: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des métriques: {str(e)}"
        )


@router.post("/optimize")
async def run_optimization(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Lance une optimisation automatique des performances.
    
    Returns:
        Résultats de l'optimisation appliquée
    """
    try:
        logger.info("Démarrage de l'optimisation manuelle")
        
        # Obtenir l'instance de l'optimiseur
        opt = await get_optimizer()
        
        # Lancement de l'optimisation en arrière-plan
        optimization_results = await opt.analyze_and_optimize()
        
        return {
            "success": True,
            "data": optimization_results,
            "message": f"{len(optimization_results['applied_optimizations'])} optimisations appliquées"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pendant l'optimisation: {str(e)}"
        )


@router.get("/optimization/history")
async def get_optimization_history() -> Dict[str, Any]:
    """
    Retourne l'historique des optimisations appliquées.
    
    Returns:
        Historique complet des optimisations
    """
    try:
        opt = await get_optimizer()
        history = opt.get_optimization_history()
        
        # Statistiques de l'historique
        total_optimizations = len(history)
        import time
        recent_optimizations = [opt_item for opt_item in history if opt_item["timestamp"] > (time.time() - 86400)]
        
        return {
            "success": True,
            "data": {
                "history": history,
                "statistics": {
                    "total_optimizations": total_optimizations,
                    "recent_optimizations_24h": len(recent_optimizations),
                    "most_frequent_rules": self._get_most_frequent_rules(history),
                    "average_improvement": self._calculate_average_improvement(history)
                }
            },
            "message": f"{total_optimizations} optimisations dans l'historique"
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération historique: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )


@router.delete("/optimization/history")
async def clear_optimization_history() -> Dict[str, Any]:
    """
    Efface l'historique des optimisations.
    
    Returns:
        Confirmation de l'effacement
    """
    try:
        opt = await get_optimizer()
        opt.clear_optimization_history()
        
        return {
            "success": True,
            "data": {},
            "message": "Historique des optimisations effacé"
        }
        
    except Exception as e:
        logger.error(f"Erreur effacement historique: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'effacement: {str(e)}"
        )


@router.post("/benchmark/scraping")
async def run_scraping_benchmark(
    urls: List[str],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Lance un benchmark du système de scraping.
    
    Args:
        urls: Liste des URLs à utiliser pour le benchmark
        
    Returns:
        Résultats du benchmark de scraping
    """
    if len(urls) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 URLs autorisées pour le benchmark"
        )
    
    try:
        logger.info(f"Démarrage benchmark scraping avec {len(urls)} URLs")
        
        # Lancement du benchmark
        results = await benchmark_suite.run_scraping_benchmark(urls)
        
        return {
            "success": True,
            "data": results,
            "message": f"Benchmark terminé: {results['throughput_urls_per_second']:.2f} URLs/s"
        }
        
    except Exception as e:
        logger.error(f"Erreur benchmark scraping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pendant le benchmark: {str(e)}"
        )


@router.post("/benchmark/cache")
async def run_cache_benchmark(
    background_tasks: BackgroundTasks,
    operations: int = 1000
) -> Dict[str, Any]:
    """
    Lance un benchmark du système de cache.
    
    Args:
        operations: Nombre d'opérations à effectuer
        
    Returns:
        Résultats du benchmark de cache
    """
    if operations > 10000:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10,000 opérations autorisées pour le benchmark"
        )
    
    try:
        logger.info(f"Démarrage benchmark cache avec {operations} opérations")
        
        # Lancement du benchmark
        results = await benchmark_suite.run_cache_benchmark(operations)
        
        return {
            "success": True,
            "data": results,
            "message": f"Benchmark terminé: {results['operations_per_second']:.0f} ops/s"
        }
        
    except Exception as e:
        logger.error(f"Erreur benchmark cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur pendant le benchmark: {str(e)}"
        )


@router.post("/profiler/reset")
async def reset_profiler() -> Dict[str, Any]:
    """
    Remet à zéro les métriques du profiler.
    
    Returns:
        Confirmation de la remise à zéro
    """
    try:
        performance_profiler.reset_metrics()
        
        return {
            "success": True,
            "data": {},
            "message": "Métriques du profiler remises à zéro"
        }
        
    except Exception as e:
        logger.error(f"Erreur reset profiler: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la remise à zéro: {str(e)}"
        )


@router.get("/bottlenecks")
async def get_performance_bottlenecks() -> Dict[str, Any]:
    """
    Identifie les goulots d'étranglement actuels.
    
    Returns:
        Liste des goulots d'étranglement détectés
    """
    try:
        report = performance_profiler.get_performance_report()
        
        # Analyse avancée des goulots d'étranglement
        critical_bottlenecks = []
        warnings = []
        
        for bottleneck in report.bottlenecks:
            if "lent" in bottleneck.lower() or "moyenne" in bottleneck.lower():
                if any(word in bottleneck for word in ["5000", "10000", "15000"]):
                    critical_bottlenecks.append(bottleneck)
                else:
                    warnings.append(bottleneck)
        
        return {
            "success": True,
            "data": {
                "critical_bottlenecks": critical_bottlenecks,
                "warnings": warnings,
                "all_bottlenecks": report.bottlenecks,
                "memory_hotspots": report.memory_hotspots,
                "optimization_suggestions": report.optimization_suggestions,
                "performance_score": self._calculate_performance_score(report)
            },
            "message": f"{len(report.bottlenecks)} goulots d'étranglement détectés"
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse bottlenecks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )


def _get_most_frequent_rules(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calcule les règles d'optimisation les plus fréquentes."""
    
    rule_counts = {}
    for optimization in history:
        rule_name = optimization.get("rule", "unknown")
        rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
    
    # Tri par fréquence décroissante
    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [{"rule": rule, "count": count} for rule, count in sorted_rules[:5]]


def _calculate_average_improvement(history: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calcule l'amélioration moyenne des optimisations."""
    
    if not history:
        return {}
    
    total_improvements = {}
    improvement_counts = {}
    
    for optimization in history:
        improvement = optimization.get("improvement", {})
        for metric, value in improvement.items():
            if isinstance(value, (int, float)):
                total_improvements[metric] = total_improvements.get(metric, 0) + value
                improvement_counts[metric] = improvement_counts.get(metric, 0) + 1
    
    return {
        metric: total_improvements[metric] / improvement_counts[metric]
        for metric in total_improvements
        if improvement_counts[metric] > 0
    }


def _calculate_performance_score(report) -> float:
    """Calcule un score de performance global."""
    
    score = 100.0
    
    # Pénalités basées sur les problèmes détectés
    score -= len(report.bottlenecks) * 10  # -10 points par bottleneck
    score -= len(report.optimization_suggestions) * 5  # -5 points par suggestion
    
    # Pénalités basées sur les métriques
    if report.average_duration_ms > 3000:  # > 3s
        score -= 20
    elif report.average_duration_ms > 1000:  # > 1s
        score -= 10
    
    if report.p95_duration_ms > 10000:  # > 10s
        score -= 15
    
    return max(0, min(100, score))