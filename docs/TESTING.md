# Guide de Tests - Scrapinium

## 🧪 Framework de Tests Enterprise

Scrapinium dispose d'un framework de tests complet conçu pour assurer la qualité et la robustesse du code en production.

## 📋 Structure des Tests

```
tests/
├── conftest.py                    # Configuration pytest & fixtures
├── pytest.ini                    # Configuration markers & options
├── test_api_integration.py       # Tests API REST complètes
├── test_browser_pool.py          # Tests du pool de navigateurs
├── test_cache_system.py          # Tests système de cache multi-niveau
├── test_e2e_scenarios.py         # Tests de scénarios end-to-end
├── test_memory_management.py     # Tests gestion mémoire
└── test_security.py              # Tests de sécurité
```

## 🏷️ Markers de Tests

| Marker | Description | Usage |
|--------|-------------|-------|
| `unit` | Tests unitaires rapides | Tests isolés, mocks |
| `integration` | Tests d'intégration | Tests API, composants |
| `performance` | Tests de performance | Benchmarks, temps de réponse |
| `slow` | Tests lents | Tests nécessitant des ressources |
| `api` | Tests API REST | Endpoints, validation |
| `scraping` | Tests scraping web | Pool navigateurs, extraction |
| `cache` | Tests cache | Redis, mémoire, stratégies |
| `memory` | Tests mémoire | Surveillance, optimisation |
| `security` | Tests sécurité | XSS, injection SQL, validation |

## 🚀 Lancement des Tests

### Script de Test Intégré

```bash
# Tests rapides (recommandé pour développement)
python scripts/run_tests.py --level fast

# Tests unitaires uniquement
python scripts/run_tests.py --level unit

# Tests d'intégration
python scripts/run_tests.py --level integration

# Tous les tests
python scripts/run_tests.py --level all

# Tests avec couverture
python scripts/run_tests.py --level fast --coverage

# Tests en parallèle
python scripts/run_tests.py --level fast --parallel

# Tests par marker
python scripts/run_tests.py --markers "api and not slow"
```

### Commandes Pytest Directes

```bash
# Tests par marker
pytest -m "unit and not slow"
pytest -m "integration"
pytest -m "performance"
pytest -m "security"

# Tests par fichier
pytest tests/test_api_integration.py -v
pytest tests/test_security.py -v

# Tests avec couverture
pytest --cov=src/scrapinium --cov-report=html

# Tests en parallèle
pytest -n auto

# Tests avec output détaillé
pytest -v --tb=long
```

## 📊 Catégories de Tests

### 1. Tests Unitaires

**Fichiers**: `test_browser_pool.py`, `test_cache_system.py`, `test_memory_management.py`

- Tests isolés avec mocks
- Validation de logique métier
- Calculs et algorithmes
- Configuration et validation

**Exemple**:
```python
@pytest.mark.unit
def test_cache_hit_rate_calculation(self):
    requests = [{"hit": True}, {"hit": False}, {"hit": True}]
    hit_rate = calculate_hit_rate(requests)
    assert hit_rate == 66.67
```

### 2. Tests d'Intégration

**Fichiers**: `test_api_integration.py`, `test_e2e_scenarios.py`

- Tests API end-to-end
- Intégration des composants
- Workflows complets
- Validation des endpoints

**Exemple**:
```python
@pytest.mark.integration
def test_complete_scraping_workflow(self, client):
    # 1. Créer tâche
    response = client.post("/scrape", json={"url": "https://example.com"})
    task_id = response.json()["data"]["task_id"]
    
    # 2. Vérifier statut
    status = client.get(f"/scrape/{task_id}")
    assert status.status_code == 200
```

### 3. Tests de Sécurité

**Fichier**: `test_security.py`

- Protection XSS
- Injection SQL
- Validation des entrées
- Headers de sécurité
- Sanitisation des données

**Exemple**:
```python
@pytest.mark.security
def test_sql_injection_protection(self, client):
    malicious_payload = "'; DROP TABLE users; --"
    response = client.get(f"/scrape/{malicious_payload}")
    assert response.status_code == 404  # Pas 500
```

### 4. Tests de Performance

**Intégrés dans chaque fichier**

- Temps de réponse API
- Utilisation mémoire
- Efficacité du cache
- Concurrence

