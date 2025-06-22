# 🛠️ Stack Technique de Scrapinium

> Technologies modernes pour le scraping web intelligent avec LLMs

## 📊 Vue d'ensemble

Scrapinium utilise une stack technique moderne, privilégiant les solutions **open-source**, **performantes** et **évolutives**. L'architecture est pensée pour la **simplicité** (KISS) et l'**efficacité** (DRY).

### 🎯 Critères de sélection

- ✅ **Performance** : Solutions optimisées pour la production
- ✅ **Modernité** : Technologies à jour avec support actif
- ✅ **Python-first** : Écosystème unifié autour de Python 3.11+
- ✅ **Open Source** : Pas de vendor lock-in, liberté d'évolution
- ✅ **Docker ready** : Containerisation native pour le déploiement

## 🏗️ Architecture technique

```mermaid
graph TB
    subgraph "Frontend & API"
        Reflex[Reflex 0.4+<br/>Interface Python]
        FastAPI[FastAPI 0.104+<br/>API REST moderne]
        Uvicorn[Uvicorn<br/>Serveur ASGI]
    end
    
    subgraph "Cœur Métier"
        Playwright[Playwright 1.40+<br/>Automation navigateur]
        BeautifulSoup[BeautifulSoup4<br/>Parsing HTML]
        Readability[Readability-lxml<br/>Extraction contenu]
        html2text[html2text<br/>Conversion Markdown]
    end
    
    subgraph "Intelligence IA"
        Ollama[Ollama<br/>LLMs locaux]
        Llama[Llama 3.1 8B<br/>Modèle par défaut]
        HTTPX[HTTPX<br/>Client HTTP async]
    end
    
    subgraph "Données & Cache"
        SQLAlchemy[SQLAlchemy 2.0+<br/>ORM async]
        SQLite[(SQLite<br/>Base par défaut)]
        PostgreSQL[(PostgreSQL<br/>Production)]
        Redis[(Redis 5.0+<br/>Cache & Queues)]
    end
    
    subgraph "DevOps & Outils"
        Poetry[Poetry<br/>Gestion dépendances]
        Ruff[Ruff<br/>Linting ultra-rapide]
        Pytest[pytest<br/>Tests]
        Docker[Docker<br/>Containerisation]
    end
```

## 🌐 Couche Présentation

### FastAPI 0.104+ (API REST)
```yaml
Rôle: API REST principale
Avantages:
  - Performance native avec asyncio
  - Documentation OpenAPI automatique
  - Validation Pydantic intégrée
  - Type hints Python natifs
Endpoints:
  - POST /scrape : Création tâche
  - GET /health : Health checks
  - GET /stats : Métriques globales
```

### Reflex 0.4+ (Interface Web)
```yaml
Rôle: Interface utilisateur Python-native
Avantages:
  - Pas de JavaScript à écrire
  - Réactivité moderne
  - Thème sombre élégant
  - Composants réutilisables
État: Structure créée, développement en cours
```

### Uvicorn (Serveur ASGI)
```yaml
Rôle: Serveur d'application haute performance
Avantages:
  - Support WebSocket natif
  - Performance optimisée
  - Reload automatique en dev
  - Production ready
```

## 🕸️ Couche Scraping

### Playwright 1.40+ (Automation Navigateur)
```yaml
Rôle: Navigation et rendu JavaScript
Avantages:
  - Support moderne (Chrome, Firefox, Safari)
  - JavaScript natif
  - Screenshots et PDF
  - API async Python
Technologies remplacées: Selenium, Requests
```

### BeautifulSoup4 (Parsing HTML)
```yaml
Rôle: Analyse et manipulation HTML/XML
Avantages:
  - API Python intuitive
  - Robustesse face au HTML cassé
  - Sélecteurs CSS et XPath
  - Performance optimisée
```

### Readability-lxml (Extraction Contenu)
```yaml
Rôle: Extraction intelligente du contenu principal
Avantages:
  - Algorithme Mozilla Readability
  - Suppression automatique du bruit
  - Préservation de la structure
  - Support multilingue
```

