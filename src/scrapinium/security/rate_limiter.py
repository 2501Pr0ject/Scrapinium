"""Système de rate limiting et protection DoS enterprise-grade."""

import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib
import logging
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.responses import Response

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """Règle de rate limiting."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10  # Limite de burst sur 10 secondes
    block_duration_minutes: int = 15  # Durée de blocage


@dataclass
class ClientStats:
    """Statistiques d'un client."""
    total_requests: int = 0
    blocked_requests: int = 0
    last_request_time: float = field(default_factory=time.time)
    first_request_time: float = field(default_factory=time.time)
    minute_requests: deque = field(default_factory=lambda: deque(maxlen=60))
    hour_requests: deque = field(default_factory=lambda: deque(maxlen=60))
    day_requests: deque = field(default_factory=lambda: deque(maxlen=24))
    burst_requests: deque = field(default_factory=lambda: deque(maxlen=10))
    blocked_until: Optional[float] = None
    abuse_score: float = 0.0
    user_agent: Optional[str] = None
    country: Optional[str] = None


class AdvancedRateLimiter:
    """Rate limiter avancé avec protection DoS."""
    
    def __init__(self):
        self.clients: Dict[str, ClientStats] = {}
        self.rules: Dict[str, RateLimitRule] = {
            "default": RateLimitRule(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=10,
                block_duration_minutes=15
            ),
            "scraping": RateLimitRule(
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_limit=5,
                block_duration_minutes=30
            ),
            "maintenance": RateLimitRule(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                burst_limit=2,
                block_duration_minutes=60
            )
        }
        self.blocked_ips: Dict[str, float] = {}
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
        
        # Configuration de sécurité
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_url_length = 2048
        self.max_header_size = 8192
        self.suspicious_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zgrab",
            "python-requests/", "curl/", "wget/", "bot"
        ]
        
        # Patterns d'attaque
        self.attack_patterns = [
            "union select", "drop table", "insert into",
            "<script>", "javascript:", "eval(",
            "../", "etc/passwd", "cmd.exe",
            "or 1=1", "' or '1'='1", "admin'--"
        ]
    
    def get_client_id(self, request: Request) -> str:
        """Générer un ID client unique."""
        # Priorité à l'IP forwarded, sinon IP client
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip") or
            getattr(request.client, "host", "unknown")
        )
        
        # Inclure User-Agent pour détecter les bots
        user_agent = request.headers.get("user-agent", "")
        
        # Hash pour anonymiser tout en gardant l'unicité
        unique_string = f"{client_ip}:{user_agent[:50]}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def get_rule_for_endpoint(self, path: str) -> RateLimitRule:
        """Obtenir la règle de rate limiting pour un endpoint."""
        if path.startswith("/scrape"):
            return self.rules["scraping"]
        elif path.startswith("/maintenance"):
            return self.rules["maintenance"]
        else:
            return self.rules["default"]
    
    def cleanup_old_records(self):
        """Nettoyer les anciens enregistrements."""
        current_time = time.time()
        
        # Nettoyer les clients inactifs (plus de 24h)
        inactive_threshold = current_time - (24 * 3600)
        clients_to_remove = [
            client_id for client_id, stats in self.clients.items()
            if stats.last_request_time < inactive_threshold
        ]
        
        for client_id in clients_to_remove:
            del self.clients[client_id]
        
        # Nettoyer les IPs bloquées expirées
        expired_blocks = [
            ip for ip, block_until in self.blocked_ips.items()
            if current_time > block_until
        ]
        
        for ip in expired_blocks:
            del self.blocked_ips[ip]
            
        logger.info(f"Nettoyage: {len(clients_to_remove)} clients inactifs, {len(expired_blocks)} blocks expirés")
    
    def detect_suspicious_activity(self, request: Request, client_stats: ClientStats) -> float:
        """Détecter une activité suspecte et calculer un score d'abus."""
        suspicion_score = 0.0
        
        # Vérifier User-Agent suspect
        user_agent = request.headers.get("user-agent", "").lower()
        client_stats.user_agent = user_agent
        
        for suspicious_ua in self.suspicious_user_agents:
            if suspicious_ua in user_agent:
                suspicion_score += 2.0
                break
        
        # User-Agent manquant ou trop court
        if not user_agent or len(user_agent) < 10:
            suspicion_score += 1.5
        
        # Vérifier les patterns d'attaque dans l'URL et les paramètres
        url_str = str(request.url).lower()
        for pattern in self.attack_patterns:
            if pattern in url_str:
                suspicion_score += 5.0
                logger.warning(f"Pattern d'attaque détecté: {pattern} dans {url_str[:100]}")
        
        # Vérifier la taille des headers
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > self.max_header_size:
            suspicion_score += 3.0
        
        # Vérifier la longueur de l'URL
        if len(str(request.url)) > self.max_url_length:
            suspicion_score += 2.0
        
        # Analyser le pattern de requêtes (trop régulier = bot)
        if len(client_stats.minute_requests) > 10:
            intervals = []
            requests_list = list(client_stats.minute_requests)
            for i in range(1, len(requests_list)):
                interval = requests_list[i] - requests_list[i-1]
                intervals.append(interval)
            
            if intervals:
                # Variance faible = requêtes trop régulières (bot)
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                if variance < 0.1 and avg_interval < 5:  # Requêtes très régulières et rapides
                    suspicion_score += 2.0
        
        # Mise à jour du score d'abus (moyenne mobile)
        client_stats.abuse_score = (client_stats.abuse_score * 0.8) + (suspicion_score * 0.2)
        
        return client_stats.abuse_score
    
    def is_rate_limited(self, client_id: str, rule: RateLimitRule) -> Tuple[bool, str, int]:
        """Vérifier si le client dépasse les limites."""
        if client_id not in self.clients:
            self.clients[client_id] = ClientStats()
        
        stats = self.clients[client_id]
        current_time = time.time()
        
        # Vérifier si le client est bloqué
        if stats.blocked_until and current_time < stats.blocked_until:
            remaining = int(stats.blocked_until - current_time)
            return True, f"Client bloqué pour {remaining}s", remaining
        
        # Nettoyer les anciennes requêtes
        current_minute = int(current_time / 60)
        current_hour = int(current_time / 3600)
        current_day = int(current_time / 86400)
        
        # Minute (glissante)
        stats.minute_requests = deque([
            req_time for req_time in stats.minute_requests
            if current_time - req_time < 60
        ], maxlen=60)
        
        # Heure (par heure entière)
        stats.hour_requests = deque([
            hour for hour in stats.hour_requests
            if current_hour - hour < 1
        ], maxlen=60)
        
        # Jour (par jour entier)
        stats.day_requests = deque([
            day for day in stats.day_requests
            if current_day - day < 1
        ], maxlen=24)
        
        # Burst (10 dernières secondes)
        stats.burst_requests = deque([
            req_time for req_time in stats.burst_requests
            if current_time - req_time < 10
        ], maxlen=10)
        
        # Vérifier les limites
        if len(stats.minute_requests) >= rule.requests_per_minute:
            self._block_client(client_id, rule.block_duration_minutes)
            return True, "Limite par minute dépassée", rule.block_duration_minutes * 60
        
        if len([h for h in stats.hour_requests if h == current_hour]) >= rule.requests_per_hour:
            self._block_client(client_id, rule.block_duration_minutes)
            return True, "Limite par heure dépassée", rule.block_duration_minutes * 60
        
        if len([d for d in stats.day_requests if d == current_day]) >= rule.requests_per_day:
            self._block_client(client_id, rule.block_duration_minutes * 4)  # Block plus long
            return True, "Limite par jour dépassée", rule.block_duration_minutes * 4 * 60
        
        if len(stats.burst_requests) >= rule.burst_limit:
            self._block_client(client_id, rule.block_duration_minutes // 2)
            return True, "Limite de burst dépassée", (rule.block_duration_minutes // 2) * 60
        
        return False, "", 0
    
    def _block_client(self, client_id: str, duration_minutes: int):
        """Bloquer un client."""
        stats = self.clients[client_id]
        block_until = time.time() + (duration_minutes * 60)
        stats.blocked_until = block_until
        stats.blocked_requests += 1
        
        logger.warning(f"Client {client_id} bloqué pour {duration_minutes} minutes. "
                      f"Total bloquages: {stats.blocked_requests}")
    
    def record_request(self, client_id: str, request: Request):
        """Enregistrer une requête."""
        if client_id not in self.clients:
            self.clients[client_id] = ClientStats()
        
        stats = self.clients[client_id]
        current_time = time.time()
        
        # Mettre à jour les statistiques
        stats.total_requests += 1
        stats.last_request_time = current_time
        stats.minute_requests.append(current_time)
        stats.hour_requests.append(int(current_time / 3600))
        stats.day_requests.append(int(current_time / 86400))
        stats.burst_requests.append(current_time)
        
        # Détecter l'activité suspecte
        suspicion_score = self.detect_suspicious_activity(request, stats)
        
        # Bloquer automatiquement si score trop élevé
        if suspicion_score > 10.0:
            self._block_client(client_id, 60)  # Block 1 heure
            logger.critical(f"Client {client_id} bloqué automatiquement - Score suspicion: {suspicion_score}")
    
    async def check_request_size(self, request: Request) -> bool:
        """Vérifier la taille de la requête."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_request_size:
                    return False
            except ValueError:
                pass
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du rate limiter."""
        current_time = time.time()
        active_clients = len([
            c for c in self.clients.values()
            if current_time - c.last_request_time < 3600
        ])
        
        blocked_clients = len([
            c for c in self.clients.values()
            if c.blocked_until and current_time < c.blocked_until
        ])
        
        total_requests = sum(c.total_requests for c in self.clients.values())
        total_blocked = sum(c.blocked_requests for c in self.clients.values())
        
        top_abusers = sorted(
            [(cid, stats.abuse_score, stats.total_requests) 
             for cid, stats in self.clients.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        return {
            "total_clients": len(self.clients),
            "active_clients_1h": active_clients,
            "blocked_clients": blocked_clients,
            "total_requests": total_requests,
            "total_blocked_requests": total_blocked,
            "block_rate_percent": (total_blocked / max(total_requests, 1)) * 100,
            "rules": {name: {
                "requests_per_minute": rule.requests_per_minute,
                "requests_per_hour": rule.requests_per_hour,
                "requests_per_day": rule.requests_per_day,
                "burst_limit": rule.burst_limit
            } for name, rule in self.rules.items()},
            "top_abusers": [
                {"client_id": cid[:8], "abuse_score": score, "requests": reqs}
                for cid, score, reqs in top_abusers
            ]
        }


# Instance globale
rate_limiter = AdvancedRateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting."""
    start_time = time.time()
    
    # Nettoyer périodiquement
    if int(start_time) % 300 == 0:  # Toutes les 5 minutes
        rate_limiter.cleanup_old_records()
    
    # Vérifier la taille de la requête
    if not await rate_limiter.check_request_size(request):
        raise HTTPException(
            status_code=413,
            detail="Requête trop volumineuse",
            headers={"Retry-After": "3600"}
        )
    
    # Obtenir l'ID client et la règle
    client_id = rate_limiter.get_client_id(request)
    rule = rate_limiter.get_rule_for_endpoint(str(request.url.path))
    
    # Vérifier les limites
    is_limited, reason, retry_after = rate_limiter.is_rate_limited(client_id, rule)
    
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes: {reason}",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(rule.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(start_time + retry_after))
            }
        )
    
    # Enregistrer la requête
    rate_limiter.record_request(client_id, request)
    
    # Continuer le traitement
    response = await call_next(request)
    
    # Ajouter les headers de rate limiting
    stats = rate_limiter.clients.get(client_id)
    if stats:
        remaining = max(0, rule.requests_per_minute - len(stats.minute_requests))
        reset_time = int((int(start_time / 60) + 1) * 60)
        
        response.headers["X-RateLimit-Limit"] = str(rule.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        # Avertir si proche de la limite
        if remaining < rule.requests_per_minute * 0.1:
            response.headers["X-RateLimit-Warning"] = "Approaching rate limit"
    
    return response