"""Nettoyage automatique des ressources pour Scrapinium."""

import asyncio
import gc
import time
import weakref
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import os
import tempfile
import shutil

from ..config import get_logger

logger = get_logger("utils.cleanup")


class ResourceType(str, Enum):
    """Types de ressources à nettoyer."""
    MEMORY = "memory"
    CACHE = "cache"
    TEMP_FILES = "temp_files"
    BROWSER_CONTEXTS = "browser_contexts"
    CONNECTIONS = "connections"
    TASKS = "tasks"


@dataclass
class CleanupRule:
    """Règle de nettoyage pour un type de ressource."""
    resource_type: ResourceType
    condition: str  # age, size, count, memory_usage
    threshold: float  # valeur seuil
    action: str  # clean, compress, archive, delete
    priority: int = 5  # 1 = highest, 10 = lowest
    enabled: bool = True
    last_run: float = field(default_factory=time.time)
    success_count: int = 0
    failure_count: int = 0


@dataclass
class CleanupResult:
    """Résultat d'une opération de nettoyage."""
    resource_type: ResourceType
    items_cleaned: int
    bytes_freed: int
    time_taken_ms: float
    success: bool
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ResourceTracker:
    """Trackeur de ressources pour identifier les fuites."""
    
    def __init__(self):
        self.tracked_objects: Dict[str, Set[weakref.ref]] = {
            resource_type.value: set() for resource_type in ResourceType
        }
        self.creation_times: Dict[int, float] = {}
        self.resource_sizes: Dict[int, int] = {}
    
    def track_resource(self, obj: Any, resource_type: ResourceType, size_bytes: int = 0):
        """Ajoute un objet au tracking."""
        obj_id = id(obj)
        self.creation_times[obj_id] = time.time()
        self.resource_sizes[obj_id] = size_bytes
        
        # Créer une weak reference avec callback de nettoyage
        def cleanup_callback(ref):
            self.creation_times.pop(obj_id, None)
            self.resource_sizes.pop(obj_id, None)
            self.tracked_objects[resource_type.value].discard(ref)
        
        weak_ref = weakref.ref(obj, cleanup_callback)
        self.tracked_objects[resource_type.value].add(weak_ref)
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des ressources trackées."""
        current_time = time.time()
        stats = {}
        
        for resource_type, refs in self.tracked_objects.items():
            # Nettoyer les références mortes
            live_refs = {ref for ref in refs if ref() is not None}
            self.tracked_objects[resource_type] = live_refs
            
            # Calculer les stats
            live_objects = [ref() for ref in live_refs if ref() is not None]
            ages = [current_time - self.creation_times.get(id(obj), current_time) 
                   for obj in live_objects if id(obj) in self.creation_times]
            sizes = [self.resource_sizes.get(id(obj), 0) 
                    for obj in live_objects if id(obj) in self.resource_sizes]
            
            stats[resource_type] = {
                "count": len(live_objects),
                "avg_age_seconds": sum(ages) / len(ages) if ages else 0,
                "max_age_seconds": max(ages) if ages else 0,
                "total_size_bytes": sum(sizes),
                "avg_size_bytes": sum(sizes) / len(sizes) if sizes else 0,
            }
        
        return stats
    
    def find_old_resources(self, max_age_seconds: float) -> Dict[ResourceType, List[Any]]:
        """Trouve les ressources anciennes."""
        current_time = time.time()
        old_resources = {}
        
        for resource_type, refs in self.tracked_objects.items():
            old_objects = []
            
            for ref in refs:
                obj = ref()
                if obj is not None:
                    obj_id = id(obj)
                    age = current_time - self.creation_times.get(obj_id, current_time)
                    if age > max_age_seconds:
                        old_objects.append(obj)
            
            if old_objects:
                old_resources[ResourceType(resource_type)] = old_objects
        
        return old_resources


class ResourceCleaner:
    """Nettoyeur de ressources avec règles configurables."""
    
    def __init__(self):
        self.rules: List[CleanupRule] = []
        self.tracker = ResourceTracker()
        self.cleanup_callbacks: Dict[ResourceType, List[Callable]] = {}
        self.temp_dirs: Set[str] = set()
        
        # Règles par défaut
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configure les règles de nettoyage par défaut."""
        self.rules = [
            # Mémoire - nettoyage agressif si > 500MB
            CleanupRule(
                resource_type=ResourceType.MEMORY,
                condition="memory_usage",
                threshold=500.0,  # MB
                action="clean",
                priority=1,
            ),
            
            # Cache - nettoyage si > 1000 entrées
            CleanupRule(
                resource_type=ResourceType.CACHE,
                condition="count",
                threshold=1000,
                action="clean",
                priority=2,
            ),
            
            # Fichiers temporaires - nettoyage si > 1h
            CleanupRule(
                resource_type=ResourceType.TEMP_FILES,
                condition="age",
                threshold=3600,  # secondes
                action="delete",
                priority=3,
            ),
            
            # Contextes navigateur - nettoyage si > 30min
            CleanupRule(
                resource_type=ResourceType.BROWSER_CONTEXTS,
                condition="age",
                threshold=1800,  # secondes
                action="clean",
                priority=4,
            ),
            
            # Tâches - nettoyage si > 100 tâches terminées
            CleanupRule(
                resource_type=ResourceType.TASKS,
                condition="count",
                threshold=100,
                action="archive",
                priority=5,
            ),
        ]
    
    def add_cleanup_callback(self, resource_type: ResourceType, callback: Callable):
        """Ajoute un callback de nettoyage pour un type de ressource."""
        if resource_type not in self.cleanup_callbacks:
            self.cleanup_callbacks[resource_type] = []
        self.cleanup_callbacks[resource_type].append(callback)
    
    def track_temp_directory(self, temp_dir: str):
        """Ajoute un dossier temporaire au tracking."""
        self.temp_dirs.add(temp_dir)
        logger.debug(f"Dossier temporaire tracké: {temp_dir}")
    
    async def cleanup_memory(self) -> CleanupResult:
        """Nettoyage agressif de la mémoire."""
        start_time = time.time()
        
        try:
            # Statistiques avant
            import psutil
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss
            
            # Garbage collection agressif
            collected = 0
            for generation in range(3):
                collected += gc.collect(generation)
            
            # Forcer la libération des caches Python
            gc.disable()
            gc.enable()
            
            # Statistiques après
            memory_after = process.memory_info().rss
            bytes_freed = max(0, memory_before - memory_after)
            
            time_taken = (time.time() - start_time) * 1000
            
            logger.info(f"Nettoyage mémoire: {bytes_freed // 1024 // 1024}MB libérés, {collected} objets collectés")
            
            return CleanupResult(
                resource_type=ResourceType.MEMORY,
                items_cleaned=collected,
                bytes_freed=bytes_freed,
                time_taken_ms=time_taken,
                success=True,
                details={"gc_objects_collected": collected}
            )
            
        except Exception as e:
            time_taken = (time.time() - start_time) * 1000
            logger.error(f"Erreur nettoyage mémoire: {e}")
            
            return CleanupResult(
                resource_type=ResourceType.MEMORY,
                items_cleaned=0,
                bytes_freed=0,
                time_taken_ms=time_taken,
                success=False,
                error_message=str(e)
            )
    
    async def cleanup_temp_files(self) -> CleanupResult:
        """Nettoyage des fichiers temporaires."""
        start_time = time.time()
        files_cleaned = 0
        bytes_freed = 0
        
        try:
            current_time = time.time()
            
            # Nettoyer les dossiers trackés
            for temp_dir in list(self.temp_dirs):
                if os.path.exists(temp_dir):
                    try:
                        # Vérifier l'âge des fichiers
                        dir_age = current_time - os.path.getctime(temp_dir)
                        if dir_age > 3600:  # > 1 heure
                            dir_size = self._get_directory_size(temp_dir)
                            shutil.rmtree(temp_dir)
                            files_cleaned += 1
                            bytes_freed += dir_size
                            self.temp_dirs.discard(temp_dir)
                            logger.debug(f"Dossier temporaire supprimé: {temp_dir}")
                    except Exception as e:
                        logger.warning(f"Erreur suppression {temp_dir}: {e}")
            
            # Nettoyer le dossier temporaire système
            temp_dir = tempfile.gettempdir()
            for item in os.listdir(temp_dir):
                if item.startswith('scrapinium_'):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            file_age = current_time - os.path.getctime(item_path)
                            if file_age > 7200:  # > 2 heures
                                file_size = os.path.getsize(item_path)
                                os.remove(item_path)
                                files_cleaned += 1
                                bytes_freed += file_size
                    except Exception as e:
                        logger.warning(f"Erreur suppression fichier temp {item_path}: {e}")
            
            time_taken = (time.time() - start_time) * 1000
            
            return CleanupResult(
                resource_type=ResourceType.TEMP_FILES,
                items_cleaned=files_cleaned,
                bytes_freed=bytes_freed,
                time_taken_ms=time_taken,
                success=True,
                details={"temp_dirs_tracked": len(self.temp_dirs)}
            )
            
        except Exception as e:
            time_taken = (time.time() - start_time) * 1000
            logger.error(f"Erreur nettoyage fichiers temp: {e}")
            
            return CleanupResult(
                resource_type=ResourceType.TEMP_FILES,
                items_cleaned=files_cleaned,
                bytes_freed=bytes_freed,
                time_taken_ms=time_taken,
                success=False,
                error_message=str(e)
            )
    
    def _get_directory_size(self, directory: str) -> int:
        """Calcule la taille d'un dossier."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
        except OSError:
            pass
        return total_size
    
    async def run_cleanup_rule(self, rule: CleanupRule) -> CleanupResult:
        """Exécute une règle de nettoyage spécifique."""
        if not rule.enabled:
            return CleanupResult(
                resource_type=rule.resource_type,
                items_cleaned=0,
                bytes_freed=0,
                time_taken_ms=0,
                success=True,
                details={"skipped": "rule_disabled"}
            )
        
        start_time = time.time()
        
        try:
            # Exécuter selon le type de ressource
            if rule.resource_type == ResourceType.MEMORY:
                result = await self.cleanup_memory()
            
            elif rule.resource_type == ResourceType.TEMP_FILES:
                result = await self.cleanup_temp_files()
            
            elif rule.resource_type in self.cleanup_callbacks:
                # Exécuter les callbacks personnalisés
                total_cleaned = 0
                total_freed = 0
                
                for callback in self.cleanup_callbacks[rule.resource_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            callback_result = await callback(rule)
                        else:
                            callback_result = callback(rule)
                        
                        if isinstance(callback_result, dict):
                            total_cleaned += callback_result.get("items_cleaned", 0)
                            total_freed += callback_result.get("bytes_freed", 0)
                    except Exception as e:
                        logger.warning(f"Erreur callback nettoyage {rule.resource_type}: {e}")
                
                time_taken = (time.time() - start_time) * 1000
                result = CleanupResult(
                    resource_type=rule.resource_type,
                    items_cleaned=total_cleaned,
                    bytes_freed=total_freed,
                    time_taken_ms=time_taken,
                    success=True,
                    details={"callbacks_executed": len(self.cleanup_callbacks[rule.resource_type])}
                )
            else:
                # Pas de nettoyage spécifique implémenté
                result = CleanupResult(
                    resource_type=rule.resource_type,
                    items_cleaned=0,
                    bytes_freed=0,
                    time_taken_ms=0,
                    success=True,
                    details={"skipped": "no_implementation"}
                )
            
            # Mettre à jour les stats de la règle
            rule.last_run = time.time()
            if result.success:
                rule.success_count += 1
            else:
                rule.failure_count += 1
            
            return result
            
        except Exception as e:
            time_taken = (time.time() - start_time) * 1000
            rule.failure_count += 1
            
            return CleanupResult(
                resource_type=rule.resource_type,
                items_cleaned=0,
                bytes_freed=0,
                time_taken_ms=time_taken,
                success=False,
                error_message=str(e)
            )
    
    async def run_all_cleanup_rules(self) -> List[CleanupResult]:
        """Exécute toutes les règles de nettoyage."""
        results = []
        
        # Trier par priorité
        sorted_rules = sorted(self.rules, key=lambda r: r.priority)
        
        for rule in sorted_rules:
            result = await self.run_cleanup_rule(rule)
            results.append(result)
            
            # Log du résultat
            if result.success:
                logger.info(
                    f"Nettoyage {rule.resource_type.value}: "
                    f"{result.items_cleaned} items, "
                    f"{result.bytes_freed // 1024 // 1024}MB libérés"
                )
            else:
                logger.warning(f"Échec nettoyage {rule.resource_type.value}: {result.error_message}")
        
        return results
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de nettoyage."""
        total_successes = sum(rule.success_count for rule in self.rules)
        total_failures = sum(rule.failure_count for rule in self.rules)
        
        return {
            "rules": [
                {
                    "resource_type": rule.resource_type.value,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                    "success_count": rule.success_count,
                    "failure_count": rule.failure_count,
                    "last_run": rule.last_run,
                    "success_rate": rule.success_count / (rule.success_count + rule.failure_count) if (rule.success_count + rule.failure_count) > 0 else 0,
                }
                for rule in self.rules
            ],
            "summary": {
                "total_rules": len(self.rules),
                "active_rules": sum(1 for rule in self.rules if rule.enabled),
                "total_successes": total_successes,
                "total_failures": total_failures,
                "overall_success_rate": total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0,
            },
            "resource_tracking": self.tracker.get_resource_stats(),
        }


