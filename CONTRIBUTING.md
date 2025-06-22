# Guide de Contribution - Scrapinium

## 🤝 Bienvenue dans la Communauté Scrapinium !

Merci de votre intérêt pour contribuer à Scrapinium ! Ce guide vous aidera à participer efficacement au développement de ce projet open-source enterprise-grade.

## 🎯 Types de Contributions

Nous accueillons tous types de contributions :

- 🐛 **Bug Reports** : Signaler des problèmes
- ✨ **Features** : Proposer de nouvelles fonctionnalités  
- 📚 **Documentation** : Améliorer la documentation
- 🧪 **Tests** : Ajouter ou améliorer les tests
- 🔧 **Performance** : Optimisations et améliorations
- 🛡️ **Security** : Corrections de sécurité
- 🌐 **Traductions** : Internationalisation
- 💡 **Idées** : Discussions et propositions

## 🚀 Démarrage Rapide

### Prérequis

```bash
# Outils requis
- Python 3.9+
- Node.js 18+ (pour le frontend)
- Git
- Docker (optionnel)
- PostgreSQL ou SQLite

# Outils recommandés
- VS Code avec extensions Python
- Postman ou Insomnia (test API)
- Redis (pour le cache)
```

### Setup Environnement

```bash
# 1. Fork et clone le projet
git clone https://github.com/your-username/scrapinium.git
cd scrapinium

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Installer Playwright
playwright install

# 5. Configuration environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 6. Initialiser la base de données
python -m scrapinium.database init

# 7. Lancer les tests
python scripts/run_tests.py --level fast

# 8. Démarrer le serveur
uvicorn src.scrapinium.api.app:app --reload
```

### Structure du Projet

```
scrapinium/
├── 📁 src/scrapinium/          # Code source principal
│   ├── api/                    # API FastAPI
│   ├── scraping/              # Moteur de scraping
│   ├── llm/                   # Intégration LLM
│   ├── cache/                 # Système de cache
│   ├── security/              # Sécurité enterprise
│   ├── utils/                 # Utilitaires
│   └── models/                # Modèles de données
├── 📁 tests/                  # Tests complets
├── 📁 docs/                   # Documentation
├── 📁 templates/              # Templates web
├── 📁 static/                 # Assets statiques
├── 📁 scripts/                # Scripts utilitaires
└── 📁 config/                 # Configurations
```

## 🔄 Workflow de Contribution

### 1. Créer une Issue

**Avant de commencer, créez toujours une issue pour :**
- 🐛 Rapporter un bug
- ✨ Proposer une nouvelle fonctionnalité
- 📚 Amélioration de documentation
- 💬 Discussion générale

**Template Bug Report :**
```markdown
## 🐛 Bug Report

### Description
Description claire et concise du bug.

### Reproduction
Étapes pour reproduire le comportement :
1. Aller à '...'
2. Cliquer sur '...'
3. Voir l'erreur

### Comportement Attendu
Description de ce qui devrait se passer.

### Captures d'Écran
Si applicable, ajoutez des captures d'écran.

### Environnement
- OS: [ex. macOS 12.0]
- Python: [ex. 3.9.7]
- Version: [ex. 2.0.0]

### Logs
```
Coller les logs d'erreur ici
```

### Contexte Additionnel
Autres informations utiles.
```

**Template Feature Request :**
```markdown
## ✨ Feature Request

### Problem
Description claire du problème que cette feature résoudrait.

### Solution Proposée
Description claire de ce que vous voulez qu'il se passe.

### Alternatives Considérées
Autres solutions ou fonctionnalités que vous avez considérées.

### Impact
- Performance: [impact prévu]
- Compatibilité: [breaking changes?]
- Complexité: [1-5, 5 = très complexe]

### Implémentation
Idées d'implémentation si vous en avez.
```

### 2. Développement

**Branch Naming Convention :**
```bash
# Features
feature/add-websocket-support
feature/improve-cache-performance

# Bug fixes
bugfix/fix-memory-leak-browser-pool
bugfix/correct-rate-limiting-headers

# Documentation
docs/update-api-reference
docs/add-deployment-guide

# Security
security/fix-xss-vulnerability
security/improve-input-validation
```

