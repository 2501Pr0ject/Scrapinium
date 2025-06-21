"""Schémas Pydantic pour validation et sérialisation."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator

from .enums import LLMProvider, LLMRole, OutputFormat, TaskStatus, UserRole, UserStatus


class BasePydanticModel(BaseModel):
    """Modèle Pydantic de base."""

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class PaginationParams(BaseModel):
    """Paramètres de pagination."""

    page: int = Field(default=1, ge=1, description="Numéro de page")
    size: int = Field(default=20, ge=1, le=100, description="Taille de la page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class APIResponse(BasePydanticModel):
    """Réponse API standard."""

    success: bool = Field(description="Statut de succès")
    message: Optional[str] = Field(default=None, description="Message informatif")
    data: Optional[dict] = Field(default=None, description="Données de réponse")
    errors: Optional[list[str]] = Field(default=None, description="Liste des erreurs")

    @classmethod
    def success_response(cls, data: dict = None, message: str = None) -> "APIResponse":
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(cls, errors: list[str], message: str = None) -> "APIResponse":
        return cls(success=False, errors=errors, message=message)


# === SCHÉMAS SCRAPING ===


class ScrapingTaskCreate(BasePydanticModel):
    """Modèle pour créer une tâche de scraping."""

    url: HttpUrl = Field(description="URL à scraper")
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN, description="Format de sortie"
    )
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OLLAMA, description="Provider LLM"
    )
    llm_model: Optional[str] = Field(default=None, description="Modèle LLM spécifique")
    user_id: Optional[str] = Field(default=None, description="ID utilisateur")

    @validator("url")
    def validate_url(cls, v):
        url_str = str(v)
        if not url_str.startswith(("http://", "https://")):
            raise ValueError("L'URL doit commencer par http:// ou https://")
        if len(url_str) > 2048:
            raise ValueError("L'URL est trop longue (max 2048 caractères)")
        return v


class ScrapingTaskUpdate(BasePydanticModel):
    """Modèle pour mettre à jour une tâche de scraping."""

    status: Optional[TaskStatus] = None
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    raw_content: Optional[str] = None
    structured_content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    execution_time_ms: Optional[int] = Field(default=None, ge=0)
    tokens_used: Optional[int] = Field(default=None, ge=0)
    content_size_bytes: Optional[int] = Field(default=None, ge=0)
    error_message: Optional[str] = None
    error_details: Optional[dict[str, Any]] = None


class ScrapingTaskResponse(BasePydanticModel):
    """Modèle de réponse pour une tâche de scraping."""

    id: int
    task_id: str
    url: str
    output_format: OutputFormat
    llm_provider: LLMProvider
    llm_model: Optional[str]
    status: TaskStatus
    progress: float
    structured_content: Optional[str]
    metadata: Optional[dict[str, Any]]
    execution_time_ms: Optional[int]
    tokens_used: Optional[int]
    content_size_bytes: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class ContentExtraction(BasePydanticModel):
    """Modèle pour l'extraction de contenu."""

    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    language: Optional[str] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None

    @validator("word_count", pre=True)
    def calculate_word_count(cls, v, values):
        if v is None and "content" in values:
            return len(values["content"].split())
        return v

    @validator("reading_time_minutes", pre=True)
    def calculate_reading_time(cls, v, values):
        if v is None and "word_count" in values and values["word_count"]:
            return max(1, round(values["word_count"] / 200))
        return v


# === SCHÉMAS LLM ===


class LLMMessage(BasePydanticModel):
    """Message pour interaction LLM."""

    role: LLMRole
    content: str = Field(min_length=1, max_length=100000)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class LLMRequest(BasePydanticModel):
    """Requête vers un LLM."""

    provider: LLMProvider
    model: str = Field(min_length=1, max_length=100)
    messages: list[LLMMessage] = Field(min_items=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32000)
    timeout_seconds: int = Field(default=60, ge=1, le=300)

    @validator("messages")
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Au moins un message est requis")
        if not any(msg.role == LLMRole.USER for msg in v):
            raise ValueError("Au moins un message 'user' est requis")
        return v


class LLMResponse(BasePydanticModel):
    """Réponse d'un LLM."""

    provider: LLMProvider
    model: str
    content: str
    usage: Optional[dict[str, int]] = None
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)
    response_time_ms: Optional[int] = None
    cost_estimate: Optional[float] = None

    @property
    def tokens_used(self) -> Optional[int]:
        if self.usage:
            return self.usage.get("total_tokens")
        return None


class APIKeyConfig(BasePydanticModel):
    """Configuration des clés API."""

    provider: LLMProvider
    api_key: str = Field(min_length=1)
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = Field(default=None, ge=1)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)

    @validator("api_key")
    def validate_api_key(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Clé API trop courte")
        return v.strip()


# === SCHÉMAS USER ===


class UserCreate(BasePydanticModel):
    """Modèle pour créer un utilisateur."""

    email: EmailStr = Field(description="Adresse email")
    password: str = Field(min_length=8, max_length=100, description="Mot de passe")
    username: Optional[str] = Field(
        default=None, min_length=3, max_length=50, description="Nom d'utilisateur"
    )
    first_name: Optional[str] = Field(
        default=None, max_length=100, description="Prénom"
    )
    last_name: Optional[str] = Field(default=None, max_length=100, description="Nom")

    @validator("username")
    def validate_username(cls, v):
        if v and not v.isalnum():
            raise ValueError(
                "Le nom d'utilisateur ne peut contenir que des lettres et chiffres"
            )
        return v


class UserUpdate(BasePydanticModel):
    """Modèle pour mettre à jour un utilisateur."""

    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    preferences: Optional[dict[str, Any]] = None


class UserResponse(BasePydanticModel):
    """Modèle de réponse utilisateur."""

    id: int
    user_id: str
    email: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    daily_scraping_quota: int
    monthly_scraping_quota: int
    preferences: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class APIKeyCreate(BasePydanticModel):
    """Modèle pour créer une clé API."""

    provider: LLMProvider = Field(description="Provider LLM")
    api_key: str = Field(min_length=10, description="Clé API")
    key_name: Optional[str] = Field(
        default=None, max_length=100, description="Nom de la clé"
    )

    @validator("api_key")
    def validate_api_key(cls, v):
        return v.strip()


class APIKeyResponse(BasePydanticModel):
    """Modèle de réponse pour une clé API."""

    id: int
    key_id: str
    provider: LLMProvider
    key_name: Optional[str]
    masked_key: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