class AutoCleaner:
    """Nettoyeur automatique avec scheduling."""
    
    def __init__(self, cleaner: ResourceCleaner, interval_seconds: int = 300):
        self.cleaner = cleaner
        self.interval_seconds = interval_seconds
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.last_cleanup_time = 0
        self.cleanup_count = 0
    
    async def start(self):
        """Démarre le nettoyage automatique."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Auto-nettoyage démarré (intervalle: {self.interval_seconds}s)")
    
    async def stop(self):
        """Arrête le nettoyage automatique."""
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto-nettoyage arrêté")
    
    async def _cleanup_loop(self):
        """Boucle principale de nettoyage."""
        while self.running:
            try:
                await asyncio.sleep(self.interval_seconds)
                
                if self.running:  # Vérifier encore après le sleep
                    logger.debug("Démarrage du cycle de nettoyage automatique")
                    results = await self.cleaner.run_all_cleanup_rules()
                    
                    # Log du résumé
                    total_items = sum(r.items_cleaned for r in results)
                    total_bytes = sum(r.bytes_freed for r in results)
                    
                    if total_items > 0 or total_bytes > 0:
                        logger.info(
                            f"Cycle de nettoyage terminé: "
                            f"{total_items} items, {total_bytes // 1024 // 1024}MB libérés"
                        )
                    
                    self.last_cleanup_time = time.time()
                    self.cleanup_count += 1
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle de nettoyage: {e}")
                # Continuer malgré l'erreur
                await asyncio.sleep(60)  # Attendre 1 minute avant de réessayer
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du nettoyeur automatique."""
        return {
            "running": self.running,
            "interval_seconds": self.interval_seconds,
            "last_cleanup_time": self.last_cleanup_time,
            "cleanup_count": self.cleanup_count,
            "time_since_last_cleanup": time.time() - self.last_cleanup_time,
        }


# Instances globales
_resource_cleaner: Optional[ResourceCleaner] = None
_auto_cleaner: Optional[AutoCleaner] = None


def get_resource_cleaner() -> ResourceCleaner:
    """Retourne l'instance globale du nettoyeur."""
    global _resource_cleaner
    if _resource_cleaner is None:
        _resource_cleaner = ResourceCleaner()
    return _resource_cleaner


def get_auto_cleaner() -> AutoCleaner:
    """Retourne l'instance globale du nettoyeur automatique."""
    global _auto_cleaner
    if _auto_cleaner is None:
        _auto_cleaner = AutoCleaner(get_resource_cleaner())
    return _auto_cleaner