**Création de Branch :**
```bash
# Synchroniser avec main
git checkout main
git pull upstream main

# Créer nouvelle branch
git checkout -b feature/your-feature-name

# Développer et commiter
git add .
git commit -m "feat: add your feature description"

# Pousser la branch
git push origin feature/your-feature-name
```

### 3. Standards de Code

#### Python Code Style

**Nous utilisons :**
- ✅ **Black** pour le formatage automatique
- ✅ **isort** pour l'organisation des imports
- ✅ **flake8** pour le linting
- ✅ **mypy** pour le type checking
- ✅ **pytest** pour les tests

**Configuration pré-commit :**
```bash
# Installer pre-commit
pip install pre-commit
pre-commit install

# Lancer manuellement
pre-commit run --all-files
```

**Style Guidelines :**
```python
# ✅ Bon exemple
from typing import Dict, List, Optional, AsyncIterator
import asyncio
import logging

from fastapi import HTTPException, Request
from pydantic import BaseModel, validator

from ..config import settings
from ..utils.security import validate_url

logger = logging.getLogger(__name__)


class ScrapingRequest(BaseModel):
    """Modèle de requête de scraping avec validation."""
    
    url: str
    use_llm: bool = False
    custom_instructions: Optional[str] = None
    
    @validator("url")
    def validate_url_format(cls, v: str) -> str:
        """Validation de l'URL avec sécurité."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL doit commencer par http:// ou https://")
        
        # Validation sécurisée
        validated_url = validate_url(v)
        if not validated_url.is_valid:
            raise ValueError(f"URL invalide: {validated_url.errors}")
        
        return validated_url.sanitized_value


async def process_scraping_request(
    request: ScrapingRequest,
    user_id: Optional[str] = None
) -> Dict[str, any]:
    """
    Traiter une requête de scraping.
    
    Args:
        request: Données de la requête validées
        user_id: ID utilisateur optionnel
        
    Returns:
        Résultat du scraping avec métadonnées
        
    Raises:
        HTTPException: Si erreur de traitement
    """
    try:
        logger.info(f"Traitement scraping pour {request.url}")
        
        # Traitement async
        result = await scraping_service.process_url(
            url=request.url,
            use_llm=request.use_llm,
            instructions=request.custom_instructions,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur scraping {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de traitement: {str(e)}"
        )
```

#### Frontend Code Style

**JavaScript/HTML Standards :**
```javascript
// ✅ Bon exemple - JavaScript moderne
class ScrapingDashboard {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.charts = new Map();
        this.updateInterval = null;
    }
    
    async initialize() {
        try {
            await this.loadInitialData();
            this.setupEventListeners();
            this.startAutoRefresh();
            
            console.log('Dashboard initialisé avec succès');
        } catch (error) {
            console.error('Erreur initialisation dashboard:', error);
            this.showErrorMessage('Impossible de charger le dashboard');
        }
    }
    
    async loadInitialData() {
        const [stats, tasks] = await Promise.all([
            this.apiClient.getStats(),
            this.apiClient.getTasks({ limit: 10 })
        ]);
        
        this.updateStatsDisplay(stats);
        this.updateTasksList(tasks);
    }
    
    setupEventListeners() {
        // Event delegation pour performance
        document.addEventListener('click', (event) => {
            if (event.target.matches('.scrape-btn')) {
                this.handleScrapeRequest(event);
            }
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}
```

### 4. Tests

**Types de Tests :**
```bash
# Tests unitaires rapides
python scripts/run_tests.py --level unit

# Tests d'intégration
python scripts/run_tests.py --level integration

# Tests de sécurité
python scripts/run_tests.py --markers security

# Tests complets
python scripts/run_tests.py --level all --coverage
```

