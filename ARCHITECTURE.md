# 🏗️ Architecture de Scrapinium

> Architecture hexagonale moderne pour le scraping web intelligent avec LLMs

## 📋 Vue d'ensemble

Scrapinium adopte une **architecture hexagonale** (ports et adaptateurs) qui sépare clairement la logique métier des détails d'implémentation. Cette approche garantit :

- ✅ **Testabilité** : Isolation des composants pour tests unitaires
- ✅ **Maintenabilité** : Code modulaire et découplé
- ✅ **Évolutivité** : Facilité d'ajout de nouvelles fonctionnalités
- ✅ **Flexibilité** : Changement d'implémentation sans impact sur le cœur

## 🔄 Diagramme d'architecture

```mermaid
graph TB
    subgraph "Interfaces Externes"
        UI[Interface Reflex]
        API[API FastAPI]
        CLI[CLI Commands]
    end
    
    subgraph "Couche Application"
        Routes[Routes & Controllers]
        Services[Services Applicatifs]
    end
    
    subgraph "Cœur Métier"
        ScrapingCore[Service de Scraping]
        LLMCore[Service LLM]
        TaskCore[Gestion des Tâches]
    end
    
    subgraph "Adaptateurs Sortants"
        Browser[Gestionnaire Playwright]
        Database[Gestionnaire DB]
        LLMClient[Client Ollama]
        Cache[Cache Redis]
    end
    
    subgraph "Infrastructure"
        Playwright[Playwright Browser]
        SQLite[(Base de Données)]
        Ollama[Ollama LLM]
        Redis[(Cache Redis)]
    end
    
    UI --> Routes
    API --> Routes
    CLI --> Services
    Routes --> Services
    Services --> ScrapingCore
    Services --> LLMCore
    Services --> TaskCore
    
    ScrapingCore --> Browser
    LLMCore --> LLMClient
    TaskCore --> Database
    TaskCore --> Cache
    
    Browser --> Playwright
    Database --> SQLite
    LLMClient --> Ollama
    Cache --> Redis
```

## 📁 Structure détaillée

```
src/scrapinium/
├── 🌐 api/                    # Interface API (Port d'entrée)
│   ├── __init__.py
│   └── app.py                 # Application FastAPI & routes
│
├── 🎨 ui/                     # Interface utilisateur (Port d'entrée)
│   ├── __init__.py
│   ├── app.py                 # Application Reflex principale
│   ├── components/            # Composants réutilisables
│   │   ├── __init__.py
│   │   ├── forms.py          # Formulaires de saisie
│   │   ├── tables.py         # Tableaux de données
│   │   └── cards.py          # Cartes d'affichage
│   └── styles.py             # Système de thème sombre
│
├── 🕸️ scraping/              # Cœur métier - Service de scraping
│   ├── __init__.py
│   ├── browser.py            # Gestionnaire Playwright (Adaptateur)
│   ├── extractor.py          # Extracteur de contenu avec Readability
│   └── service.py            # Service principal de scraping
│
├── 🧠 llm/                   # Cœur métier - Service LLM
│   ├── __init__.py
│   └── ollama.py             # Client Ollama (Adaptateur)
│
├── 🗃️ models/                # Modèles de domaine
│   ├── __init__.py
│   ├── database.py           # Entités SQLAlchemy
│   ├── enums.py              # Énumérations métier
│   └── schemas.py            # DTOs Pydantic
│
├── ⚙️ config/                # Configuration système
│   ├── __init__.py
│   ├── database.py           # Configuration base de données
│   └── settings.py           # Configuration globale
│
└── 🛠️ utils/                 # Utilitaires transversaux
    ├── __init__.py
    ├── helpers.py            # Fonctions utilitaires
    └── validators.py         # Validateurs de données
```

## 🏛️ Principes architecturaux

### 1. Séparation des responsabilités

