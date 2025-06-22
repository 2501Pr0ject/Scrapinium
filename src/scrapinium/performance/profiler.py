"""
Profiler de performance avancé pour Scrapinium.
Analyse les goulots d'étranglement et propose des optimisations.
"""

import asyncio
import cProfile
import io
import pstats
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict
import psutil
import gc
from weakref import WeakSet

from ..utils.logging import get_logger
from ..utils.memory import MemoryMonitor

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Métriques de performance d'une opération."""
    
    operation_name: str
    duration_ms: float
    memory_usage_mb: float
    memory_peak_mb: float
    cpu_usage_percent: float
    objects_created: int
    objects_deleted: int
    cache_hits: int = 0
    cache_misses: int = 0
    db_queries: int = 0
    http_requests: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfilingReport:
    """Rapport de profiling complet."""
    
    total_operations: int
    total_duration_ms: float
    average_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    slowest_operations: List[PerformanceMetrics]
    memory_hotspots: List[str]
    optimization_suggestions: List[str]
    bottlenecks: List[str]


class AdvancedProfiler:
    """Profiler de performance avancé avec analyse intelligente."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.active_profiles: WeakSet = WeakSet()
        self.memory_monitor = MemoryMonitor()
        self.call_counts = defaultdict(int)
        self.duration_stats = defaultdict(list)
        
    def profile(self, operation_name: str = None):
        """Décorateur pour profiler une fonction."""
        def decorator(func: Callable):
            nonlocal operation_name
            if operation_name is None:
                operation_name = f"{func.__module__}.{func.__name__}"
                
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self.profile_context(operation_name):
                    return await func(*args, **kwargs)
                    
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.profile_context(operation_name):
                    return func(*args, **kwargs)
                    
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    @contextmanager
    def profile_context(self, operation_name: str):
        """Context manager pour profiler un bloc de code."""
        
        # Préparation du profiling
        start_time = time.perf_counter()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        initial_cpu = process.cpu_percent()
        
        # Démarrage du tracing mémoire
        tracemalloc.start()
        
        # Comptage des objets
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        try:
            yield
            
        finally:
            # Calcul des métriques finales
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Métriques mémoire
            final_memory = process.memory_info().rss / 1024 / 1024
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Métriques CPU
            final_cpu = process.cpu_percent()
            avg_cpu = (initial_cpu + final_cpu) / 2
            
            # Comptage des objets
            gc.collect()
            final_objects = len(gc.get_objects())
            objects_created = max(0, final_objects - initial_objects)
            
            # Création des métriques
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                duration_ms=duration_ms,
                memory_usage_mb=final_memory,
                memory_peak_mb=peak / 1024 / 1024,
                cpu_usage_percent=avg_cpu,
                objects_created=objects_created,
                objects_deleted=max(0, initial_objects - final_objects)
            )
            
            # Enregistrement
            self.metrics.append(metrics)
            self.call_counts[operation_name] += 1
            self.duration_stats[operation_name].append(duration_ms)
            
            logger.debug(f"Profiled {operation_name}: {duration_ms:.2f}ms, "
                        f"{final_memory:.1f}MB memory")
    
    def get_performance_report(self) -> ProfilingReport:
        """Génère un rapport de performance complet."""
        
        if not self.metrics:
            return ProfilingReport(
                total_operations=0,
                total_duration_ms=0,
                average_duration_ms=0,
                p95_duration_ms=0,
                p99_duration_ms=0,
                slowest_operations=[],
                memory_hotspots=[],
                optimization_suggestions=[],
                bottlenecks=[]
            )
        
        # Calculs statistiques
        all_durations = [m.duration_ms for m in self.metrics]
        total_duration = sum(all_durations)
        avg_duration = total_duration / len(all_durations)
        
        sorted_durations = sorted(all_durations)
        p95_duration = sorted_durations[int(len(sorted_durations) * 0.95)]
        p99_duration = sorted_durations[int(len(sorted_durations) * 0.99)]
        
        # Opérations les plus lentes
        slowest_ops = sorted(self.metrics, key=lambda x: x.duration_ms, reverse=True)[:10]
        
        # Analyse des hotspots mémoire
        memory_hotspots = self._analyze_memory_hotspots()
        
        # Suggestions d'optimisation
        suggestions = self._generate_optimization_suggestions()
        
        # Détection des goulots d'étranglement
        bottlenecks = self._detect_bottlenecks()
        
        return ProfilingReport(
            total_operations=len(self.metrics),
            total_duration_ms=total_duration,
            average_duration_ms=avg_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            slowest_operations=slowest_ops,
            memory_hotspots=memory_hotspots,
            optimization_suggestions=suggestions,
            bottlenecks=bottlenecks
        )
    
    def _analyze_memory_hotspots(self) -> List[str]:
        """Analyse les hotspots mémoire."""
        
        hotspots = []
        
        # Opérations avec forte consommation mémoire
        high_memory_ops = [
            m for m in self.metrics 
            if m.memory_peak_mb > 100  # Plus de 100MB
        ]
        
        if high_memory_ops:
            hotspots.append(f"{len(high_memory_ops)} opérations avec forte consommation mémoire")
        
        # Opérations avec beaucoup d'objets créés
        high_object_ops = [
            m for m in self.metrics 
            if m.objects_created > 10000
        ]
        
        if high_object_ops:
            hotspots.append(f"{len(high_object_ops)} opérations créant beaucoup d'objets")
        
        return hotspots
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """Génère des suggestions d'optimisation intelligentes."""
        
        suggestions = []
        
        # Analyse des durées
        slow_operations = [m for m in self.metrics if m.duration_ms > 5000]  # > 5s
        if slow_operations:
            suggestions.append(f"Optimiser les {len(slow_operations)} opérations lentes (>5s)")
        
        # Analyse mémoire
        memory_intensive = [m for m in self.metrics if m.memory_peak_mb > 50]
        if memory_intensive:
            suggestions.append(f"Réduire la consommation mémoire de {len(memory_intensive)} opérations")
        
        # Analyse des objets
        object_intensive = [m for m in self.metrics if m.objects_created > 5000]
        if object_intensive:
            suggestions.append("Implémenter object pooling pour réduire les allocations")
        
        # Analyse du cache
        cache_metrics = [m for m in self.metrics if m.cache_hits + m.cache_misses > 0]
        if cache_metrics:
            total_hits = sum(m.cache_hits for m in cache_metrics)
            total_requests = sum(m.cache_hits + m.cache_misses for m in cache_metrics)
            hit_rate = total_hits / total_requests if total_requests > 0 else 0
            
            if hit_rate < 0.8:
                suggestions.append(f"Améliorer le taux de cache ({hit_rate:.1%} actuel)")
        
        # Analyse des requêtes DB
        db_intensive = [m for m in self.metrics if m.db_queries > 10]
        if db_intensive:
            suggestions.append("Réduire le nombre de requêtes DB avec du batching")
        
        return suggestions
    
    def _detect_bottlenecks(self) -> List[str]:
        """Détecte les goulots d'étranglement."""
        
        bottlenecks = []
        
        # Analyse des opérations fréquentes et lentes
        for operation, durations in self.duration_stats.items():
            if len(durations) > 10:  # Opération fréquente
                avg_duration = sum(durations) / len(durations)
                if avg_duration > 1000:  # Moyenne > 1s
                    bottlenecks.append(f"{operation}: appelé {len(durations)}x, "
                                     f"moyenne {avg_duration:.0f}ms")
        
        # Détection des patterns
        scraping_ops = [m for m in self.metrics if 'scrape' in m.operation_name.lower()]
        if scraping_ops:
            avg_scraping_time = sum(m.duration_ms for m in scraping_ops) / len(scraping_ops)
            if avg_scraping_time > 3000:  # > 3s en moyenne
                bottlenecks.append(f"Scraping lent: {avg_scraping_time:.0f}ms en moyenne")
        
        return bottlenecks
    
    def reset_metrics(self):
        """Remet à zéro les métriques collectées."""
        self.metrics.clear()
        self.call_counts.clear()
        self.duration_stats.clear()
        logger.info("Métriques de performance remises à zéro")
    
    def export_detailed_report(self) -> Dict[str, Any]:
        """Exporte un rapport détaillé au format JSON."""
        
        report = self.get_performance_report()
        
        return {
            "summary": {
                "total_operations": report.total_operations,
                "total_duration_ms": report.total_duration_ms,
                "average_duration_ms": report.average_duration_ms,
                "p95_duration_ms": report.p95_duration_ms,
                "p99_duration_ms": report.p99_duration_ms
            },
            "slowest_operations": [
                {
                    "name": op.operation_name,
                    "duration_ms": op.duration_ms,
                    "memory_peak_mb": op.memory_peak_mb,
                    "objects_created": op.objects_created
                }
                for op in report.slowest_operations
            ],
            "call_frequency": dict(self.call_counts),
            "duration_percentiles": {
                operation: {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "p50": sorted(durations)[len(durations) // 2],
                    "p95": sorted(durations)[int(len(durations) * 0.95)],
                    "p99": sorted(durations)[int(len(durations) * 0.99)]
                }
                for operation, durations in self.duration_stats.items()
                if len(durations) > 0
            },
            "memory_hotspots": report.memory_hotspots,
            "optimization_suggestions": report.optimization_suggestions,
            "bottlenecks": report.bottlenecks
        }


class BenchmarkSuite:
    """Suite de benchmarks pour tester les performances."""
    
    def __init__(self, profiler: AdvancedProfiler):
        self.profiler = profiler
        
    async def run_scraping_benchmark(self, urls: List[str]) -> Dict[str, Any]:
        """Benchmark du système de scraping."""
        
        logger.info(f"Démarrage benchmark scraping avec {len(urls)} URLs")
        
        results = {
            "total_urls": len(urls),
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "total_time_ms": 0,
            "average_time_per_url_ms": 0,
            "throughput_urls_per_second": 0
        }
        
        start_time = time.perf_counter()
        
        # Simulation du scraping (à remplacer par le vrai service)
        for url in urls:
            try:
                with self.profiler.profile_context(f"benchmark_scrape_{url}"):
                    # Simuler le scraping
                    await asyncio.sleep(0.1)  # Remplacer par await scraping_service.scrape(url)
                    results["successful_scrapes"] += 1
            except Exception as e:
                logger.error(f"Erreur scraping {url}: {e}")
                results["failed_scrapes"] += 1
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        results["total_time_ms"] = total_time_ms
        results["average_time_per_url_ms"] = total_time_ms / len(urls)
        results["throughput_urls_per_second"] = len(urls) / (total_time_ms / 1000)
        
        logger.info(f"Benchmark terminé: {results['throughput_urls_per_second']:.2f} URLs/s")
        
        return results
    
    async def run_cache_benchmark(self, operations: int = 1000) -> Dict[str, Any]:
        """Benchmark du système de cache."""
        
        logger.info(f"Démarrage benchmark cache avec {operations} opérations")
        
        results = {
            "total_operations": operations,
            "cache_hits": 0,
            "cache_misses": 0,
            "set_operations": 0,
            "get_operations": 0,
            "total_time_ms": 0,
            "operations_per_second": 0
        }
        
        start_time = time.perf_counter()
        
        # Simulation des opérations de cache
        for i in range(operations):
            with self.profiler.profile_context(f"benchmark_cache_op_{i}"):
                if i % 3 == 0:  # SET
                    # Simuler cache.set()
                    await asyncio.sleep(0.001)
                    results["set_operations"] += 1
                else:  # GET
                    # Simuler cache.get()
                    await asyncio.sleep(0.0005)
                    results["get_operations"] += 1
                    
                    # Simuler hit/miss
                    if i % 4 == 0:
                        results["cache_hits"] += 1
                    else:
                        results["cache_misses"] += 1
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        results["total_time_ms"] = total_time_ms
        results["operations_per_second"] = operations / (total_time_ms / 1000)
        
        logger.info(f"Benchmark cache terminé: {results['operations_per_second']:.0f} ops/s")
        
        return results


# Instance globale du profiler
performance_profiler = AdvancedProfiler()

# Décorateurs de convenance
profile = performance_profiler.profile
profile_context = performance_profiler.profile_context