### html2text (Conversion Markdown)
```yaml
Rôle: Conversion HTML vers Markdown propre
Avantages:
  - Markdown standard
  - Configuration flexible
  - Préservation des liens
  - Gestion des tableaux
```

## 🧠 Couche Intelligence

### Ollama (LLMs Locaux)
```yaml
Rôle: Hébergement local de modèles LLM
Avantages:
  - Pas de coûts API
  - Données privées
  - Latence faible
  - Support GPU
Modèles supportés:
  - Llama 3.1 8B (défaut)
  - Mistral 7B
  - CodeLlama
  - Personnalisés
```

### HTTPX (Client HTTP Async)
```yaml
Rôle: Communication avec Ollama
Avantages:
  - API async/await native
  - Support HTTP/2
  - Timeouts configurables
  - Retry automatique
```

## 🗃️ Couche Données

### SQLAlchemy 2.0+ (ORM)
```yaml
Rôle: Mapping objet-relationnel moderne
Avantages:
  - API async native
  - Type hints complets
  - Migrations Alembic
  - Performance optimisée
Modèles:
  - ScrapingTask : Tâches de scraping
  - User : Utilisateurs (futur)
  - UserAPIKey : Clés API (futur)
```

### SQLite (Base par Défaut)
```yaml
Rôle: Base de données embarquée
Avantages:
  - Zéro configuration
  - Performance locale
  - Backup simple
  - Développement rapide
Limites: Concurrence limitée
```

### PostgreSQL (Production)
```yaml
Rôle: Base de données production
Avantages:
  - Concurrence élevée
  - JSON natif
  - Extensions riches
  - Haute disponibilité
Usage: Docker Compose inclus
```

### Redis 5.0+ (Cache & Queues)
```yaml
Rôle: Cache haute performance et queues
Avantages:
  - Latence sub-millisecondes
  - Structures de données riches
  - Pub/Sub intégré
  - Persistance configurable
Usage futur: Celery workers distribués
```

## 🛠️ Couche DevOps

### Poetry (Gestion Dépendances)
```yaml
Rôle: Gestionnaire de dépendances moderne
Avantages:
  - Lock file deterministe
  - Virtual env automatique
  - Build & publish intégrés
  - Résolution de conflits
Fichiers:
  - pyproject.toml : Configuration
  - poetry.lock : Versions exactes
```

### Ruff (Linting Ultra-rapide)
```yaml
Rôle: Linting et formatage Python
Avantages:
  - 100x plus rapide que pylint
  - Compatible Black/isort
  - Rules configurables
  - Auto-fix intégré
Configuration: pyproject.toml
```

### pytest (Framework de Tests)
```yaml
Rôle: Tests unitaires et d'intégration
Avantages:
  - API simple et puissante
  - Fixtures flexibles
  - Plugins riches
  - Coverage intégré
Extensions: pytest-asyncio
```

### Docker & Docker Compose
```yaml
Rôle: Containerisation et orchestration
Avantages:
  - Environnements reproductibles
  - Déploiement simplifié
  - Multi-services intégré
  - Production ready
Services:
  - scrapinium-app : Application principale
  - postgres : Base de données
  - redis : Cache
  - ollama : LLM local
```

## 📦 Dépendances complètes

### Core Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"                    # Python moderne avec type hints
fastapi = "^0.104.1"               # API REST performante
uvicorn = "^0.24.0"                # Serveur ASGI
playwright = "^1.40.0"             # Automation navigateur
beautifulsoup4 = "^4.12.2"         # Parsing HTML
readability-lxml = "^0.8.1"        # Extraction contenu
html2text = "^2020.1.16"           # Conversion Markdown
sqlalchemy = "^2.0.23"             # ORM moderne
redis = "^5.0.1"                   # Cache et queues
pydantic = "^2.5.0"                # Validation données
pydantic-settings = "^2.10.0"      # Configuration
httpx = "^0.25.2"                  # Client HTTP async
python-dateutil = "^2.8.2"         # Manipulation dates
python-multipart = "^0.0.6"        # Upload fichiers
python-dotenv = "^1.0.0"           # Variables environnement
email-validator = "^2.2.0"         # Validation emails
aiosqlite = "^0.21.0"              # SQLite async
```

### Development Dependencies
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"                 # Framework tests
pytest-asyncio = "^0.21.1"        # Tests async
ruff = "^0.1.6"                   # Linting ultra-rapide
pre-commit = "^3.5.0"             # Hooks Git
mypy = "^1.7.1"                   # Type checking
```

