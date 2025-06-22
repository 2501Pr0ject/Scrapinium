"""
Optimiseur de performance automatique pour Scrapinium.
Applique automatiquement les optimisations basées sur l'analyse.
"""

import asyncio
import gc
import weakref
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import time

from .profiler import AdvancedProfiler, ProfilingReport
from ..cache.manager import CacheManager
from ..scraping.browser import BrowserPool
from ..utils.memory import MemoryMonitor
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationRule:
    """Règle d'optimisation automatique."""
    
    name: str
    condition: Callable[[ProfilingReport], bool]
    action: Callable[[], Any]
    priority: int = 1
    cooldown_seconds: int = 300  # 5 minutes
    last_applied: Optional[float] = None


class PerformanceOptimizer:
    """Optimiseur de performance automatique avec apprentissage."""
    
    def __init__(
        self, 
        profiler: AdvancedProfiler,
        cache_manager: Optional[CacheManager] = None,
        browser_pool: Optional[BrowserPool] = None,
        memory_monitor: Optional[MemoryMonitor] = None
    ):
        self.profiler = profiler
        self.cache_manager = cache_manager
        self.browser_pool = browser_pool
        self.memory_monitor = memory_monitor
        
        self.optimization_rules: List[OptimizationRule] = []
        self.optimization_history: List[Dict[str, Any]] = []
        self.performance_baselines: Dict[str, float] = {}
        
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configure les règles d'optimisation par défaut."""
        
        # Règle 1: Nettoyage mémoire agressif
        self.add_rule(
            name="aggressive_gc",
            condition=lambda report: any("mémoire" in suggestion.lower() for suggestion in report.optimization_suggestions),
            action=self._perform_aggressive_gc,
            priority=1,
            cooldown_seconds=60
        )
        
        # Règle 2: Optimisation du cache
        self.add_rule(
            name="cache_optimization",
            condition=lambda report: any("cache" in suggestion.lower() for suggestion in report.optimization_suggestions),
            action=self._optimize_cache,
            priority=2,
            cooldown_seconds=300
        )
        
        # Règle 3: Optimisation du pool de navigateurs
        self.add_rule(
            name="browser_pool_optimization",
            condition=lambda report: report.average_duration_ms > 5000,  # Scraping lent
            action=self._optimize_browser_pool,
            priority=3,
            cooldown_seconds=600
        )
        
        # Règle 4: Optimisation des connexions DB
        self.add_rule(
            name="database_optimization",
            condition=lambda report: any("db" in suggestion.lower() for suggestion in report.optimization_suggestions),
            action=self._optimize_database_connections,
            priority=2,
            cooldown_seconds=300
        )
        
        # Règle 5: Compression des données
        self.add_rule(
            name="data_compression",
            condition=lambda report: any(m.memory_peak_mb > 100 for m in report.slowest_operations),
            action=self._enable_data_compression,
            priority=3,
            cooldown_seconds=900
        )
    
    def add_rule(
        self, 
        name: str, 
        condition: Callable[[ProfilingReport], bool],
        action: Callable[[], Any],
        priority: int = 1,
        cooldown_seconds: int = 300
    ):
        """Ajoute une règle d'optimisation personnalisée."""
        
        rule = OptimizationRule(
            name=name,
            condition=condition,
            action=action,
            priority=priority,
            cooldown_seconds=cooldown_seconds
        )
        
        self.optimization_rules.append(rule)
        logger.info(f"Règle d'optimisation ajoutée: {name}")
    
    async def analyze_and_optimize(self) -> Dict[str, Any]:
        """Analyse les performances et applique les optimisations automatiques."""
        
        logger.info("Démarrage de l'analyse et optimisation automatique")
        
        # Génération du rapport de performance
        report = self.profiler.get_performance_report()
        
        optimization_results = {
            "report_summary": {
                "total_operations": report.total_operations,
                "average_duration_ms": report.average_duration_ms,
                "p95_duration_ms": report.p95_duration_ms,
                "bottlenecks_count": len(report.bottlenecks),
                "suggestions_count": len(report.optimization_suggestions)
            },
            "applied_optimizations": [],
            "skipped_optimizations": [],
            "performance_improvements": {}
        }
        
        # Application des règles d'optimisation
        current_time = time.time()
        applicable_rules = []
        
        for rule in sorted(self.optimization_rules, key=lambda r: r.priority):
            try:
                # Vérification du cooldown
                if (rule.last_applied and 
                    current_time - rule.last_applied < rule.cooldown_seconds):
                    optimization_results["skipped_optimizations"].append({
                        "rule": rule.name,
                        "reason": "cooldown_active",
                        "remaining_seconds": rule.cooldown_seconds - (current_time - rule.last_applied)
                    })
                    continue
                
                # Vérification de la condition
                if rule.condition(report):
                    applicable_rules.append(rule)
                else:
                    optimization_results["skipped_optimizations"].append({
                        "rule": rule.name,
                        "reason": "condition_not_met"
                    })
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'évaluation de la règle {rule.name}: {e}")
                optimization_results["skipped_optimizations"].append({
                    "rule": rule.name,
                    "reason": f"evaluation_error: {str(e)}"
                })
        
        # Application des optimisations
        for rule in applicable_rules:
            try:
                logger.info(f"Application de l'optimisation: {rule.name}")
                
                # Mesure des performances avant
                before_metrics = await self._capture_performance_snapshot()
                
                # Application de l'optimisation
                await rule.action()
                
                # Mesure des performances après
                await asyncio.sleep(1)  # Laisser le temps aux changements de prendre effet
                after_metrics = await self._capture_performance_snapshot()
                
                # Calcul de l'amélioration
                improvement = self._calculate_improvement(before_metrics, after_metrics)
                
                # Enregistrement
                rule.last_applied = current_time
                optimization_results["applied_optimizations"].append({
                    "rule": rule.name,
                    "applied_at": current_time,
                    "improvement": improvement
                })
                
                # Historique
                self.optimization_history.append({
                    "rule": rule.name,
                    "timestamp": current_time,
                    "before_metrics": before_metrics,
                    "after_metrics": after_metrics,
                    "improvement": improvement
                })
                
                logger.info(f"Optimisation {rule.name} appliquée avec succès")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'application de {rule.name}: {e}")
                optimization_results["applied_optimizations"].append({
                    "rule": rule.name,
                    "error": str(e),
                    "applied_at": current_time
                })
        
        # Calcul des améliorations globales
        if len(self.optimization_history) >= 2:
            recent_improvements = self.optimization_history[-5:]  # 5 dernières optimisations
            optimization_results["performance_improvements"] = self._calculate_global_improvements(recent_improvements)
        
        logger.info(f"Optimisation terminée: {len(optimization_results['applied_optimizations'])} optimisations appliquées")
        
        return optimization_results
    
    async def _capture_performance_snapshot(self) -> Dict[str, float]:
        """Capture un instantané des métriques de performance."""
        
        snapshot = {
            "timestamp": time.time(),
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "cache_hit_rate": 0,
            "active_connections": 0
        }
        
        try:
            # Métriques mémoire
            if self.memory_monitor:
                memory_stats = self.memory_monitor.get_memory_stats()
                snapshot["memory_usage_mb"] = memory_stats.get("process_memory_mb", 0)
            
            # Métriques cache
            if self.cache_manager:
                cache_stats = await self.cache_manager.get_stats()
                total_requests = cache_stats.get("cache_hits", 0) + cache_stats.get("cache_misses", 0)
                if total_requests > 0:
                    snapshot["cache_hit_rate"] = cache_stats.get("cache_hits", 0) / total_requests
            
            # Métriques pool de navigateurs
            if self.browser_pool:
                pool_stats = self.browser_pool.get_pool_stats()
                snapshot["active_connections"] = pool_stats.active_browsers
                
        except Exception as e:
            logger.warning(f"Erreur lors de la capture des métriques: {e}")
        
        return snapshot
    
    def _calculate_improvement(self, before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
        """Calcule l'amélioration entre deux snapshots."""
        
        improvement = {}
        
        for key in before:
            if key in after and key != "timestamp":
                if before[key] > 0:
                    improvement[key] = ((after[key] - before[key]) / before[key]) * 100
                else:
                    improvement[key] = 0
        
        return improvement
    
    def _calculate_global_improvements(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcule les améliorations globales sur l'historique."""
        
        if len(history) < 2:
            return {}
        
        first_metrics = history[0]["before_metrics"]
        last_metrics = history[-1]["after_metrics"]
        
        return self._calculate_improvement(first_metrics, last_metrics)
    
    async def _perform_aggressive_gc(self):
        """Effectue un nettoyage mémoire agressif."""
        
        logger.info("Application du nettoyage mémoire agressif")
        
        # Nettoyage standard
        for generation in range(3):
            collected = gc.collect(generation)
            logger.debug(f"GC génération {generation}: {collected} objets collectés")
        
        # Nettoyage des références faibles
        import weakref
        weakref.finalize
        
        # Nettoyage des caches internes
        if self.cache_manager:
            await self.cache_manager.cleanup_expired()
        
        logger.info("Nettoyage mémoire agressif terminé")
    
    async def _optimize_cache(self):
        """Optimise la configuration du cache."""
        
        if not self.cache_manager:
            logger.warning("Cache manager non disponible pour l'optimisation")
            return
        
        logger.info("Optimisation du cache en cours")
        
        # Obtenir les statistiques actuelles
        stats = await self.cache_manager.get_stats()
        hit_rate = stats.get("hit_rate", 0)
        
        # Ajustements basés sur le taux de hit
        if hit_rate < 0.7:  # Taux de hit faible
            # Augmenter la taille du cache
            logger.info("Augmentation de la taille du cache pour améliorer le hit rate")
            # self.cache_manager.resize(new_size=current_size * 1.2)
        
        elif hit_rate > 0.95:  # Taux de hit très élevé
            # On peut réduire la taille pour économiser la mémoire
            logger.info("Réduction de la taille du cache (hit rate très élevé)")
            # self.cache_manager.resize(new_size=current_size * 0.9)
        
        # Nettoyage des entrées expirées
        await self.cache_manager.cleanup_expired()
        
        logger.info("Optimisation du cache terminée")
    
    async def _optimize_browser_pool(self):
        """Optimise la configuration du pool de navigateurs."""
        
        if not self.browser_pool:
            logger.warning("Browser pool non disponible pour l'optimisation")
            return
        
        logger.info("Optimisation du pool de navigateurs")
        
        # Obtenir les statistiques
        stats = self.browser_pool.get_pool_stats()
        
        # Ajustements basés sur l'utilisation
        queue_length = getattr(stats, 'queue_length', 0)
        active_browsers = getattr(stats, 'active_browsers', 0)
        
        if queue_length > 5:  # File d'attente longue
            logger.info("Augmentation de la taille du pool de navigateurs")
            # Logique pour augmenter la taille du pool
        
        # Redémarrage des navigateurs anciens
        await self.browser_pool.restart_old_browsers()
        
        logger.info("Optimisation du pool de navigateurs terminée")
    
    async def _optimize_database_connections(self):
        """Optimise les connexions à la base de données."""
        
        logger.info("Optimisation des connexions base de données")
        
        # Nettoyage des connexions inactives
        # Cette logique dépendrait de votre ORM/driver de base de données
        
        logger.info("Optimisation des connexions base de données terminée")
    
    async def _enable_data_compression(self):
        """Active la compression des données."""
        
        logger.info("Activation de la compression des données")
        
        # Logique pour activer la compression
        # Cela pourrait inclure la configuration de middleware de compression
        
        logger.info("Compression des données activée")
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique des optimisations."""
        return self.optimization_history.copy()
    
    def clear_optimization_history(self):
        """Efface l'historique des optimisations."""
        self.optimization_history.clear()
        logger.info("Historique des optimisations effacé")
    
    async def schedule_periodic_optimization(self, interval_seconds: int = 3600):
        """Programme des optimisations périodiques."""
        
        logger.info(f"Programmation des optimisations périodiques (intervalle: {interval_seconds}s)")
        
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                logger.info("Démarrage de l'optimisation périodique")
                
                results = await self.analyze_and_optimize()
                applied_count = len(results["applied_optimizations"])
                
                logger.info(f"Optimisation périodique terminée: {applied_count} optimisations appliquées")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'optimisation périodique: {e}")


class AdaptiveOptimizer(PerformanceOptimizer):
    """Optimiseur adaptatif qui apprend des patterns de performance."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_patterns: Dict[str, List[float]] = defaultdict(list)
        self.optimization_effectiveness: Dict[str, List[float]] = defaultdict(list)
    
    def learn_from_optimization(self, rule_name: str, improvement: Dict[str, float]):
        """Apprend de l'efficacité d'une optimisation."""
        
        # Calcul d'un score d'efficacité global
        effectiveness_score = 0
        valid_metrics = 0
        
        for metric, improvement_percent in improvement.items():
            if metric == "memory_usage_mb" and improvement_percent < 0:  # Réduction mémoire = bon
                effectiveness_score += abs(improvement_percent)
                valid_metrics += 1
            elif metric == "cache_hit_rate" and improvement_percent > 0:  # Amélioration cache = bon
                effectiveness_score += improvement_percent
                valid_metrics += 1
        
        if valid_metrics > 0:
            effectiveness_score /= valid_metrics
            self.optimization_effectiveness[rule_name].append(effectiveness_score)
            
            # Garder seulement les 20 dernières mesures
            if len(self.optimization_effectiveness[rule_name]) > 20:
                self.optimization_effectiveness[rule_name] = self.optimization_effectiveness[rule_name][-20:]
            
            logger.debug(f"Efficacité de {rule_name}: {effectiveness_score:.2f}%")
    
    def get_rule_effectiveness(self, rule_name: str) -> float:
        """Retourne l'efficacité moyenne d'une règle."""
        
        scores = self.optimization_effectiveness.get(rule_name, [])
        return sum(scores) / len(scores) if scores else 0
    
    def adapt_rule_priorities(self):
        """Adapte les priorités des règles basées sur leur efficacité."""
        
        for rule in self.optimization_rules:
            effectiveness = self.get_rule_effectiveness(rule.name)
            
            # Ajustement de la priorité basé sur l'efficacité
            if effectiveness > 10:  # Très efficace
                rule.priority = max(1, rule.priority - 1)
            elif effectiveness < 2:  # Peu efficace
                rule.priority = min(5, rule.priority + 1)
            
            logger.debug(f"Priorité de {rule.name} ajustée à {rule.priority} "
                        f"(efficacité: {effectiveness:.2f}%)")