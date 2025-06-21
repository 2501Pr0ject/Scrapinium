"""Modèles de données pour Scrapinium."""

# Énumérations
# Modèles de base de données
from .database import (
    Base,
    BaseModelMixin,
    ScrapingTask,
    User,
    UserAPIKey,
)
from .enums import (
    LLMProvider,
    LLMRole,
    OutputFormat,
    TaskStatus,
    UserRole,
    UserStatus,
)

# Schémas Pydantic
from .schemas import (
    APIKeyConfig,
    APIKeyCreate,
    APIKeyResponse,
    APIResponse,
    # Base
    BasePydanticModel,
    ContentExtraction,
    # LLM
    LLMMessage,
    LLMRequest,
    LLMResponse,
    PaginationParams,
    # Scraping
    ScrapingTaskCreate,
    ScrapingTaskResponse,
    ScrapingTaskUpdate,
    # User
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Enums
    "TaskStatus",
    "OutputFormat",
    "LLMProvider",
    "LLMRole",
    "UserRole",
    "UserStatus",
    # Database
    "Base",
    "BaseModelMixin",
    "ScrapingTask",
    "User",
    "UserAPIKey",
    # Schemas
    "BasePydanticModel",
    "PaginationParams",
    "APIResponse",
    "ScrapingTaskCreate",
    "ScrapingTaskUpdate",
    "ScrapingTaskResponse",
    "ContentExtraction",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "APIKeyConfig",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "APIKeyCreate",
    "APIKeyResponse",
]
