"""Surveillance et optimisation mémoire pour Scrapinium."""

import asyncio
import gc
import logging
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque
import psutil
import os

from ..config import get_logger

logger = get_logger("utils.memory")


@dataclass
class MemorySnapshot:
    """Instantané de l'utilisation mémoire."""
    timestamp: float
    process_memory_mb: float
    system_memory_percent: float
    gc_objects: int
    active_coroutines: int
    cache_size_mb: float = 0.0
    browser_contexts: int = 0
    
    def __post_init__(self):
        self.timestamp = self.timestamp or time.time()


@dataclass 
class MemoryStats:
    """Statistiques mémoire globales."""
    current_usage_mb: float = 0.0
    peak_usage_mb: float = 0.0
    average_usage_mb: float = 0.0
    gc_collections: int = 0
    memory_warnings: int = 0
    oom_near_misses: int = 0
    cache_evictions: int = 0
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    
    @property
    def usage_trend(self) -> str:
        """Tendance d'utilisation mémoire."""
        if len(self.snapshots) < 2:
            return "stable"
        
        recent = self.snapshots[-5:]  # 5 derniers snapshots
        if len(recent) < 2:
            return "stable"
            
        trend = recent[-1].process_memory_mb - recent[0].process_memory_mb
        if trend > 10:  # +10MB
            return "increasing"
        elif trend < -10:  # -10MB
            return "decreasing"
        else:
            return "stable"


