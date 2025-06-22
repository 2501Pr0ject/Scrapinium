"""Gestionnaire de tâches pour remplacer les variables globales."""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import threading
from ..utils.logging import get_logger

logger = get_logger("task_manager")


class TaskManager:
    """Gestionnaire thread-safe pour les tâches de scraping."""
    
    def __init__(self):
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._completed_tasks: List[Dict[str, Any]] = []
        self._lock = threading.RLock()  # RLock pour éviter les deadlocks
        self._max_completed_tasks = 1000  # Limiter la mémoire
        
    def add_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Ajouter une tâche active."""
        with self._lock:
            task_data["created_at"] = datetime.now(timezone.utc).isoformat()
            task_data["status"] = "pending"
            self._active_tasks[task_id] = task_data
            logger.debug(f"Task {task_id} added to active tasks")
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Mettre à jour une tâche active."""
        with self._lock:
            if task_id in self._active_tasks:
                self._active_tasks[task_id].update(updates)
                self._active_tasks[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
                logger.debug(f"Task {task_id} updated")
                return True
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une tâche par ID."""
        with self._lock:
            return self._active_tasks.get(task_id)
    
    def complete_task(self, task_id: str, result_data: Dict[str, Any]) -> bool:
        """Marquer une tâche comme terminée et la déplacer."""
        with self._lock:
            if task_id not in self._active_tasks:
                return False
            
            # Récupérer et mettre à jour la tâche
            task = self._active_tasks.pop(task_id)
            task.update(result_data)
            task["status"] = "completed"
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Ajouter aux tâches terminées
            self._completed_tasks.append(task)
            
            # Limiter la taille de l'historique
            if len(self._completed_tasks) > self._max_completed_tasks:
                removed = self._completed_tasks.pop(0)
                logger.debug(f"Removed old completed task: {removed.get('id', 'unknown')}")
            
            logger.debug(f"Task {task_id} marked as completed")
            return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Marquer une tâche comme échouée."""
        with self._lock:
            if task_id not in self._active_tasks:
                return False
            
            task = self._active_tasks.pop(task_id)
            task["status"] = "failed" 
            task["error"] = error_message
            task["failed_at"] = datetime.now(timezone.utc).isoformat()
            
            self._completed_tasks.append(task)
            
            # Limiter la taille de l'historique
            if len(self._completed_tasks) > self._max_completed_tasks:
                self._completed_tasks.pop(0)
            
            logger.warning(f"Task {task_id} marked as failed: {error_message}")
            return True
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Récupérer toutes les tâches actives."""
        with self._lock:
            return self._active_tasks.copy()
    
    def get_completed_tasks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer les tâches terminées."""
        with self._lock:
            if limit:
                return self._completed_tasks[-limit:]
            return self._completed_tasks.copy()
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Récupérer les statistiques des tâches."""
        with self._lock:
            active_count = len(self._active_tasks)
            completed_count = len(self._completed_tasks)
            
            # Compter par statut
            failed_count = sum(1 for task in self._completed_tasks if task.get("status") == "failed")
            success_count = completed_count - failed_count
            
            return {
                "active_tasks": active_count,
                "completed_tasks": completed_count,
                "successful_tasks": success_count,
                "failed_tasks": failed_count,
                "success_rate": (success_count / completed_count * 100) if completed_count > 0 else 0.0
            }
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Nettoyer les vieilles tâches terminées."""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
            initial_count = len(self._completed_tasks)
            
            self._completed_tasks = [
                task for task in self._completed_tasks
                if datetime.fromisoformat(task.get("completed_at", task.get("failed_at", ""))).replace(tzinfo=timezone.utc).timestamp() > cutoff_time
            ]
            
            removed_count = initial_count - len(self._completed_tasks)
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old completed tasks")
            
            return removed_count
    
    def clear_all(self) -> None:
        """Vider toutes les tâches (pour tests)."""
        with self._lock:
            self._active_tasks.clear()
            self._completed_tasks.clear()
            logger.info("All tasks cleared")


# Instance singleton
_task_manager_instance: Optional[TaskManager] = None
_instance_lock = threading.Lock()


def get_task_manager() -> TaskManager:
    """Récupérer l'instance singleton du gestionnaire de tâches."""
    global _task_manager_instance
    
    if _task_manager_instance is None:
        with _instance_lock:
            if _task_manager_instance is None:
                _task_manager_instance = TaskManager()
                logger.info("TaskManager instance created")
    
    return _task_manager_instance


def reset_task_manager() -> None:
    """Réinitialiser l'instance (pour tests)."""
    global _task_manager_instance
    with _instance_lock:
        _task_manager_instance = None