"""Module de sécurité enterprise-grade pour Scrapinium."""

from .rate_limiter import rate_limiter, AdvancedRateLimiter, RateLimitRule
from .headers import security_headers, SecurityHeaders
from .input_validator import input_validator, AdvancedInputValidator, ValidationLevel, ValidationResult
from .config_security import security_manager, ProductionSecurityManager, SecurityLevel

__all__ = [
    # Rate Limiting
    "rate_limiter",
    "AdvancedRateLimiter", 
    "RateLimitRule",
    
    # Security Headers
    "security_headers",
    "SecurityHeaders",
    
    # Input Validation
    "input_validator",
    "AdvancedInputValidator",
    "ValidationLevel",
    "ValidationResult",
    
    # Security Configuration
    "security_manager",
    "ProductionSecurityManager",
    "SecurityLevel"
]

# Configuration globale de sécurité
SECURITY_VERSION = "1.0.0"
SECURITY_FEATURES = [
    "Rate Limiting Avancé",
    "Protection DoS/DDoS", 
    "Validation d'Inputs Stricte",
    "Headers de Sécurité",
    "CORS Hardening",
    "Détection d'Intrusion",
    "Audit de Conformité",
    "Configuration Production"
]

def get_security_status():
    """Obtenir le statut global de sécurité."""
    return {
        "version": SECURITY_VERSION,
        "features": SECURITY_FEATURES,
        "rate_limiter": "active",
        "input_validator": input_validator.level.value,
        "security_headers": "enabled",
        "security_level": security_manager.security_level.value,
        "compliance_ready": True
    }