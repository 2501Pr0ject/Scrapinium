# Guide de Déploiement - Scrapinium

## 🚀 Déploiement Production Enterprise

Guide complet pour déployer Scrapinium en production avec haute disponibilité, sécurité et performance optimales.

## 🏗️ Architectures de Déploiement

### Architecture Simple (Single Server)

```
┌─────────────────────────────────────┐
│           Load Balancer             │
│         (Nginx/Traefik)            │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│        Scrapinium Server            │
│  ┌─────────────┬─────────────────┐  │
│  │ FastAPI     │ Browser Pool    │  │
│  │ (Uvicorn)   │ (Playwright)    │  │
│  └─────────────┴─────────────────┘  │
│  ┌─────────────┬─────────────────┐  │
│  │ PostgreSQL  │ Redis Cache     │  │
│  │ Database    │                 │  │
│  └─────────────┴─────────────────┘  │
└─────────────────────────────────────┘
```

### Architecture Scalable (Multi-Services)

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
│                  (AWS ALB / GCP LB)                        │
└─────────────┬───────────────────────┬───────────────────────┘
              │                       │
┌─────────────▼───────────┐ ┌─────────▼───────────────────────┐
│   API Servers (3x)      │ │     Worker Nodes (5x)           │
│                         │ │                                 │
│ ┌─────────────────────┐ │ │ ┌─────────────────────────────┐ │
│ │ Scrapinium API      │ │ │ │ Browser Pool Workers        │ │
│ │ (FastAPI/Uvicorn)   │ │ │ │ (Playwright + Celery)       │ │
│ └─────────────────────┘ │ │ └─────────────────────────────┘ │
└─────────────────────────┘ └─────────────────────────────────┘
              │                       │
              └───────────┬───────────┘
                          │