**Exemple**:
```python
@pytest.mark.performance
def test_api_response_time(self, client, performance_thresholds):
    start_time = time.time()
    response = client.get("/health")
    response_time = (time.time() - start_time) * 1000
    
    assert response_time < performance_thresholds["api_response_time_ms"]
```

## 🔧 Configuration des Tests

### Fixtures Principales

```python
# Client de test FastAPI
@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)

# Seuils de performance
@pytest.fixture
def performance_thresholds():
    return {
        "api_response_time_ms": 100,
        "memory_usage_max_mb": 512,
        "cache_hit_rate_min": 80.0
    }

# URLs de test
@pytest.fixture
def sample_urls():
    return [
        "https://httpbin.org/html",
        "https://example.com"
    ]
```

### Paramètres de Test

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
markers =
    unit: Tests unitaires rapides
    integration: Tests d'intégration
    performance: Tests de performance
    security: Tests de sécurité
    
addopts = -v --tb=short --strict-markers
timeout = 60
```

## 📈 Couverture de Code

### Génération des Rapports

```bash
# Rapport HTML (recommandé)
pytest --cov=src/scrapinium --cov-report=html
open htmlcov/index.html

# Rapport terminal
pytest --cov=src/scrapinium --cov-report=term

# Rapport complet
pytest --cov=src/scrapinium --cov-report=html --cov-report=term --cov-report=xml
```

### Objectifs de Couverture

| Composant | Objectif | Priorité |
|-----------|----------|----------|
| API Core | 95%+ | Critique |
| Cache System | 90%+ | Haute |
| Browser Pool | 85%+ | Haute |
| Memory Management | 80%+ | Moyenne |
| Utilities | 75%+ | Moyenne |

## 🚨 Tests de Régression

### Avant Chaque Release

```bash
# Suite complète de tests
python scripts/run_tests.py --level all --coverage

# Tests de sécurité
pytest -m security -v

# Tests de performance
pytest -m performance -v

# Tests end-to-end
pytest -m "integration and slow" -v
```

### CI/CD Pipeline

```yaml
# .github/workflows/tests.yml (exemple)
- name: Run Fast Tests
  run: python scripts/run_tests.py --level fast

- name: Run Security Tests  
  run: pytest -m security

- name: Run Performance Tests
  run: pytest -m performance
```

## 🔍 Debugging des Tests

### Modes de Debug

```bash
# Mode verbeux complet
pytest -vvv --tb=long

# Arrêt au premier échec
pytest -x

# Debug avec pdb
pytest --pdb

# Logs détaillés
pytest --log-cli-level=DEBUG
```

### Analyse des Échecs

```bash
# Re-exécuter les tests échoués
pytest --lf

# Exécuter les tests les plus lents
pytest --durations=10

# Profiling des tests
pytest --profile
```

## 📚 Bonnes Pratiques

### Structure des Tests

1. **AAA Pattern**: Arrange, Act, Assert
2. **Noms descriptifs**: `test_api_returns_valid_response_for_valid_url`
3. **Tests isolés**: Pas de dépendances entre tests
4. **Mocks appropriés**: Pour les services externes

### Performance

1. **Tests rapides**: Unitaires < 100ms
2. **Tests parallèles**: Utiliser `-n auto` pour CI
3. **Fixtures scoped**: Réutiliser les fixtures coûteuses
4. **Skip intelligents**: Tests dépendants des services externes

### Maintenance

1. **Nettoyage**: Supprimer les tests obsolètes
2. **Refactoring**: Maintenir la lisibilité
3. **Documentation**: Commenter les tests complexes
4. **Mise à jour**: Adapter aux évolutions du code

## 📊 Métriques de Qualité

### Objectifs de Performance

| Métrique | Objectif | Seuil Critique |
|----------|----------|---------------|
| Tests unitaires | < 50ms | 100ms |
| Tests intégration | < 500ms | 1000ms |
| Couverture globale | > 85% | < 70% |
| Taux de succès CI | > 98% | < 95% |

### Surveillance Continue

- **Temps d'exécution**: Monitoring des performances
- **Flaky tests**: Détection des tests instables  
- **Couverture**: Évolution de la couverture
- **Qualité**: Code smells et complexité

---

**Version**: 0.2.0  
**Dernière mise à jour**: 2024-12-21  
**Auteur**: Scrapinium Team