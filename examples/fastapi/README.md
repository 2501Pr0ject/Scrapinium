# Exemple FastAPI - Scrapinium

## 📋 Description

Application FastAPI complète démontrant l'utilisation avancée de Scrapinium pour le scraping web intelligent avec LLM et ML.

## 🚀 Utilisation

### Démarrer l'application

```bash
# Depuis la racine du projet
cd examples/fastapi
python app.py

# Ou directement
python examples/fastapi/app.py
```

L'API sera disponible sur `http://localhost:8000`

### Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🔧 Fonctionnalités

### API Endpoints

- `POST /scrape` - Démarrer un scraping avec options ML
- `GET /scrape/{task_id}` - Statut d'une tâche  
- `GET /scrape/{task_id}/result` - Récupérer le résultat
- `GET /tasks` - Lister toutes les tâches
- `GET /stats` - Statistiques du système
- `GET /health` - Health check

### ML Pipeline Intégré

- **Classification automatique** du contenu (article, e-commerce, blog...)
- **Détection anti-bot** avec stratégies d'évasion
- **Analyse sémantique** complète (mots-clés, sentiment, topics)
- **Cache intelligent** pour performances optimales

## 📊 Exemples d'Usage

### Scraping Simple

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "output_format": "markdown",
    "use_llm": false
  }'
```

### Scraping avec ML et LLM

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://techcrunch.com/latest",
    "output_format": "markdown", 
    "use_llm": true,
    "custom_instructions": "Extraire uniquement les actualités tech importantes"
  }'
```

### Analyse ML uniquement

```bash
curl -X POST "http://localhost:8000/ml/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<html>...</html>",
    "url": "https://example.com"
  }'
```

## 🏗️ Architecture

L'application utilise l'architecture complète de Scrapinium :

- **Pool de navigateurs** Playwright optimisé
- **Cache multi-niveau** (mémoire + Redis)
- **Pipeline ML** intégré
- **LLM local** via Ollama
- **Monitoring** temps réel

## 📈 Performance

- **3-5x plus rapide** grâce au pool de navigateurs
- **91%+ cache hit rate** pour les requêtes répétées
- **~50ms par analyse ML** avec parallélisation
- **Support de concurrence** jusqu'à 10 requêtes simultanées

## 🔒 Sécurité

- **Rate limiting** automatique
- **Validation d'entrées** stricte
- **Headers de sécurité** appliqués
- **Protection SSRF** intégrée

## 🛠️ Configuration

Variables d'environnement supportées (voir `.env.example`) :

```bash
SCRAPINIUM_DEBUG=false
SCRAPINIUM_HOST=0.0.0.0
SCRAPINIUM_PORT=8000
SCRAPINIUM_DATABASE_URL=sqlite:///./scrapinium.db
SCRAPINIUM_REDIS_URL=redis://localhost:6379
SCRAPINIUM_OLLAMA_HOST=http://localhost:11434
```

## 📚 Documentation

- [Documentation API complète](../../docs/API.md)
- [Architecture détaillée](../../docs/ARCHITECTURE.md)
- [Guide de configuration](../../docs/CONFIGURATION.md)