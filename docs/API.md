# API Reference - Scrapinium

## 🚀 API REST Complète

Scrapinium expose une API REST moderne et performante avec documentation OpenAPI/Swagger intégrée.

## 📡 Endpoints Principaux

### Base URL
```
Development: http://localhost:8000
Production:  https://api.scrapinium.com
```

### Authentication
```http
# Future implementation
Authorization: Bearer <your-api-token>
X-API-Key: <your-api-key>
```

## 🔍 Scraping API

### POST /scrape
**Créer une nouvelle tâche de scraping**

```http
POST /scrape
Content-Type: application/json

{
  "url": "https://example.com",
  "output_format": "markdown",
  "use_llm": true,
  "custom_instructions": "Extract main content and structure it",
  "use_cache": true,
  "priority": "normal"
}
```

**Paramètres:**
- `url` (string, required): URL à scraper (HTTPS recommandé)
- `output_format` (enum): `text`, `markdown`, `json`, `html`
- `use_llm` (boolean): Utiliser LLM pour structurer le contenu
- `custom_instructions` (string): Instructions personnalisées pour le LLM
- `use_cache` (boolean): Utiliser le cache si disponible
- `priority` (enum): `low`, `normal`, `high`, `urgent`

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456789",
    "status": "pending",
    "estimated_completion": "2024-12-21T10:05:00Z",
    "queue_position": 3
  },
  "message": "Tâche de scraping créée avec succès",
  "timestamp": "2024-12-21T10:00:00Z"
}
```

**Codes d'erreur:**
- `400`: Paramètres invalides
- `422`: URL invalide ou non accessible
- `429`: Rate limit dépassé
- `503`: Service temporairement indisponible

---

### GET /scrape/{task_id}
**Obtenir le statut d'une tâche**

```http
GET /scrape/task_123456789
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "id": "task_123456789",
    "url": "https://example.com",
    "status": "completed",
    "progress": 100,
    "result": "# Main Content\n\nProcessed content here...",
    "metadata": {
      "execution_time_ms": 2500,
      "tokens_used": 150,
      "content_length": 5200,
      "word_count": 850,
      "reading_time_minutes": 3.4,
      "cache_hit": false,
      "browser_used": "chromium",
      "llm_provider": "ollama"
    },
    "created_at": "2024-12-21T10:00:00Z",
    "completed_at": "2024-12-21T10:02:30Z"
  }
}
```

**Statuts possibles:**
- `pending`: En attente dans la queue
- `initializing`: Initialisation des ressources
- `extracting`: Extraction du contenu
- `processing_llm`: Traitement par LLM
- `post_processing`: Post-traitement
- `completed`: Terminé avec succès
- `failed`: Échec avec erreur

---

### GET /tasks
**Lister toutes les tâches**

```http
GET /tasks?limit=20&offset=0&status=completed&sort=created_at:desc
```

**Paramètres de requête:**
- `limit` (int): Nombre max de résultats (1-100, défaut: 20)
- `offset` (int): Offset pour pagination (défaut: 0)
- `status` (enum): Filtrer par statut
- `sort` (string): Tri `field:direction` (ex: `created_at:desc`)

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task_123456789",
        "url": "https://example.com",
        "status": "completed",
        "created_at": "2024-12-21T10:00:00Z",
        "execution_time_ms": 2500
      }
    ],
    "total": 156,
    "active": 3,
    "completed": 150,
    "failed": 3,
    "pagination": {
      "limit": 20,
      "offset": 0,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 📊 Monitoring API

### GET /health
**Health check système**

```http
GET /health
```

**Réponse 200:**
```json
{
  "api": "healthy",
  "database": "connected",
  "cache": "operational",
  "browser_pool": "ready",
  "llm": "available",
  "timestamp": "2024-12-21T10:00:00Z",
  "version": "2.0.0",
  "uptime_seconds": 86400
}
```

---

### GET /stats
**Statistiques globales**

```http
GET /stats
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "total_tasks": 1542,
    "active_tasks": 5,
    "completed_tasks": 1480,
    "failed_tasks": 57,
    "success_rate": 96.3,
    "average_execution_time_ms": 2850,
    "requests_per_minute": 45,
    "cache_hit_rate": 78.5,
    "browser_pool": {
      "active_browsers": 3,
      "available_browsers": 2,
      "total_requests": 8945,
      "average_response_time_ms": 1200
    },
    "memory": {
      "process_memory_mb": 256,
      "cache_memory_mb": 128,
      "available_memory_mb": 1792
    }
  }
}
```

---

### GET /stats/cache
**Statistiques détaillées du cache**

```http
GET /stats/cache
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "hit_rate": 78.5,
    "total_requests": 8945,
    "cache_hits": 7022,
    "cache_misses": 1923,
    "total_entries": 2456,
    "memory_usage_mb": 128,
    "redis_usage_mb": 340,
    "average_response_time_ms": 15,
    "strategies": {
      "lru": {
        "entries": 1200,
        "hit_rate": 85.2
      },
      "ttl": {
        "entries": 856,
        "hit_rate": 72.1
      },
      "smart": {
        "entries": 400,
        "hit_rate": 91.8
      }
    },
    "top_cached_domains": [
      {"domain": "example.com", "requests": 145, "hit_rate": 89.6},
      {"domain": "test.org", "requests": 98, "hit_rate": 76.5}
    ]
  }
}
```

---

### GET /stats/memory
**Surveillance mémoire détaillée**

```http
GET /stats/memory
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "current_usage": {
      "process_memory_mb": 256.8,
      "heap_memory_mb": 189.2,
      "cache_memory_mb": 128.4,
      "browser_memory_mb": 67.6
    },
    "thresholds": {
      "warning_mb": 512,
      "critical_mb": 1024,
      "max_mb": 2048
    },
    "garbage_collection": {
      "last_run": "2024-12-21T09:55:00Z",
      "objects_freed": 1580,
      "time_taken_ms": 45
    },
    "memory_trend": {
      "growth_rate_mb_per_hour": 2.3,
      "peak_usage_mb": 289.1,
      "average_usage_mb": 245.7
    }
  }
}
```

---

### GET /stats/browser
**Statistiques du pool de navigateurs**

```http
GET /stats/browser
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "pool_status": {
      "max_browsers": 5,
      "active_browsers": 3,
      "available_browsers": 2,
      "queue_length": 0
    },
    "performance": {
      "total_requests": 8945,
      "successful_requests": 8756,
      "failed_requests": 189,
      "success_rate": 97.9,
      "average_response_time_ms": 1200,
      "p95_response_time_ms": 2800,
      "p99_response_time_ms": 4500
    },
    "browser_instances": [
      {
        "id": "browser_1",
        "status": "active",
        "requests_handled": 2456,
        "uptime_minutes": 45,
        "last_activity": "2024-12-21T09:59:30Z"
      }
    ]
  }
}
```

## 🛡️ Security API

### GET /security/rate-limit/stats
**Statistiques de rate limiting**

```http
GET /security/rate-limit/stats
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "total_clients": 156,
    "active_clients_1h": 45,
    "blocked_clients": 3,
    "total_requests": 15680,
    "total_blocked_requests": 89,
    "block_rate_percent": 0.57,
    "rules": {
      "default": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000,
        "burst_limit": 10
      },
      "scraping": {
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "requests_per_day": 5000,
        "burst_limit": 5
      }
    },
    "top_abusers": [
      {
        "client_id": "abc12345",
        "abuse_score": 8.5,
        "requests": 1250
      }
    ]
  }
}
```

---

### GET /security/compliance/check
**Audit de conformité sécurité**

```http
GET /security/compliance/check
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "overall_score": 94.5,
    "environment_security": {
      "score": 92,
      "issues": [],
      "warnings": [
        "Variable d'environnement manquante: OPENAI_API_KEY"
      ],
      "compliant": true
    },
    "compliance": {
      "compliance_score": 97.0,
      "checklist": {
        "OWASP_TOP_10": {
          "injection_protection": true,
          "broken_authentication": true,
          "sensitive_data_exposure": true,
          "xss": true,
          "security_misconfiguration": true
        },
        "ISO_27001": {
          "access_control": true,
          "cryptography": true,
          "operations_security": true
        },
        "GDPR": {
          "data_protection_by_design": true,
          "consent_management": true,
          "breach_notification": true
        }
      }
    },
    "recommendations": [
      "Configurer un WAF en amont",
      "Implémenter la rotation automatique des clés"
    ]
  }
}
```

---

### POST /security/validation/test
**Tester la validation des inputs**

```http
POST /security/validation/test
Content-Type: application/json