┌─────────────────────────▼─────────────────────────────────┐
│                 Data Layer                                │
│                                                           │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ PostgreSQL  │ │ Redis       │ │ Message Queue       │ │
│ │ (Primary +  │ │ Cluster     │ │ (RabbitMQ/AWS SQS)  │ │
│ │ Read Replica│ │             │ │                     │ │
│ └─────────────┘ └─────────────┘ └─────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### Architecture Enterprise (Cloud Native)

```
┌─────────────────────────────────────────────────────────────┐
│                      CDN + WAF                              │
│                 (CloudFlare/AWS CF)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  Kubernetes Cluster                         │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│ │   Ingress   │ │ API Gateway │ │   Service Mesh          │ │
│ │   (Nginx)   │ │  (Istio)    │ │   (Linkerd/Istio)       │ │
│ └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                Application Layer                         │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│ │ │ API Pods    │ │ Worker Pods │ │ Browser Pool Pods   │ │ │
│ │ │ (3-10 pods) │ │ (5-20 pods) │ │ (2-5 pods)          │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                  Data Layer                             │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│ │ │ PostgreSQL  │ │ Redis       │ │ Monitoring Stack    │ │ │
│ │ │ Operator    │ │ Operator    │ │ (Prometheus/Grafana)│ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🐳 Déploiement Docker

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Reverse Proxy & Load Balancer
  nginx:
    image: nginx:1.21-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - scrapinium-api
    networks:
      - scrapinium-network
    restart: unless-stopped
    
  # Application API
  scrapinium-api:
    image: scrapinium:${VERSION:-latest}
    environment:
      # === PRODUCTION CONFIG ===
      ENVIRONMENT: production
      DEBUG: false
      
      # === DATABASE ===
      DATABASE_URL: postgresql://scrapinium:${DB_PASSWORD}@postgres:5432/scrapinium
      DATABASE_POOL_SIZE: 20
      DATABASE_MAX_OVERFLOW: 30
      
      # === CACHE ===
      REDIS_URL: redis://redis:6379/0
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      
      # === SECURITY ===
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET: ${JWT_SECRET}
      SECURITY_LEVEL: production
      RATE_LIMITING_ENABLED: true
      
      # === BROWSER POOL ===
      BROWSER_POOL_SIZE: 5
      BROWSER_TIMEOUT_SECONDS: 45
      
      # === LLM ===
      OLLAMA_HOST: http://ollama:11434
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      
      # === MONITORING ===
      ENABLE_METRICS: true
      LOG_LEVEL: INFO
      
    volumes:
      - scrapinium-data:/app/data
      - ./logs:/app/logs
    networks:
      - scrapinium-network
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
        reservations:
          memory: 1G
          cpus: "0.5"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Browser Workers (dédié pour Playwright)
  scrapinium-browser-worker:
    image: scrapinium-browser-worker:${VERSION:-latest}
    environment:
      WORKER_TYPE: browser
      REDIS_URL: redis://redis:6379/0
      BROWSER_POOL_SIZE: 3
      MAX_CONCURRENT_TASKS: 10
    volumes:
      - browser-cache:/app/browser-cache
    networks:
      - scrapinium-network
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 3G
          cpus: "2.0"
        reservations:
          memory: 2G
          cpus: "1.0"
    security_opt:
      - seccomp:unconfined
      - apparmor:unconfined

  # Database PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: scrapinium
      POSTGRES_USER: scrapinium
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
      - ./postgres/ssl:/var/lib/postgresql/ssl
    networks:
      - scrapinium-network
    restart: unless-stopped
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/var/lib/postgresql/ssl/server.crt
      -c ssl_key_file=/var/lib/postgresql/ssl/server.key
      -c log_connections=on
      -c log_disconnections=on
      -c log_statement=all
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB

  # Cache Redis
  redis:
    image: redis:7-alpine
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
      - ./redis/redis.conf:/etc/redis/redis.conf
    networks:
      - scrapinium-network
    restart: unless-stopped
    command: redis-server /etc/redis/redis.conf --requirepass ${REDIS_PASSWORD}
    sysctls:
      - net.core.somaxconn=65535

  # LLM Service (Ollama)
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - scrapinium-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    environment:
      OLLAMA_MODELS: "llama2,codellama"

  # Monitoring - Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - scrapinium-network
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  # Monitoring - Grafana
  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - scrapinium-network
    restart: unless-stopped

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  scrapinium-data:
    driver: local
  browser-cache:
    driver: local
  ollama-data:
    driver: local
  prometheus-data:
    driver: local
  grafana-data:
    driver: local

networks:
  scrapinium-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

secrets:
  db_password:
    external: true
  redis_password:
    external: true
  secret_key:
    external: true
  jwt_secret:
    external: true
```

### Configuration Nginx

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https:;";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=scrape:10m rate=5r/s;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/geo+json
        application/javascript
        application/x-javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rdf+xml
        application/rss+xml
        application/xhtml+xml
        application/xml
        font/eot
        font/otf
        font/ttf
        image/svg+xml
        text/css
        text/javascript
        text/plain
        text/xml;
    
    # Upstream servers
    upstream scrapinium_api {
        least_conn;
        server scrapinium-api:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    # HTTPS Redirect
    server {
        listen 80;
        server_name scrapinium.com www.scrapinium.com;
        return 301 https://$server_name$request_uri;
    }
    
    # Main HTTPS Server
    server {
        listen 443 ssl http2;
        server_name scrapinium.com www.scrapinium.com;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;
        
        # API Routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://scrapinium_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # Scraping endpoint (lower rate limit)
        location /scrape {
            limit_req zone=scrape burst=10 nodelay;
            
            proxy_pass http://scrapinium_api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }
        
        # Static files and web interface
        location / {
            proxy_pass http://scrapinium_api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
                proxy_pass http://scrapinium_api;
            }
        }
        
        # Health check
        location /health {
            access_log off;
            proxy_pass http://scrapinium_api;
            proxy_connect_timeout 5s;
            proxy_send_timeout 5s;
            proxy_read_timeout 5s;
        }
        
        # Security
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
```

## ☸️ Déploiement Kubernetes

### Namespace et ConfigMaps

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: scrapinium
  labels:
    name: scrapinium
    environment: production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scrapinium-config
  namespace: scrapinium
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  BROWSER_POOL_SIZE: "5"
  BROWSER_TIMEOUT_SECONDS: "45"
  RATE_LIMITING_ENABLED: "true"
  SECURITY_LEVEL: "production"
  ENABLE_METRICS: "true"
  DATABASE_POOL_SIZE: "20"
  DATABASE_MAX_OVERFLOW: "30"
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: scrapinium-secrets
  namespace: scrapinium
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  JWT_SECRET: <base64-encoded-jwt-secret>
  DATABASE_PASSWORD: <base64-encoded-db-password>
  REDIS_PASSWORD: <base64-encoded-redis-password>
  OPENAI_API_KEY: <base64-encoded-openai-key>
```

### API Deployment

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scrapinium-api
  namespace: scrapinium
  labels:
    app: scrapinium-api
    component: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scrapinium-api
  template:
    metadata:
      labels:
        app: scrapinium-api
        component: api
    spec:
      containers:
      - name: scrapinium-api
        image: scrapinium:2.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://scrapinium:$(DATABASE_PASSWORD)@postgres:5432/scrapinium"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        envFrom:
        - configMapRef:
            name: scrapinium-config
        - secretRef:
            name: scrapinium-secrets
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: app-data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: app-data
        persistentVolumeClaim:
          claimName: scrapinium-data-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: scrapinium-logs-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: scrapinium-api-service
  namespace: scrapinium
spec:
  selector:
    app: scrapinium-api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
```

### Browser Workers Deployment

```yaml
# k8s/browser-workers.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scrapinium-browser-workers
  namespace: scrapinium
  labels:
    app: scrapinium-browser-workers
    component: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scrapinium-browser-workers
  template:
    metadata:
      labels:
        app: scrapinium-browser-workers
        component: worker
    spec:
      containers:
      - name: browser-worker
        image: scrapinium-browser-worker:2.0.0
        env:
        - name: WORKER_TYPE
          value: "browser"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        - name: BROWSER_POOL_SIZE
          value: "3"
        - name: MAX_CONCURRENT_TASKS
          value: "10"
        envFrom:
        - secretRef:
            name: scrapinium-secrets
        resources:
          limits:
            cpu: 2000m
            memory: 3Gi
          requests:
            cpu: 1000m
            memory: 2Gi
        securityContext:
          capabilities:
            add:
            - SYS_ADMIN
        volumeMounts:
        - name: browser-cache
          mountPath: /app/browser-cache
        - name: dev-shm
          mountPath: /dev/shm
      volumes:
      - name: browser-cache
        persistentVolumeClaim:
          claimName: browser-cache-pvc
      - name: dev-shm
        emptyDir:
          medium: Memory
          sizeLimit: 2Gi
```

### Database (PostgreSQL)

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: scrapinium
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: scrapinium
        - name: POSTGRES_USER
          value: scrapinium
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: scrapinium-secrets
              key: DATABASE_PASSWORD
        - name: POSTGRES_INITDB_ARGS
          value: "--auth-host=scram-sha-256"
        ports:
        - containerPort: 5432
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 1Gi
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: postgres-config
          mountPath: /etc/postgresql/postgresql.conf
          subPath: postgresql.conf
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: scrapinium
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: scrapinium-ingress
  namespace: scrapinium
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - scrapinium.com
    - api.scrapinium.com
    secretName: scrapinium-tls
  rules:
  - host: scrapinium.com
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: scrapinium-api-service
            port:
              number: 80
  - host: api.scrapinium.com
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: scrapinium-api-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scrapinium-api-hpa
  namespace: scrapinium
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: scrapinium-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

## ☁️ Déploiement Cloud

### AWS (ECS + RDS + ElastiCache)

```yaml
# aws/ecs-task-definition.json
{
  "family": "scrapinium-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/scrapiniumTaskRole",
  "containerDefinitions": [
    {
      "name": "scrapinium-api",
      "image": "YOUR_ACCOUNT.dkr.ecr.region.amazonaws.com/scrapinium:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "DEBUG", 
          "value": "false"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:ACCOUNT:secret:scrapinium/database-url"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:region:ACCOUNT:secret:scrapinium/redis-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:ACCOUNT:secret:scrapinium/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/scrapinium-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Terraform Infrastructure

```hcl
# terraform/main.tf
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "scrapinium-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = {
    Environment = "production"
    Project = "scrapinium"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "scrapinium-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = true
  
  tags = {
    Environment = "production"
    Project = "scrapinium"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "scrapinium-cluster"
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight = 70
  }
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight = 30
  }
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Environment = "production"
    Project = "scrapinium"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier = "scrapinium-db"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp2"
  storage_encrypted     = true
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.large"
  
  db_name  = "scrapinium"
  username = "scrapinium"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"
  
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "scrapinium-db-final-snapshot"
  
  performance_insights_enabled = true
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
  
  tags = {
    Environment = "production"
    Project = "scrapinium"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "scrapinium-redis"
  description                  = "Redis cluster for Scrapinium"
  
  node_type                    = "cache.t3.medium"
  num_cache_clusters           = 2
  port                         = 6379
  parameter_group_name         = "default.redis7"
  
  subnet_group_name            = aws_elasticache_subnet_group.main.name
  security_group_ids           = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled   = true
  transit_encryption_enabled   = true
  auth_token                   = var.redis_password
  
  automatic_failover_enabled   = true
  multi_az_enabled            = true
  
  snapshot_retention_limit     = 7
  snapshot_window             = "03:00-05:00"
  
  tags = {
    Environment = "production"
    Project = "scrapinium"
  }
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "scrapinium-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 3
  
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight = 70
  }
  
  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight = 30
  }
  
  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = module.vpc.private_subnets
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "scrapinium-api"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.api]
}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 3
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "scrapinium-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

## 📊 Monitoring et Logging

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "scrapinium_alerts.yml"

scrape_configs:
  - job_name: 'scrapinium-api'
    static_configs:
      - targets: ['scrapinium-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Alerting Rules

```yaml
# monitoring/scrapinium_alerts.yml
groups:
- name: scrapinium.rules
  rules:
  - alert: ScrapiniumAPIDown
    expr: up{job="scrapinium-api"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Scrapinium API is down"
      description: "Scrapinium API has been down for more than 2 minutes."
      
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second."
      
  - alert: HighMemoryUsage
    expr: process_memory_usage_percentage > 85
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}%."
      
  - alert: DatabaseConnectionFailure
    expr: postgresql_up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection failure"
      description: "Cannot connect to PostgreSQL database."
      
  - alert: RedisConnectionFailure
    expr: redis_up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Redis connection failure"
      description: "Cannot connect to Redis cache."
      
  - alert: BrowserPoolExhausted
    expr: browser_pool_available_browsers == 0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Browser pool exhausted"
      description: "No available browsers in the pool."
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "Scrapinium Performance Dashboard",
    "tags": ["scrapinium", "performance"],
    "timezone": "UTC",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec",
            "min": 0
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "process_memory_usage_bytes",
            "legendFormat": "Memory Usage"
          }
        ]
      },
      {
        "id": 4,
        "title": "Browser Pool Status",
        "type": "stat",
        "targets": [
          {
            "expr": "browser_pool_active_browsers",
            "legendFormat": "Active"
          },
          {
            "expr": "browser_pool_available_browsers", 
            "legendFormat": "Available"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## 🔧 Scripts de Déploiement

### Script de Déploiement Automatisé

```bash
#!/bin/bash
# scripts/deploy.sh

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
BACKUP_ENABLED=${3:-true}

echo "🚀 Deploying Scrapinium v${VERSION} to ${ENVIRONMENT}"

# Validation
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Check if required environment variables are set
required_vars=("SECRET_KEY" "DATABASE_PASSWORD" "REDIS_PASSWORD")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        echo "❌ Environment variable $var is not set"
        exit 1
    fi
done

# Backup database (if enabled)
if [[ "$BACKUP_ENABLED" == "true" && "$ENVIRONMENT" == "production" ]]; then
    echo "💾 Creating database backup..."
    ./scripts/backup.sh
fi

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml pull

# Database migration (if needed)
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm scrapinium-api python -m alembic upgrade head

# Health check before deployment
echo "🏥 Running health checks..."
./scripts/health_check.sh pre-deployment

# Deploy with zero downtime
echo "🚀 Deploying services..."
if [[ "$ENVIRONMENT" == "production" ]]; then
    # Blue-green deployment for production
    ./scripts/blue_green_deploy.sh "$VERSION"
else
    # Standard deployment for staging
    docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d
fi

# Post-deployment health checks
echo "🏥 Post-deployment health checks..."
sleep 30
./scripts/health_check.sh post-deployment

# Warm up cache
echo "🔥 Warming up cache..."
./scripts/cache_warmup.sh

# Run smoke tests
echo "🧪 Running smoke tests..."
./scripts/smoke_tests.sh "$ENVIRONMENT"

echo "✅ Deployment completed successfully!"
echo "📊 Dashboard: https://grafana.scrapinium.com"
echo "📈 Metrics: https://prometheus.scrapinium.com"
echo "🌐 Application: https://scrapinium.com"
```

### Script de Health Check

```bash
#!/bin/bash
# scripts/health_check.sh

set -euo pipefail

ENVIRONMENT=${ENVIRONMENT:-production}
API_URL=${API_URL:-http://localhost:8000}
TIMEOUT=${TIMEOUT:-30}

echo "🏥 Running health checks for $ENVIRONMENT environment..."

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local timeout=${3:-10}
    
    echo "Checking $endpoint..."
    
    if response=$(curl -s -w "%{http_code}" -o /tmp/response --max-time "$timeout" "$API_URL$endpoint"); then
        if [[ "$response" == "$expected_status" ]]; then
            echo "✅ $endpoint - OK"
            return 0
        else
            echo "❌ $endpoint - Expected $expected_status, got $response"
            return 1
        fi
    else
        echo "❌ $endpoint - Connection failed"
        return 1
    fi
}

# Check database connectivity
check_database() {
    echo "Checking database connectivity..."
    if docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T postgres pg_isready -U scrapinium; then
        echo "✅ Database - OK"
        return 0
    else
        echo "❌ Database - Connection failed"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    echo "Checking Redis connectivity..."
    if docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis - OK"
        return 0
    else
        echo "❌ Redis - Connection failed"
        return 1
    fi
}

# Main health checks
failed_checks=0

# API endpoints
check_endpoint "/health" 200 || ((failed_checks++))
check_endpoint "/api" 200 || ((failed_checks++))
check_endpoint "/stats" 200 || ((failed_checks++))

# Infrastructure
check_database || ((failed_checks++))
check_redis || ((failed_checks++))

# Performance checks
echo "Checking API performance..."
response_time=$(curl -w "%{time_total}" -s -o /dev/null "$API_URL/health")
if (( $(echo "$response_time > 1.0" | bc -l) )); then
    echo "⚠️ API response time is slow: ${response_time}s"
    ((failed_checks++))
else
    echo "✅ API response time: ${response_time}s"
fi

# Summary
if [[ $failed_checks -eq 0 ]]; then
    echo "✅ All health checks passed!"
    exit 0
else
    echo "❌ $failed_checks health check(s) failed!"
    exit 1
fi
```

## 📋 Checklist de Déploiement

### Pré-Production

- [ ] **Code Quality**
  - [ ] Tests passent (>95% succès)
  - [ ] Couverture de code >85%
  - [ ] Linting et formatage corrects
  - [ ] Review de code effectuée

- [ ] **Configuration**
  - [ ] Variables d'environnement configurées
  - [ ] Secrets sécurisés externalisés
  - [ ] Configuration DB/Redis validée
  - [ ] HTTPS certificats valides

- [ ] **Infrastructure** 
  - [ ] Ressources provisionnées
  - [ ] Monitoring configuré
  - [ ] Alertes configurées
  - [ ] Backup strategy en place

### Production

- [ ] **Déploiement**
  - [ ] Backup base de données créé
  - [ ] Migration BD exécutée
  - [ ] Services déployés avec succès
  - [ ] Health checks passent

- [ ] **Post-Déploiement**
  - [ ] Monitoring fonctionnel
  - [ ] Logs accessibles
  - [ ] Performance acceptable
  - [ ] Smoke tests réussis

### Rollback Plan

En cas de problème :

1. **Arrêt immédiat** du déploiement
2. **Restoration** depuis backup
3. **Rollback** vers version précédente
4. **Analyse post-mortem** et corrections

---

**Version**: 2.0.0  
**Dernière mise à jour**: 2024-12-21  
**Platforms supportées**: Docker, Kubernetes, AWS ECS, GCP Cloud Run  
**Support déploiement**: deploy-support@scrapinium.com