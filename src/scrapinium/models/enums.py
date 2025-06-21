"""Énumérations centralisées pour Scrapinium."""

from enum import Enum


class TaskStatus(str, Enum):
    """Statuts des tâches de scraping."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(str, Enum):
    """Formats de sortie supportés."""

    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    PLAIN_TEXT = "plain_text"
    HTML = "html"


class LLMProvider(str, Enum):
    """Providers LLM supportés."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"


class LLMRole(str, Enum):
    """Rôles dans une conversation LLM."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class UserRole(str, Enum):
    """Rôles utilisateur."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserStatus(str, Enum):
    """Statuts utilisateur."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
