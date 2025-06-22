"""Module de logging configuré pour Scrapinium."""

import logging
import structlog
from typing import Dict, Any


def configure_logging(level: str = "INFO") -> None:
    """Configure le système de logging structuré."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Récupère un logger configuré."""
    return structlog.get_logger(name)


class PerformanceLogger:
    """Logger spécialisé pour les métriques de performance."""
    
    def __init__(self):
        self.logger = get_logger("performance")
    
    def log_scraping_performance(self, metrics: Dict[str, Any]) -> None:
        """Log les métriques de performance de scraping."""
        self.logger.info(
            "scraping_performance",
            **metrics
        )
    
    def log_cache_performance(self, metrics: Dict[str, Any]) -> None:
        """Log les métriques de performance de cache."""
        self.logger.info(
            "cache_performance",
            **metrics
        )
    
    def log_memory_usage(self, metrics: Dict[str, Any]) -> None:
        """Log l'utilisation mémoire."""
        self.logger.info(
            "memory_usage",
            **metrics
        )


# Configuration par défaut
configure_logging()