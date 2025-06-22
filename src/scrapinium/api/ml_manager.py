"""Gestionnaire ML Pipeline pour remplacer la variable globale."""

import threading
from typing import Optional
from ..ml.ml_pipeline import MLPipeline
from ..utils.logging import get_logger

logger = get_logger("ml_manager")


class MLManager:
    """Gestionnaire thread-safe pour le pipeline ML."""
    
    def __init__(self):
        self._ml_pipeline: Optional[MLPipeline] = None
        self._lock = threading.RLock()
        self._initialization_error: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialiser le pipeline ML."""
        with self._lock:
            if self._ml_pipeline is not None:
                logger.debug("ML Pipeline already initialized")
                return True
            
            try:
                logger.info("🧠 Initializing ML Pipeline...")
                self._ml_pipeline = MLPipeline()
                await self._ml_pipeline.initialize()
                self._initialization_error = None
                logger.info("✅ ML Pipeline initialized successfully")
                return True
                
            except Exception as e:
                error_msg = f"Failed to initialize ML Pipeline: {e}"
                logger.error(error_msg)
                self._initialization_error = error_msg
                self._ml_pipeline = None
                return False
    
    def get_pipeline(self) -> Optional[MLPipeline]:
        """Récupérer le pipeline ML."""
        with self._lock:
            return self._ml_pipeline
    
    def is_available(self) -> bool:
        """Vérifier si le pipeline ML est disponible."""
        with self._lock:
            return self._ml_pipeline is not None
    
    def get_initialization_error(self) -> Optional[str]:
        """Récupérer l'erreur d'initialisation s'il y en a une."""
        with self._lock:
            return self._initialization_error
    
    async def shutdown(self) -> None:
        """Arrêter proprement le pipeline ML."""
        with self._lock:
            if self._ml_pipeline is not None:
                try:
                    # Si le pipeline a une méthode shutdown
                    if hasattr(self._ml_pipeline, 'shutdown'):
                        await self._ml_pipeline.shutdown()
                    logger.info("ML Pipeline shutdown completed")
                except Exception as e:
                    logger.error(f"Error during ML Pipeline shutdown: {e}")
                finally:
                    self._ml_pipeline = None
                    self._initialization_error = None
    
    def reset(self) -> None:
        """Réinitialiser le gestionnaire (pour tests)."""
        with self._lock:
            self._ml_pipeline = None
            self._initialization_error = None
            logger.debug("ML Manager reset")


# Instance singleton
_ml_manager_instance: Optional[MLManager] = None
_instance_lock = threading.Lock()


def get_ml_manager() -> MLManager:
    """Récupérer l'instance singleton du gestionnaire ML."""
    global _ml_manager_instance
    
    if _ml_manager_instance is None:
        with _instance_lock:
            if _ml_manager_instance is None:
                _ml_manager_instance = MLManager()
                logger.info("MLManager instance created")
    
    return _ml_manager_instance


def reset_ml_manager() -> None:
    """Réinitialiser l'instance (pour tests)."""
    global _ml_manager_instance
    with _instance_lock:
        _ml_manager_instance = None