**Couche Interface (Ports d'entrée)**
- `api/` : Exposition HTTP REST avec FastAPI
- `ui/` : Interface utilisateur avec Reflex
- Responsabilité : Traduction des demandes externes vers le domaine

**Couche Application**
- Routes et contrôleurs dans `api/app.py`
- Orchestration des services métier
- Responsabilité : Coordination et workflow

**Couche Domaine (Cœur métier)**
- `scraping/service.py` : Logique de scraping
- `llm/` : Logique d'intelligence artificielle
- Responsabilité : Règles métier et invariants

**Couche Infrastructure (Adaptateurs sortants)**
- `scraping/browser.py` : Interface avec Playwright
- `llm/ollama.py` : Interface avec Ollama
- `config/database.py` : Interface avec la base de données
- Responsabilité : Communication avec l'extérieur

### 2. Inversion des dépendances

```python
# ✅ Correct : Le service dépend d'une abstraction
class ScrapingService:
    def __init__(self, browser_manager: BrowserManager):
        self.browser = browser_manager  # Interface

# ✅ L'adaptateur implémente l'interface
class PlaywrightBrowserManager(BrowserManager):
    async def navigate(self, url: str) -> Page:
        # Implémentation spécifique Playwright
```

### 3. Configuration par l'extérieur

```python
# Configuration centralisée dans config/settings.py
class Settings(BaseSettings):
    # Application
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Base de données
    database_url: str = "sqlite:///./scrapinium.db"
    
    # LLM
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    
    # Performance
    max_concurrent_requests: int = 10
    request_timeout: int = 60
```

## 🔄 Flux de données

### 1. Scraping d'une URL

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant ScrapingService
    participant BrowserManager
    participant ContentExtractor
    participant LLMService
    participant Database
    
    Client->>API: POST /scrape
    API->>ScrapingService: scrape_url()
    ScrapingService->>BrowserManager: navigate(url)
    BrowserManager->>BrowserManager: load_page()
    BrowserManager-->>ScrapingService: page_content
    ScrapingService->>ContentExtractor: extract_content()
    ContentExtractor-->>ScrapingService: structured_content
    ScrapingService->>LLMService: enhance_with_llm()
    LLMService-->>ScrapingService: enhanced_content
    ScrapingService->>Database: save_task()
    ScrapingService-->>API: result
    API-->>Client: JSON response
```

### 2. Gestion des tâches asynchrones

```mermaid
graph LR
    A[Demande client] --> B[Création tâche]
    B --> C[Queue de traitement]
    C --> D[Worker async]
    D --> E[Mise à jour statut]
    E --> F[Notification client]
    
    D --> G[Scraping Playwright]
    D --> H[Extraction contenu]
    D --> I[Traitement LLM]
```

## 📊 Modèles de données

### Entités principales

```python
# Domain Models
@dataclass
class ScrapingTask:
    """Entité métier pour une tâche de scraping."""
    task_id: str
    url: str
    status: TaskStatus
    output_format: OutputFormat
    created_at: datetime
    metadata: Dict[str, Any]

# Data Transfer Objects
class ScrapingTaskCreate(BaseModel):
    """DTO pour création de tâche."""
    url: HttpUrl
    output_format: OutputFormat = OutputFormat.MARKDOWN
    use_llm: bool = True
    custom_instructions: Optional[str] = None

# Database Entities
class ScrapingTaskDB(Base):
    """Entité base de données."""
    __tablename__ = "scraping_tasks"
    id = Column(Integer, primary_key=True)
    task_id = Column(String(36), unique=True, index=True)
    url = Column(String(2048), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
```

### Énumérations métier

```python
class TaskStatus(str, Enum):
    """Statuts possibles d'une tâche."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OutputFormat(str, Enum):
    """Formats de sortie supportés."""
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"

class LLMProvider(str, Enum):
    """Fournisseurs LLM supportés."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
```

## 🔌 Points d'extension

### 1. Nouveaux adaptateurs LLM

```python
# Interface commune
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: str) -> str:
        pass

# Implémentations
class OllamaProvider(LLMProvider):
    # Implémentation Ollama locale

class OpenAIProvider(LLMProvider):
    # Implémentation OpenAI API

class AnthropicProvider(LLMProvider):
    # Implémentation Claude API
```

### 2. Nouveaux formats de sortie

```python
# Extracteur extensible
class ContentExtractor:
    def __init__(self):
        self.formatters = {
            OutputFormat.MARKDOWN: MarkdownFormatter(),
            OutputFormat.JSON: JSONFormatter(),
            OutputFormat.HTML: HTMLFormatter(),
            # Facile d'ajouter de nouveaux formats
        }
```

### 3. Nouveaux navigateurs

```python
# Interface navigateur
class BrowserManager(ABC):
    @abstractmethod
    async def navigate(self, url: str) -> str:
        pass

# Implémentations possibles
class PlaywrightManager(BrowserManager):
    # Implémentation actuelle

class SeleniumManager(BrowserManager):
    # Implémentation alternative

class RequestsManager(BrowserManager):
    # Pour sites statiques
```

## 🔧 Configuration et déploiement

### Configuration par environnement

```python
# .env.development
SCRAPINIUM_DEBUG=true
SCRAPINIUM_DATABASE_URL=sqlite:///./dev.db
SCRAPINIUM_OLLAMA_HOST=http://localhost:11434

# .env.production
SCRAPINIUM_DEBUG=false
SCRAPINIUM_DATABASE_URL=postgresql://user:pass@db:5432/scrapinium
SCRAPINIUM_OLLAMA_HOST=http://ollama:11434
```

### Docker multi-service

```yaml
# docker-compose.yml
services:
  scrapinium-app:
    build: .
    environment:
      - SCRAPINIUM_DATABASE_URL=postgresql://scrapinium:password@postgres:5432/scrapinium
      - SCRAPINIUM_OLLAMA_HOST=http://ollama:11434
    depends_on: [postgres, ollama, redis]

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: scrapinium

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama

  redis:
    image: redis:7-alpine
```

## 📈 Métriques et observabilité

### Health checks distribuées

```python
@app.get("/health")
async def health_check():
    return {
        "api": await check_api_health(),
        "database": await check_database_health(),
        "ollama": await check_ollama_health(),
        "redis": await check_redis_health(),
    }
```

### Logging structuré

```python
# Logs JSON pour agrégation
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "service": "scrapinium.scraping",
  "task_id": "abc-123",
  "url": "https://example.com",
  "duration_ms": 1500,
  "status": "completed"
}
```

## 🎯 Avantages de cette architecture

### ✅ Testabilité maximale
- Tests unitaires isolés par couche
- Mocks faciles avec interfaces
- Tests d'intégration ciblés

### ✅ Évolutivité technique
- Ajout de nouveaux LLMs sans impact
- Changement de base de données transparent
- Support multi-navigateurs

### ✅ Maintenance simplifiée
- Code découplé et modulaire
- Responsabilités claires
- Refactoring sécurisé

### ✅ Performance optimisée
- Traitement asynchrone natif
- Cache multi-niveaux
- Pools de connexions

## 🚀 Prochaines évolutions

### v0.2.0 - Interface complète
- Interface Reflex complète
- Dashboard de monitoring
- Gestion d'utilisateurs

### v0.3.0 - Distribution
- Workers Celery distribués
- Load balancing intelligent
- Métriques Prometheus

### v1.0.0 - Enterprise
- Multi-tenancy
- Authentification SSO
- Audit et compliance

---

Cette architecture garantit que Scrapinium peut évoluer de manière contrôlée tout en maintenant la qualité et les performances. Elle respecte les principes SOLID et facilite les tests automatisés.