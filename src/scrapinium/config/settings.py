"""Configuration complète pour Scrapinium."""

import json
import logging
import logging.config
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class JSONFormatter(logging.Formatter):
    """Formateur JSON pour les logs structurés."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "module"):
            log_data["module"] = record.module
        if hasattr(record, "funcName"):
            log_data["function"] = record.funcName
        if hasattr(record, "lineno"):
            log_data["line"] = record.lineno

        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
            }:
                log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class Settings(BaseSettings):
    """Configuration complète de l'application."""

    # Application
    app_name: str = "Scrapinium"
    app_version: str = "0.1.0"
    debug: bool = True  # Mode développement activé
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database
    database_url: str = Field(default="sqlite:///./scrapinium.db")
    database_echo: bool = Field(default=False)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = None

    # Ollama
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1:8b")
    ollama_timeout: int = Field(default=120)

    # API Keys externes (optionnelles)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None

    # Scraping
    max_concurrent_requests: int = Field(default=5, ge=1, le=50)
    request_timeout: int = Field(default=30, ge=5, le=300)
    user_agent: str = Field(default="Scrapinium/0.1.0 (Web Scraper)")
    max_content_size: int = Field(default=10 * 1024 * 1024)  # 10MB

    # Sécurité
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    password_min_length: int = Field(default=8)

    # CORS
    cors_origins: list[str] = Field(default=["*"])
    cors_methods: list[str] = Field(default=["*"])
    cors_headers: list[str] = Field(default=["*"])

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_burst: int = Field(default=10)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="standard")  # standard, json

    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # Features flags
    enable_user_registration: bool = Field(default=True)
    enable_api_keys: bool = Field(default=True)
    enable_quotas: bool = Field(default=True)
    enable_caching: bool = Field(default=True)

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith(("sqlite://", "postgresql://", "mysql://")):
            raise ValueError("URL de base de données invalide")
        return v

    @validator("redis_url")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("URL Redis invalide")
        return v

    @validator("ollama_host")
    def validate_ollama_host(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("Host Ollama invalide")
        return v

    @property
    def celery_config(self) -> dict:
        """Configuration Celery."""
        return {
            "broker_url": self.celery_broker_url or self.redis_url,
            "result_backend": self.celery_result_backend or self.redis_url,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "UTC",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": 30 * 60,
            "task_soft_time_limit": 25 * 60,
        }

    @property
    def is_development(self) -> bool:
        return self.debug

    @property
    def is_production(self) -> bool:
        return not self.debug

    def create_logging_config(self) -> dict[str, Any]:
        """Configuration du système de logging."""

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d %(funcName)s(): %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "json": {
                    "()": JSONFormatter,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG" if self.debug else "INFO",
                    "formatter": "detailed",
                    "filename": "logs/scrapinium.log",
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "json",
                    "filename": "logs/errors.log",
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "scrapinium": {
                    "level": "DEBUG" if self.debug else "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
            "root": {"level": "WARNING", "handlers": ["console", "error_file"]},
        }

        return config

    def setup_logging(self):
        """Configure le système de logging."""
        config = self.create_logging_config()
        logging.config.dictConfig(config)

        logger = logging.getLogger("scrapinium")
        logger.info("🔍 Système de logging initialisé")

        if self.debug:
            logger.debug("🐛 Mode debug activé")

    class Config:
        env_file = ".env"
        env_prefix = "SCRAPINIUM_"
        case_sensitive = False


# Instance globale des settings
settings = Settings()


def get_settings() -> Settings:
    """Récupère les settings (pour injection de dépendance)."""
    return settings


def get_logger(name: str = None) -> logging.Logger:
    """Obtient un logger configuré."""
    if name:
        return logging.getLogger(f"scrapinium.{name}")
    return logging.getLogger("scrapinium")
