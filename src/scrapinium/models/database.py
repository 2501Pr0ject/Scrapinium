"""Modèles SQLAlchemy pour la base de données."""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .enums import LLMProvider, OutputFormat, TaskStatus, UserRole, UserStatus

Base = declarative_base()


class BaseModelMixin:
    """Mixin pour les modèles de base."""

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ScrapingTask(Base, BaseModelMixin):
    """Modèle de tâche de scraping."""

    __tablename__ = "scraping_tasks"

    # Identifiants
    task_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    # Configuration de scraping
    url = Column(String(2048), nullable=False, index=True)
    output_format = Column(
        String(20), nullable=False, default=OutputFormat.MARKDOWN.value
    )
    llm_provider = Column(String(20), nullable=False, default=LLMProvider.OLLAMA.value)
    llm_model = Column(String(100), nullable=True)

    # État de la tâche
    status = Column(
        String(20), nullable=False, default=TaskStatus.PENDING.value, index=True
    )
    progress = Column(Float, nullable=False, default=0.0)

    # Résultats
    raw_content = Column(Text, nullable=True)
    structured_content = Column(Text, nullable=True)
    task_metadata = Column(JSON, nullable=True)

    # Métriques
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    content_size_bytes = Column(Integer, nullable=True)

    # Messages d'erreur
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Relations
    user_id = Column(String(36), nullable=True, index=True)


class User(Base, BaseModelMixin):
    """Modèle utilisateur."""

    __tablename__ = "users"

    # Identifiants
    user_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)

    # Authentification
    hashed_password = Column(String(255), nullable=True)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    # Profil
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(String(512), nullable=True)

    # Permissions
    role = Column(String(20), nullable=False, default=UserRole.USER.value)
    status = Column(String(20), nullable=False, default=UserStatus.PENDING.value)

    # Préférences
    preferences = Column(JSON, nullable=True)

    # Quotas et limites
    daily_scraping_quota = Column(Integer, nullable=False, default=100)
    monthly_scraping_quota = Column(Integer, nullable=False, default=1000)

    # Relations
    api_keys = relationship(
        "UserAPIKey", back_populates="user", cascade="all, delete-orphan"
    )


class UserAPIKey(Base, BaseModelMixin):
    """Clés API utilisateur."""

    __tablename__ = "user_api_keys"

    # Identifiants
    key_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(
        String(36), ForeignKey("users.user_id"), nullable=False, index=True
    )

    # Configuration clé
    provider = Column(String(20), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    key_name = Column(String(100), nullable=True)

    # État
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(String, nullable=True)

    # Métadonnées
    key_metadata = Column(JSON, nullable=True)

    # Relations
    user = relationship("User", back_populates="api_keys")


class ScrapingTemplate(Base, BaseModelMixin):
    """Modèle de template de scraping."""

    __tablename__ = "scraping_templates"

    # Identifiants
    template_id = Column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    # Informations de base
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False, index=True)
    author = Column(String(100), nullable=True)

    # Configuration
    output_format = Column(String(20), nullable=False, default=OutputFormat.MARKDOWN.value)
    llm_provider = Column(String(20), nullable=False, default=LLMProvider.OLLAMA.value)
    llm_model = Column(String(100), nullable=True)

    # Instructions et configuration
    instructions = Column(Text, nullable=False)
    css_selectors = Column(JSON, nullable=True)
    example_urls = Column(JSON, nullable=True)  # Liste d'URLs d'exemple
    tags = Column(JSON, nullable=True)  # Liste de tags

    # État et métadonnées
    is_public = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Métadonnées
    template_metadata = Column(JSON, nullable=True)