## ⚡ Comparaisons techniques

### vs Scrapy
```yaml
Scrapy:
  ❌ Pas de JavaScript natif
  ❌ API callback complexe
  ❌ Pas d'async/await moderne
  ✅ Performance brute élevée

Scrapinium:
  ✅ JavaScript complet (Playwright)
  ✅ API async/await native
  ✅ LLM intégré
  ✅ Interface moderne
```

### vs Beautiful Soup seul
```yaml
Beautiful Soup seul:
  ❌ Pas de JavaScript
  ❌ Pas d'intelligence IA
  ❌ Extraction manuelle
  ✅ Simple à utiliser

Scrapinium:
  ✅ Stack complète
  ✅ Intelligence artificielle
  ✅ Extraction automatique
  ✅ API REST intégrée
```

### vs Solutions SaaS
```yaml
SaaS (Apify, Octoparse, etc.):
  ❌ Coûts récurrents
  ❌ Vendor lock-in
  ❌ Données externalisées
  ✅ Zéro configuration

Scrapinium:
  ✅ Open source gratuit
  ✅ Données locales/privées
  ✅ Personnalisation complète
  ✅ LLM local sans coûts
```

## 🔧 Configuration optimisée

### Production Settings
```python
# .env.production
SCRAPINIUM_DEBUG=false
SCRAPINIUM_DATABASE_URL=postgresql://scrapinium:password@postgres:5432/scrapinium
SCRAPINIUM_REDIS_URL=redis://redis:6379
SCRAPINIUM_OLLAMA_HOST=http://ollama:11434
SCRAPINIUM_MAX_CONCURRENT_REQUESTS=20
SCRAPINIUM_LOG_LEVEL=INFO
SCRAPINIUM_LOG_FORMAT=json
```

### Docker Production
```yaml
# docker-compose.prod.yml
services:
  scrapinium-app:
    build: .
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 📊 Métriques de performance

### Benchmarks internes
```yaml
Scraping simple (sans JS):
  Temps moyen: 500ms
  Mémoire: ~50MB
  Concurrence: 10 req/s

Scraping avec JS (Playwright):
  Temps moyen: 2s
  Mémoire: ~200MB
  Concurrence: 5 req/s

Traitement LLM (Llama 3.1 8B):
  Temps moyen: 3-5s
  Mémoire: ~8GB (GPU) / ~16GB (CPU)
  Débit: 1-2 req/s
```

### Optimisations appliquées
```yaml
FastAPI:
  - Async/await natif
  - Response models optimisés
  - Middleware CORS minimal

Playwright:
  - Réutilisation des contexts
  - Headless par défaut
  - Timeouts configurés

SQLAlchemy:
  - Connection pooling
  - Lazy loading optimisé
  - Bulk operations

Ollama:
  - Modèle gardé en mémoire
  - Streaming désactivé pour l'API
  - Timeouts appropriés
```

## 🚀 Évolutions futures

### v0.2.0 - Robustesse
```yaml
Ajouts prévus:
  - Celery : Workers distribués
  - Prometheus : Métriques
  - Sentry : Error tracking
  - nginx : Reverse proxy
```

### v0.3.0 - Scale
```yaml
Ajouts prévus:
  - Kubernetes : Orchestration
  - MinIO : Stockage objet
  - Grafana : Dashboards
  - Elasticsearch : Logs centralisés
```

---

Cette stack technique garantit **performance**, **maintenabilité** et **évolutivité** tout en restant simple à déployer et à maintenir. Elle privilégie l'écosystème Python moderne pour une expérience développeur optimale.