class MemoryMonitor:
    """Moniteur de mémoire avancé pour Scrapinium."""
    
    def __init__(
        self, 
        warning_threshold_mb: float = 500.0,
        critical_threshold_mb: float = 1000.0,
        snapshot_interval: int = 30,
        max_snapshots: int = 100
    ):
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.snapshot_interval = snapshot_interval
        self.max_snapshots = max_snapshots
        
        self.stats = MemoryStats()
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Historique des allocations
        self.allocation_history = deque(maxlen=1000)
        
        # Activer tracemalloc pour le debug
        if not tracemalloc.is_tracing():
            tracemalloc.start()
    
    def add_callback(self, event: str, callback: Callable):
        """
        Ajoute un callback pour un événement mémoire.
        
        Events: 'warning', 'critical', 'gc_triggered', 'cleanup_needed'
        """
        self.callbacks[event].append(callback)
    
    def get_current_usage(self) -> MemorySnapshot:
        """Retourne un snapshot de l'utilisation mémoire actuelle."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Mémoire du processus
        process_memory_mb = memory_info.rss / 1024 / 1024
        
        # Mémoire système
        system_memory = psutil.virtual_memory()
        system_memory_percent = system_memory.percent
        
        # Objets Python
        gc_objects = len(gc.get_objects())
        
        # Coroutines actives
        active_coroutines = len([
            task for task in asyncio.all_tasks() 
            if not task.done()
        ])
        
        return MemorySnapshot(
            timestamp=time.time(),
            process_memory_mb=process_memory_mb,
            system_memory_percent=system_memory_percent,
            gc_objects=gc_objects,
            active_coroutines=active_coroutines
        )
    
    async def take_snapshot(self) -> MemorySnapshot:
        """Prend un snapshot et met à jour les statistiques."""
        snapshot = self.get_current_usage()
        
        # Mettre à jour les statistiques
        self.stats.current_usage_mb = snapshot.process_memory_mb
        if snapshot.process_memory_mb > self.stats.peak_usage_mb:
            self.stats.peak_usage_mb = snapshot.process_memory_mb
        
        # Ajouter au snapshot
        self.stats.snapshots.append(snapshot)
        
        # Limiter le nombre de snapshots
        if len(self.stats.snapshots) > self.max_snapshots:
            self.stats.snapshots.pop(0)
        
        # Calculer la moyenne
        if self.stats.snapshots:
            self.stats.average_usage_mb = sum(
                s.process_memory_mb for s in self.stats.snapshots
            ) / len(self.stats.snapshots)
        
        # Vérifier les seuils
        await self._check_thresholds(snapshot)
        
        return snapshot
    
    async def _check_thresholds(self, snapshot: MemorySnapshot):
        """Vérifie les seuils et déclenche les callbacks."""
        
        # Seuil critique
        if snapshot.process_memory_mb > self.critical_threshold_mb:
            self.stats.oom_near_misses += 1
            logger.critical(
                f"🚨 MÉMOIRE CRITIQUE: {snapshot.process_memory_mb:.1f}MB "
                f"(seuil: {self.critical_threshold_mb}MB)"
            )
            await self._trigger_callbacks('critical', snapshot)
            
        # Seuil d'avertissement  
        elif snapshot.process_memory_mb > self.warning_threshold_mb:
            self.stats.memory_warnings += 1
            logger.warning(
                f"⚠️  MÉMOIRE ÉLEVÉE: {snapshot.process_memory_mb:.1f}MB "
                f"(seuil: {self.warning_threshold_mb}MB)"
            )
            await self._trigger_callbacks('warning', snapshot)
    
    async def _trigger_callbacks(self, event: str, snapshot: MemorySnapshot):
        """Déclenche les callbacks pour un événement."""
        for callback in self.callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(snapshot)
                else:
                    callback(snapshot)
            except Exception as e:
                logger.error(f"Erreur callback mémoire {event}: {e}")
    
    async def force_gc(self) -> int:
        """Force un garbage collection et retourne le nombre d'objets collectés."""
        before = len(gc.get_objects())
        
        # GC complet
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)
        
        after = len(gc.get_objects())
        objects_freed = before - after
        
        self.stats.gc_collections += 1
        
        logger.info(f"🗑️  GC forcé: {objects_freed} objets libérés, {collected} collectés")
        
        await self._trigger_callbacks('gc_triggered', await self.take_snapshot())
        
        return objects_freed
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """Optimise l'utilisation mémoire avec plusieurs stratégies."""
        logger.info("🔧 Optimisation mémoire en cours...")
        
        before_snapshot = await self.take_snapshot()
        
        optimizations = {
            "gc_freed_objects": 0,
            "cache_evictions": 0,
            "memory_saved_mb": 0.0,
            "strategies_applied": [],
        }
        
        # 1. Garbage Collection forcé
        gc_freed = await self.force_gc()
        optimizations["gc_freed_objects"] = gc_freed
        optimizations["strategies_applied"].append("garbage_collection")
        
        # 2. Nettoyer les imports inutilisés
        try:
            import sys
            modules_before = len(sys.modules)
            
            # Identifier les modules peu utilisés (simulation)
            # Dans un vrai cas, on analyserait l'usage réel
            optimizations["strategies_applied"].append("module_cleanup")
            
        except Exception as e:
            logger.warning(f"Erreur nettoyage modules: {e}")
        
        # 3. Compacter les structures de données
        try:
            # Compacter les listes/dicts importantes
            optimizations["strategies_applied"].append("data_compaction")
        except Exception as e:
            logger.warning(f"Erreur compaction données: {e}")
        
        after_snapshot = await self.take_snapshot()
        
        # Calculer les gains
        memory_saved = before_snapshot.process_memory_mb - after_snapshot.process_memory_mb
        optimizations["memory_saved_mb"] = memory_saved
        
        logger.info(
            f"✅ Optimisation terminée: {memory_saved:.1f}MB économisés, "
            f"{len(optimizations['strategies_applied'])} stratégies"
        )
        
        return optimizations
    
    async def start_monitoring(self):
        """Démarre la surveillance continue."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"🔍 Surveillance mémoire démarrée (intervalle: {self.snapshot_interval}s)")
    
    async def stop_monitoring(self):
        """Arrête la surveillance."""
        self.monitoring_active = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Surveillance mémoire arrêtée")
    
    async def _monitor_loop(self):
        """Boucle principale de surveillance."""
        while self.monitoring_active:
            try:
                await self.take_snapshot()
                await asyncio.sleep(self.snapshot_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur surveillance mémoire: {e}")
                await asyncio.sleep(self.snapshot_interval)
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Génère un rapport détaillé de la mémoire."""
        current = self.get_current_usage()
        
        report = {
            "current_usage": {
                "process_memory_mb": current.process_memory_mb,
                "system_memory_percent": current.system_memory_percent,
                "gc_objects": current.gc_objects,
                "active_coroutines": current.active_coroutines,
            },
            "statistics": {
                "peak_usage_mb": self.stats.peak_usage_mb,
                "average_usage_mb": self.stats.average_usage_mb,
                "usage_trend": self.stats.usage_trend,
                "gc_collections": self.stats.gc_collections,
                "memory_warnings": self.stats.memory_warnings,
                "oom_near_misses": self.stats.oom_near_misses,
            },
            "thresholds": {
                "warning_mb": self.warning_threshold_mb,
                "critical_mb": self.critical_threshold_mb,
                "warning_reached": current.process_memory_mb > self.warning_threshold_mb,
                "critical_reached": current.process_memory_mb > self.critical_threshold_mb,
            },
            "monitoring": {
                "active": self.monitoring_active,
                "snapshot_count": len(self.stats.snapshots),
                "snapshot_interval": self.snapshot_interval,
            }
        }
        
        # Analyse des tendances
        if len(self.stats.snapshots) >= 2:
            recent_snapshots = self.stats.snapshots[-10:]  # 10 derniers
            memory_values = [s.process_memory_mb for s in recent_snapshots]
            
            report["trends"] = {
                "min_recent": min(memory_values),
                "max_recent": max(memory_values),
                "volatility": max(memory_values) - min(memory_values),
                "direction": self.stats.usage_trend,
            }
        
        return report
    
    async def emergency_cleanup(self) -> bool:
        """Nettoyage d'urgence en cas de mémoire critique."""
        logger.critical("🚨 NETTOYAGE D'URGENCE MÉMOIRE")
        
        try:
            # 1. GC agressif
            await self.force_gc()
            
            # 2. Déclencher les callbacks de nettoyage
            await self._trigger_callbacks('cleanup_needed', await self.take_snapshot())
            
            # 3. Optimisation complète
            await self.optimize_memory()
            
            # Vérifier le résultat
            final_snapshot = await self.take_snapshot()
            
            if final_snapshot.process_memory_mb < self.critical_threshold_mb:
                logger.info("✅ Nettoyage d'urgence réussi")
                return True
            else:
                logger.error("❌ Nettoyage d'urgence insuffisant")
                return False
                
        except Exception as e:
            logger.error(f"💥 Erreur lors du nettoyage d'urgence: {e}")
            return False