**Écriture de Tests :**
```python
# tests/test_your_feature.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.scrapinium.api.app import create_app


class TestYourFeature:
    """Tests pour votre nouvelle fonctionnalité."""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def mock_data(self):
        """Données de test."""
        return {
            "url": "https://example.com",
            "expected_result": "content processed"
        }
    
    def test_basic_functionality(self, client, mock_data):
        """Test de base de la fonctionnalité."""
        response = client.post("/your-endpoint", json=mock_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data["data"]
    
    @pytest.mark.parametrize("invalid_input,expected_error", [
        ("", "URL requise"),
        ("invalid-url", "Format URL invalide"),
        ("javascript:alert('xss')", "URL non autorisée")
    ])
    def test_input_validation(self, client, invalid_input, expected_error):
        """Test de validation des inputs."""
        response = client.post("/your-endpoint", json={"url": invalid_input})
        
        assert response.status_code == 422
        error_data = response.json()
        assert expected_error in str(error_data)
    
    @patch('src.scrapinium.scraping.service.scrape_url')
    async def test_error_handling(self, mock_scrape, client):
        """Test de gestion d'erreurs."""
        # Simuler une erreur
        mock_scrape.side_effect = Exception("Network error")
        
        response = client.post("/your-endpoint", json={
            "url": "https://example.com"
        })
        
        assert response.status_code == 500
        error_data = response.json()
        assert "Network error" in error_data["detail"]
```

### 5. Documentation

**Docstrings Standards :**
```python
def complex_function(
    param1: str,
    param2: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Description courte de la fonction.
    
    Description détaillée si nécessaire, avec explications
    sur l'algorithme, les cas d'usage, etc.
    
    Args:
        param1: Description du premier paramètre
        param2: Description du second paramètre (optionnel)
        **kwargs: Paramètres additionnels
            - special_option: Description de l'option
            - another_option: Autre option possible
    
    Returns:
        Dictionnaire contenant:
            - result: Résultat principal
            - metadata: Métadonnées du traitement
            - success: Booléen de succès
    
    Raises:
        ValueError: Si param1 est vide
        HTTPException: Si erreur réseau
        
    Example:
        >>> result = complex_function("test", param2=42)
        >>> print(result["success"])
        True
        
    Note:
        Cette fonction est optimisée pour de gros volumes.
        Utiliser avec précaution en production.
    """
```

**Documentation API :**
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["scraping"])


class ScrapeRequest(BaseModel):
    """
    Modèle de requête de scraping.
    
    Attributes:
        url: URL à scraper (HTTPS recommandé)
        use_llm: Utiliser LLM pour traitement
        instructions: Instructions personnalisées
    """
    url: str
    use_llm: bool = False
    instructions: Optional[str] = None


@router.post(
    "/scrape",
    summary="Créer une tâche de scraping",
    description="""
    Crée une nouvelle tâche de scraping pour l'URL spécifiée.
    
    - **url**: URL à scraper (doit être accessible publiquement)
    - **use_llm**: Active le traitement par LLM pour structurer le contenu
    - **instructions**: Instructions personnalisées pour le LLM
    
    La tâche est traitée de manière asynchrone. Utilisez l'endpoint
    `/scrape/{task_id}` pour suivre le progrès.
    """,
    response_description="Tâche créée avec succès",
    responses={
        200: {
            "description": "Tâche créée",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "task_id": "task_123456789",
                            "status": "pending"
                        }
                    }
                }
            }
        },
        422: {"description": "Paramètres invalides"},
        429: {"description": "Rate limit dépassé"}
    }
)
async def create_scraping_task(request: ScrapeRequest):
    """Créer une nouvelle tâche de scraping."""
    # Implémentation...
```

## 📋 Pull Request Process

### 1. Checklist Pré-PR

**Avant de soumettre :**
- [ ] Tests ajoutés/mis à jour
- [ ] Documentation mise à jour
- [ ] Code formaté (black, isort)
- [ ] Linting passé (flake8, mypy)
- [ ] Tests passent localement
- [ ] Commits signés (optionnel mais recommandé)

### 2. Template Pull Request

```markdown
## 📝 Description

Résumé clair des changements et des raisons.

Fixes #(issue_number)

## 🔄 Type de Changement

- [ ] 🐛 Bug fix (changement non-breaking qui corrige un problème)
- [ ] ✨ New feature (changement non-breaking qui ajoute une fonctionnalité)
- [ ] 💥 Breaking change (fix ou feature qui casserait les fonctionnalités existantes)
- [ ] 📚 Documentation update

## 🧪 Comment Tester

Instructions détaillées pour tester vos changements :

1. Étape 1
2. Étape 2
3. Résultat attendu