{
  "url": "https://example.com",
  "content": "Test content with <script>alert('xss')</script>",
  "custom_data": {
    "nested": "value"
  }
}
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "validation_results": [
      {
        "input_type": "url",
        "result": {
          "is_valid": true,
          "sanitized_value": "https://example.com",
          "errors": [],
          "warnings": [],
          "risk_score": 0.0
        }
      },
      {
        "input_type": "json_payload",
        "result": {
          "is_valid": false,
          "sanitized_value": {},
          "errors": [
            "Pattern XSS détecté: <script>"
          ],
          "warnings": [],
          "risk_score": 7.5
        }
      }
    ],
    "summary": {
      "total_validations": 2,
      "valid_count": 1,
      "invalid_count": 1,
      "max_risk_score": 7.5,
      "risk_level": "HIGH"
    }
  }
}
```

## 🔧 Maintenance API

### POST /maintenance/gc
**Déclencher garbage collection**

```http
POST /maintenance/gc
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "objects_freed": 1580,
    "memory_freed_mb": 23.4,
    "time_taken_ms": 45,
    "gc_stats": {
      "generation_0": 1250,
      "generation_1": 280,
      "generation_2": 50
    }
  },
  "message": "Garbage collection terminé"
}
```

---

### POST /maintenance/optimize
**Optimisation mémoire globale**

```http
POST /maintenance/optimize
```

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "cache_optimized": true,
    "memory_compacted": true,
    "connections_cleaned": 15,
    "browser_pool_optimized": true,
    "memory_saved_mb": 45.2,
    "performance_improvement_percent": 8.5
  },
  "message": "Optimisation mémoire terminée"
}
```

