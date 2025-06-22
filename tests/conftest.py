"""Configuration pytest pour Scrapinium."""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Ajouter le src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from scrapinium.api.app import create_app
    from scrapinium.config.settings import settings
    SCRAPINIUM_AVAILABLE = True
except ImportError:
    SCRAPINIUM_AVAILABLE = False


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Fixture pour event loop asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Configuration pour tests."""
    return {
        "debug": True,
        "database_url": "sqlite:///:memory:",
        "redis_url": None,  # Pas de Redis pour les tests
        "ollama_host": "http://localhost:11434",
        "secret_key": "test-secret-key"
    }


@pytest.fixture
def app(test_settings):
    """Application FastAPI pour tests."""
    if not SCRAPINIUM_AVAILABLE:
        pytest.skip("Scrapinium modules non disponibles")
    
    # Override settings pour tests
    for key, value in test_settings.items():
        setattr(settings, key, value)
    
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    """Client de test synchrone."""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Client de test asynchrone."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_urls():
    """URLs de test pour scraping."""
    return [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://example.com",
    ]


@pytest.fixture
def mock_scraping_result():
    """Résultat de scraping simulé."""
    return {
        "status": "completed",
        "url": "https://example.com",
        "structured_content": "# Test Content\n\nThis is a test.",
        "task_metadata": {
            "execution_time_ms": 1500,
            "tokens_used": 150,
            "content_length": 500
        }
    }


@pytest.fixture
def performance_thresholds():
    """Seuils de performance pour tests."""
    return {
        "api_response_time_ms": 100,
        "cache_hit_rate_min": 80.0,
        "memory_usage_max_mb": 512,
        "browser_pool_wait_time_max_ms": 50
    }


class MockOllamaClient:
    """Client Ollama simulé pour tests."""
    
    async def health_check(self) -> bool:
        return True
    
    async def process_content(self, content: str, instructions: str = "") -> str:
        return f"# Processed Content\n\n{content[:100]}..."
    
    async def cleanup(self):
        pass


@pytest.fixture
def mock_ollama():
    """Client Ollama simulé."""
    return MockOllamaClient()


# Markers pour categoriser les tests
def pytest_configure(config):
    """Configuration des markers pytest."""
    config.addinivalue_line("markers", "unit: Tests unitaires rapides")
    config.addinivalue_line("markers", "integration: Tests d'intégration")
    config.addinivalue_line("markers", "performance: Tests de performance")
    config.addinivalue_line("markers", "slow: Tests lents nécessitant des ressources")
    config.addinivalue_line("markers", "api: Tests de l'API REST")
    config.addinivalue_line("markers", "scraping: Tests de scraping web")
    config.addinivalue_line("markers", "cache: Tests du système de cache")
    config.addinivalue_line("markers", "memory: Tests de gestion mémoire")