## 📋 Checklist

- [ ] Mon code suit les guidelines du projet
- [ ] J'ai effectué une auto-review de mon code
- [ ] J'ai commenté mon code, particulièrement les parties complexes
- [ ] J'ai fait les changements de documentation correspondants
- [ ] Mes changements ne génèrent pas de nouveaux warnings
- [ ] J'ai ajouté des tests qui prouvent que mon fix est efficace ou que ma feature fonctionne
- [ ] Les tests unitaires nouveaux et existants passent localement
- [ ] Toutes les dépendances sont à jour

## 📊 Impact Performance

Si applicable, détaillez l'impact sur les performances :
- Temps d'exécution : +/- X%
- Utilisation mémoire : +/- X MB
- Benchmarks avant/après

## 🔒 Sécurité

Si ce changement a des implications de sécurité :
- [ ] Audit de sécurité effectué
- [ ] Tests de sécurité ajoutés
- [ ] Documentation sécurité mise à jour

## 📸 Screenshots

Si applicable, ajoutez des screenshots des changements UI.

## 🔗 Références

- Issue connexe: #XXX
- Documentation: [lien]
- Discussions: [lien]
```

### 3. Review Process

**Nos critères de review :**

1. **Fonctionnalité** 
   - ✅ Code fonctionne comme attendu
   - ✅ Cas limites gérés
   - ✅ Erreurs gérées proprement

2. **Qualité Code**
   - ✅ Code lisible et maintenable
   - ✅ Standards de codage respectés
   - ✅ Architecture cohérente

3. **Tests**
   - ✅ Couverture de test adéquate
   - ✅ Tests edge cases
   - ✅ Tests de régression

4. **Sécurité**
   - ✅ Pas de vulnérabilités introduites
   - ✅ Validation des inputs
   - ✅ Gestion des erreurs sécurisée

5. **Performance**
   - ✅ Pas de régression performance
   - ✅ Optimisations appropriées
   - ✅ Utilisation mémoire raisonnable

6. **Documentation**
   - ✅ Documentation à jour
   - ✅ Comments appropriés
   - ✅ API documentation mise à jour

## 🎖️ Reconnaissance

### Hall of Fame

Nous reconnaissons nos contributeurs de plusieurs façons :

- 🏆 **Contributors Wall** dans le README
- 🎯 **Badges spécialisés** (Security, Performance, Documentation, etc.)
- 📧 **Newsletter mentions** pour contributions majeures
- 🎁 **Goodies** pour contributeurs réguliers

### Types de Contributeurs

- 🥇 **Core Maintainer** : Accès write, décisions techniques
- 🥈 **Regular Contributor** : 10+ PRs acceptées
- 🥉 **Active Contributor** : 5+ PRs acceptées  
- 🌟 **Community Helper** : Support utilisateurs, documentation
- 🐛 **Bug Hunter** : 5+ bugs reportés/corrigés
- 🛡️ **Security Researcher** : Vulnérabilités découvertes
- 📚 **Documentation Expert** : Améliorations documentation

## 🤔 Besoin d'Aide ?

### Ressources

- 📖 **Documentation** : `/docs` folder
- 💬 **Discussions** : GitHub Discussions
- 🐛 **Issues** : GitHub Issues
- 📧 **Email** : contributors@scrapinium.com

### Mentorship

Nouveau contributeur ? Nous avons un programme de mentorship !

- ✅ Issues étiquetées `good-first-issue`
- ✅ Issues étiquetées `help-wanted`
- ✅ Mentoring par des contributeurs expérimentés
- ✅ Sessions de code review en live (monthly)

### Communication

- **GitHub Discussions** : Questions générales, idées
- **GitHub Issues** : Bugs, feature requests
- **Email** : Problèmes privés, sécurité
- **Discord** : Chat informel (lien dans README)

## 📄 Licence

En contribuant à Scrapinium, vous acceptez que vos contributions soient licenciées sous la même licence que le projet.

---

**Merci de contribuer à Scrapinium ! 🚀**

Ensemble, construisons le meilleur outil de scraping open-source du marché !

---

**Version**: 1.0.0  
**Dernière mise à jour**: 2024-12-21  
**Maintainers**: @core-team