"""Configuration de la base de données."""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..models.database import Base
from .settings import settings


class DatabaseManager:
    """Gestionnaire de base de données."""

    def __init__(self):
        self.sync_engine = None
        self.async_engine = None
        self.sync_session_factory = None
        self.async_session_factory = None
        self._initialize_engines()

    def _initialize_engines(self):
        """Initialize les moteurs de base de données."""
        database_url = settings.database_url

        # Configuration pour SQLite
        if database_url.startswith("sqlite"):
            # Moteur synchrone
            self.sync_engine = create_engine(
                database_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=settings.debug,
            )

            # Moteur asynchrone (pour SQLite, on utilise aiosqlite)
            async_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
            self.async_engine = create_async_engine(
                async_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=settings.debug,
            )

        # Configuration pour PostgreSQL
        elif database_url.startswith("postgresql"):
            # Moteur synchrone
            self.sync_engine = create_engine(
                database_url, pool_size=5, max_overflow=10, echo=settings.debug
            )

            # Moteur asynchrone
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.async_engine = create_async_engine(
                async_url, pool_size=5, max_overflow=10, echo=settings.debug
            )

        else:
            raise ValueError(f"URL de base de données non supportée: {database_url}")

        # Factories de sessions
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine, autocommit=False, autoflush=False
        )

        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        )

    def create_all_tables(self):
        """Crée toutes les tables."""
        Base.metadata.create_all(bind=self.sync_engine)

    def drop_all_tables(self):
        """Supprime toutes les tables."""
        Base.metadata.drop_all(bind=self.sync_engine)

    def get_sync_session(self) -> Session:
        """Obtient une session synchrone."""
        return self.sync_session_factory()

    async def get_async_session(self) -> AsyncSession:
        """Obtient une session asynchrone."""
        return self.async_session_factory()

    def close(self):
        """Ferme les connexions."""
        if self.sync_engine:
            self.sync_engine.dispose()
        if self.async_engine:
            self.async_engine.sync_dispose()


# Instance globale
db_manager = DatabaseManager()


def get_sync_db() -> Session:
    """Dépendance pour obtenir une session synchrone."""
    db = db_manager.get_sync_session()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dépendance pour obtenir une session asynchrone."""
    async with db_manager.async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def init_database():
    """Initialise la base de données."""
    print("🗄️ Initialisation de la base de données...")

    try:
        # Créer les tables
        db_manager.create_all_tables()
        print("✅ Tables créées avec succès")

        # Vérifier la connexion
        with db_manager.get_sync_session() as session:
            session.execute("SELECT 1")
            print("✅ Connexion à la base de données vérifiée")

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        raise


def reset_database():
    """Remet à zéro la base de données (ATTENTION: supprime toutes les données)."""
    print("⚠️ Remise à zéro de la base de données...")

    try:
        # Supprimer toutes les tables
        db_manager.drop_all_tables()
        print("✅ Tables supprimées")

        # Recréer les tables
        db_manager.create_all_tables()
        print("✅ Tables recréées")

    except Exception as e:
        print(f"❌ Erreur lors de la remise à zéro: {e}")
        raise