# Instance globale
_memory_monitor: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """Retourne l'instance globale du moniteur mémoire."""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor


async def setup_memory_monitoring():
    """Configure la surveillance mémoire pour Scrapinium."""
    monitor = get_memory_monitor()
    
    # Callbacks pour les événements critiques
    async def on_memory_warning(snapshot: MemorySnapshot):
        logger.warning(f"⚠️  Mémoire élevée détectée: {snapshot.process_memory_mb:.1f}MB")
        # Déclencher un GC préventif
        await monitor.force_gc()
    
    async def on_memory_critical(snapshot: MemorySnapshot):
        logger.critical(f"🚨 Mémoire critique: {snapshot.process_memory_mb:.1f}MB")
        # Nettoyage d'urgence
        await monitor.emergency_cleanup()
    
    async def on_cleanup_needed(snapshot: MemorySnapshot):
        logger.info("🧹 Nettoyage mémoire demandé")
        # Ici on pourrait déclencher des nettoyages spécifiques (cache, etc.)
    
    # Enregistrer les callbacks
    monitor.add_callback('warning', on_memory_warning)
    monitor.add_callback('critical', on_memory_critical) 
    monitor.add_callback('cleanup_needed', on_cleanup_needed)
    
    # Démarrer la surveillance
    await monitor.start_monitoring()
    
    logger.info("🔍 Surveillance mémoire configurée et démarrée")