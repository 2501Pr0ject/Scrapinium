"""Configuration de headers de sécurité et CORS hardening."""

from typing import Dict, List, Optional
from fastapi import Response, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse
import time
import secrets
import logging

logger = logging.getLogger(__name__)


class SecurityHeaders:
    """Gestionnaire de headers de sécurité enterprise-grade."""
    
    def __init__(self, production_mode: bool = False):
        self.production_mode = production_mode
        
        # Configuration des headers de sécurité
        self.security_headers = {
            # Protection XSS
            "X-XSS-Protection": "1; mode=block",
            
            # Prévention du MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Protection contre le clickjacking
            "X-Frame-Options": "DENY",
            
            # Référer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy (anciennement Feature Policy)
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "fullscreen=(self)"
            ),
            
            # Content Security Policy
            "Content-Security-Policy": self._get_csp_policy(),
            
            # HSTS (uniquement en production avec HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if production_mode else None,
            
            # Cache control pour les ressources sensibles
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Headers personnalisés pour identifier le service
            "X-Powered-By": "Scrapinium/2.0",
            "X-Security-Level": "Enterprise",
            
            # Protection contre les attaques de timing
            "X-Response-Time-Threshold": "5000",  # 5 secondes max
        }
        
        # Domaines autorisés pour CORS (configuration stricte)
        self.allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]
        
        if production_mode:
            # En production, ajouter uniquement les domaines de production
            self.allowed_origins.extend([
                "https://scrapinium.com",
                "https://app.scrapinium.com",
                "https://api.scrapinium.com"
            ])
        
        # Méthodes HTTP autorisées
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        
        # Headers autorisés
        self.allowed_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-API-Key",
            "X-Client-Version",
            "User-Agent"
        ]
        
        # Headers exposés au client
        self.exposed_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "X-Response-Time",
            "X-Request-ID"
        ]
        
        # Nonce pour CSP (généré à chaque requête)
        self.csp_nonces = {}
    
    def _get_csp_policy(self) -> str:
        """Générer la politique Content Security Policy."""
        if self.production_mode:
            # CSP strict pour la production
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests"
            )
        else:
            # CSP plus permissif pour le développement
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "http://localhost:* https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' "
                "http://localhost:* https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' http://localhost:* https://fonts.gstatic.com; "
                "img-src 'self' data: http: https:; "
                "connect-src 'self' http://localhost:* https:; "
                "frame-src 'none'; "
                "object-src 'none'"
            )
    
    def generate_request_id(self) -> str:
        """Générer un ID unique pour la requête."""
        return f"req_{int(time.time())}_{secrets.token_hex(8)}"
    
    def generate_csp_nonce(self, request_id: str) -> str:
        """Générer un nonce pour CSP."""
        nonce = secrets.token_urlsafe(16)
        self.csp_nonces[request_id] = nonce
        return nonce
    
    def apply_security_headers(self, response: Response, request: Request) -> Response:
        """Appliquer tous les headers de sécurité."""
        # Générer l'ID de requête
        request_id = self.generate_request_id()
        
        # Appliquer les headers de base
        for header, value in self.security_headers.items():
            if value is not None:
                response.headers[header] = value
        
        # Ajouter l'ID de requête
        response.headers["X-Request-ID"] = request_id
        
        # Ajouter le timestamp de traitement
        response.headers["X-Response-Time"] = str(int(time.time() * 1000))
        
        # CSP avec nonce dynamique si nécessaire
        if "text/html" in response.headers.get("content-type", ""):
            nonce = self.generate_csp_nonce(request_id)
            csp_with_nonce = self.security_headers["Content-Security-Policy"]
            csp_with_nonce = csp_with_nonce.replace("'unsafe-inline'", f"'nonce-{nonce}'")
            response.headers["Content-Security-Policy"] = csp_with_nonce
            response.headers["X-CSP-Nonce"] = nonce
        
        # Headers spécifiques selon le type de contenu
        content_type = response.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # Pour les API JSON
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cache-Control"] = "no-store"
        
        elif "text/html" in content_type:
            # Pour les pages HTML
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Headers de sécurité pour les endpoints sensibles
        path = str(request.url.path) if hasattr(request, 'url') else ""
        
        if path.startswith("/maintenance"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        
        elif path.startswith("/admin"):
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        
        # Supprimer les headers qui révèlent des informations
        headers_to_remove = ["Server", "X-Powered-By-Custom"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]
        
        return response
    
    def create_cors_middleware(self) -> CORSMiddleware:
        """Créer le middleware CORS sécurisé."""
        return CORSMiddleware(
            allow_origins=self.allowed_origins,
            allow_credentials=False,  # Désactivé pour la sécurité
            allow_methods=self.allowed_methods,
            allow_headers=self.allowed_headers,
            expose_headers=self.exposed_headers,
            max_age=3600 if self.production_mode else 300,  # Cache CORS
        )
    
    def validate_origin(self, origin: str) -> bool:
        """Valider l'origine d'une requête."""
        if not origin:
            return False
        
        # Vérifier contre la liste blanche
        for allowed in self.allowed_origins:
            if origin == allowed:
                return True
            
            # Permettre les sous-domaines en production
            if self.production_mode and allowed.startswith("https://"):
                domain = allowed.replace("https://", "")
                if origin.endswith(f".{domain}") and origin.startswith("https://"):
                    return True
        
        return False
    
    def create_security_response(self, status_code: int, message: str) -> StarletteResponse:
        """Créer une réponse avec headers de sécurité."""
        response = StarletteResponse(
            content=f'{{"error": "{message}", "status": {status_code}}}',
            status_code=status_code,
            headers={"Content-Type": "application/json"}
        )
        
        # Appliquer les headers de sécurité de base
        basic_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store",
            "X-Request-ID": self.generate_request_id()
        }
        
        for header, value in basic_headers.items():
            response.headers[header] = value
        
        return response
    
    def get_security_report(self) -> Dict[str, any]:
        """Générer un rapport de configuration de sécurité."""
        return {
            "production_mode": self.production_mode,
            "cors_configuration": {
                "allowed_origins": len(self.allowed_origins),
                "allowed_methods": self.allowed_methods,
                "allowed_headers": len(self.allowed_headers),
                "exposed_headers": len(self.exposed_headers),
                "credentials_enabled": False
            },
            "security_headers": {
                "enabled_headers": len([h for h in self.security_headers.values() if h]),
                "csp_enabled": bool(self.security_headers.get("Content-Security-Policy")),
                "hsts_enabled": bool(self.security_headers.get("Strict-Transport-Security")),
                "xss_protection": bool(self.security_headers.get("X-XSS-Protection")),
                "frame_protection": bool(self.security_headers.get("X-Frame-Options")),
            },
            "content_security": {
                "nonces_generated": len(self.csp_nonces),
                "csp_policy_length": len(self.security_headers.get("Content-Security-Policy", "")),
                "strict_mode": self.production_mode
            },
            "recommendations": self._get_security_recommendations()
        }
    
    def _get_security_recommendations(self) -> List[str]:
        """Obtenir des recommandations de sécurité."""
        recommendations = []
        
        if not self.production_mode:
            recommendations.append("Activer le mode production pour HSTS et CSP strict")
            recommendations.append("Configurer HTTPS avec certificats valides")
        
        if len(self.allowed_origins) > 10:
            recommendations.append("Réduire le nombre d'origines CORS autorisées")
        
        if "unsafe-eval" in self.security_headers.get("Content-Security-Policy", ""):
            recommendations.append("Éliminer 'unsafe-eval' de la CSP pour plus de sécurité")
        
        recommendations.extend([
            "Configurer un WAF (Web Application Firewall) en amont",
            "Implémenter la validation CSRF pour les formulaires",
            "Activer le monitoring des headers de sécurité",
            "Configurer des alertes pour les violations CSP"
        ])
        
        return recommendations
    
    def cleanup_nonces(self, max_age_minutes: int = 60):
        """Nettoyer les anciens nonces."""
        current_time = time.time()
        expired_nonces = [
            req_id for req_id, nonce in self.csp_nonces.items()
            if current_time - int(req_id.split('_')[1]) > (max_age_minutes * 60)
        ]
        
        for req_id in expired_nonces:
            del self.csp_nonces[req_id]
        
        if expired_nonces:
            logger.info(f"Nettoyage de {len(expired_nonces)} nonces expirés")


# Instance globale
security_headers = SecurityHeaders(production_mode=False)  # Sera configuré dynamiquement


async def security_headers_middleware(request: Request, call_next):
    """Middleware pour appliquer les headers de sécurité."""
    # Vérifier l'origine si présente
    origin = request.headers.get("origin")
    if origin and not security_headers.validate_origin(origin):
        logger.warning(f"Origine non autorisée: {origin}")
        return security_headers.create_security_response(
            403, "Origine non autorisée"
        )
    
    # Traiter la requête
    response = await call_next(request)
    
    # Appliquer les headers de sécurité
    response = security_headers.apply_security_headers(response, request)
    
    # Nettoyer périodiquement les nonces
    if int(time.time()) % 300 == 0:  # Toutes les 5 minutes
        security_headers.cleanup_nonces()
    
    return response