---

### DELETE /cache
**Vider le cache**

```http
DELETE /cache?pattern=*example.com*
```

**Paramètres:**
- `pattern` (string): Pattern pour nettoyage sélectif (optionnel)

**Réponse 200:**
```json
{
  "success": true,
  "data": {
    "cleared_entries": 156,
    "memory_freed_mb": 45.2,
    "time_taken_ms": 120,
    "pattern_used": "*example.com*"
  },
  "message": "Cache nettoyé avec succès"
}
```

## 📋 Modèles de Données

### ScrapingTaskCreate
```json
{
  "url": "string (required, format: uri)",
  "output_format": "enum: text|markdown|json|html (default: markdown)",
  "use_llm": "boolean (default: false)",
  "custom_instructions": "string (optional, max: 2000 chars)",
  "use_cache": "boolean (default: true)",
  "priority": "enum: low|normal|high|urgent (default: normal)"
}
```

### ScrapingResult
```json
{
  "id": "string (uuid)",
  "url": "string (uri)",
  "status": "enum: pending|extracting|processing_llm|completed|failed",
  "progress": "integer (0-100)",
  "result": "string (optional)",
  "metadata": "TaskMetadata",
  "created_at": "string (datetime)",
  "completed_at": "string (datetime, optional)",
  "error": "string (optional)"
}
```

### TaskMetadata
```json
{
  "execution_time_ms": "integer",
  "tokens_used": "integer (optional)",
  "content_length": "integer",
  "word_count": "integer",
  "reading_time_minutes": "number",
  "cache_hit": "boolean",
  "browser_used": "string",
  "llm_provider": "string (optional)",
  "security_score": "number (0-10)"
}
```

### APIResponse
```json
{
  "success": "boolean",
  "data": "object (optional)",
  "message": "string",
  "timestamp": "string (datetime)",
  "errors": "array[string] (optional)",
  "warnings": "array[string] (optional)"
}
```

## 🚨 Codes d'Erreur

### Erreurs Client (4xx)
- **400 Bad Request**: Paramètres invalides
- **401 Unauthorized**: Authentification requise
- **403 Forbidden**: Accès interdit
- **404 Not Found**: Ressource non trouvée
- **422 Unprocessable Entity**: Validation échouée
- **429 Too Many Requests**: Rate limit dépassé

### Erreurs Serveur (5xx)
- **500 Internal Server Error**: Erreur interne
- **503 Service Unavailable**: Service temporairement indisponible
- **504 Gateway Timeout**: Timeout de traitement

### Format d'Erreur Standard
```json
{
  "success": false,
  "message": "Description de l'erreur",
  "error_code": "VALIDATION_FAILED",
  "details": "Détails spécifiques de l'erreur",
  "timestamp": "2024-12-21T10:00:00Z",
  "request_id": "req_123456789"
}
```

## 📈 Rate Limiting

### Headers de Rate Limiting
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640080800
X-RateLimit-Warning: Approaching rate limit
```

### Limites par Endpoint
| Endpoint | Limite/minute | Limite/heure | Limite/jour |
|----------|---------------|--------------|-------------|
| `/scrape` | 30 | 500 | 5,000 |
| `/tasks` | 60 | 1,000 | 10,000 |
| `/stats/*` | 60 | 1,000 | 10,000 |
| `/maintenance/*` | 10 | 100 | 1,000 |

## 🔧 Configuration Headers

### Headers Recommandés
```http
# Requête
Content-Type: application/json
Accept: application/json
User-Agent: MyApp/1.0.0
X-Request-ID: unique-request-id

# Authentification (future)
Authorization: Bearer your-token
X-API-Key: your-api-key
```

### Headers de Sécurité (Réponse)
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

## 🔗 WebSocket API (Future)

### Connexion WebSocket
```javascript
const ws = new WebSocket('wss://api.scrapinium.com/ws');

// Suivre une tâche en temps réel
ws.send(JSON.stringify({
  "action": "subscribe",
  "task_id": "task_123456789"
}));

// Recevoir les mises à jour
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Task ${update.task_id}: ${update.progress}%`);
};
```

## 📚 Documentation Interactive

### Swagger UI
```
GET /docs - Documentation interactive Swagger
GET /redoc - Documentation ReDoc alternative
GET /openapi.json - Schéma OpenAPI 3.0
```

### Exemples cURL

**Scraping Simple:**
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "output_format": "markdown"
  }'
```

**Scraping avec LLM:**
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "output_format": "markdown",
    "use_llm": true,
    "custom_instructions": "Extract main content and create a summary"
  }'
```

**Vérifier une tâche:**
```bash
curl "http://localhost:8000/scrape/task_123456789"
```

**Statistiques:**
```bash
curl "http://localhost:8000/stats"
```

---

**Version API**: 2.0.0  
**Dernière mise à jour**: 2024-12-21  
**Format**: OpenAPI 3.0.0  
**Support**: api-support@scrapinium.com