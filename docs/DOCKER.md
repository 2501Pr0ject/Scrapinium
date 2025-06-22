# 🐳 Guide Docker Scrapinium

## Vue d'ensemble

Scrapinium propose **deux configurations Docker** optimisées :

- **`docker-compose.yml`** : Environnement de **développement**
- **`docker-compose.prod.yml`** : Environnement de **production**

## 🔧 Développement

### Configuration
- **Base de données** : SQLite (simple, locale)
- **Cache** : Redis (optimisations v0.2.0)
- **LLM** : Ollama local
- **Ports exposés** : 8000, 6379, 11434 (debugging)
- **Volumes** : Code source monté pour hot-reload

### Utilisation

```bash
# Démarrage rapide
docker-compose up --build

# En arrière-plan
docker-compose up -d

# Arrêt
docker-compose down

# Logs
docker-compose logs -f scrapinium-app
```

### URLs Développement
- **Interface web** : http://localhost:8000
- **API** : http://localhost:8000/docs
- **Redis** : localhost:6379
- **Ollama** : http://localhost:11434

## 🚀 Production

### Configuration
- **Base de données** : PostgreSQL (robuste, scalable)
- **Cache** : Redis (haute performance)
- **LLM** : Ollama avec support GPU
- **Reverse proxy** : Nginx (SSL, load balancing)
- **Health checks** : Surveillance automatique
- **Sécurité** : Ports fermés, logs optimisés

### Déploiement

```bash
# Configuration production
cp .env.example .env.production
# Éditer .env.production avec vos valeurs

# Variables requises
export SECRET_KEY="your-super-secret-production-key"
export POSTGRES_PASSWORD="your-secure-db-password"

# Démarrage production
docker-compose -f docker-compose.prod.yml up -d

# Vérification
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### URLs Production
- **Interface web** : http://your-domain (via nginx)
- **API** : http://your-domain/api
- **Health check** : http://your-domain/health

## 📊 Services Inclus

### Scrapinium App
- **Port** : 8000
- **Rôle** : API FastAPI + Interface web v0.2.0
- **Fonctionnalités** : Pool navigateurs, cache multi-niveau, streaming

### Redis
- **Port** : 6379 (dev) / interne (prod)
- **Rôle** : Cache haute performance
- **Performance** : 91%+ hit rate, 8500+ ops/sec

### Ollama
- **Port** : 11434
- **Rôle** : LLM local (Llama 3.1 8B)
- **Support** : GPU en production

### PostgreSQL (prod uniquement)
- **Port** : interne
- **Rôle** : Base de données principale
- **Features** : Backup automatique, health checks

### Nginx (prod uniquement)
- **Ports** : 80, 443
- **Rôle** : Reverse proxy, SSL, compression
- **Features** : Rate limiting, static files

## 🔒 Sécurité

### Variables Sensibles
```bash
# JAMAIS dans le code source
SECRET_KEY=your-production-secret
POSTGRES_PASSWORD=secure-password
SSL_CERT_PATH=/path/to/cert
```

### Bonnes Pratiques
- ✅ Utilisez `.env.production` sur le serveur uniquement
- ✅ Changez toutes les clés/mots de passe par défaut
- ✅ Activez HTTPS en production
- ✅ Monitorer les logs de sécurité
- ❌ JAMAIS commiter les fichiers `.env`

## 🔧 Maintenance

### Commandes Utiles

```bash
# Voir les logs
docker-compose logs -f [service]

# Restart un service
docker-compose restart scrapinium-app

# Mise à jour
docker-compose pull
docker-compose up -d

# Nettoyage
docker-compose down -v  # ⚠️ Supprime les données!
docker system prune -a
```

### Monitoring

```bash
# Stats en temps réel
docker stats

# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/stats

# Performance cache
curl http://localhost:8000/stats/cache
```

## 🚀 Performance

### Optimisations Incluses
- **Pool de navigateurs** : 3-5 instances Chromium
- **Cache multi-niveau** : Redis + Memory
- **Streaming** : Traitement efficace mémoire
- **Compression** : GZIP/LZ4/Brotli automatique
- **Health checks** : Auto-healing des services

### Métriques Cibles
- **API Latence** : <100ms
- **Cache Hit Rate** : >90%
- **Memory Usage** : <500MB par service
- **Concurrent Users** : 100+ simultanés

## 🆘 Dépannage

### Problèmes Courants

**Ollama ne démarre pas**
```bash
# Vérifier les logs
docker-compose logs ollama

# Redémarrer
docker-compose restart ollama
```

**Redis connexion échouée**
```bash
# Test de connexion
docker-compose exec redis redis-cli ping

# Vérifier la config
docker-compose exec scrapinium-app env | grep REDIS
```

**Performance dégradée**
```bash
# Statistiques détaillées
curl http://localhost:8000/stats/memory
curl http://localhost:8000/stats/browser

# Nettoyage cache
curl -X DELETE http://localhost:8000/cache
```

## 📚 Ressources

- **Logs** : `./logs/` (montés en volume)
- **Données** : `./data/` (persistantes)
- **Config** : `.env.example` (template)
- **Monitoring** : Interface web http://localhost:8000

---

**🔥 Scrapinium v0.2.0 - Solution de scraping haute performance**