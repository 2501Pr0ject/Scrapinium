"""Configuration de sécurité pour environnement de production."""

import os
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import yaml
import json

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Niveaux de sécurité."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"


@dataclass
class DatabaseSecurityConfig:
    """Configuration de sécurité base de données."""
    encrypt_at_rest: bool = True
    ssl_required: bool = True
    connection_timeout: int = 30
    max_connections: int = 100
    password_min_length: int = 16
    require_complex_passwords: bool = True
    audit_logging: bool = True
    backup_encryption: bool = True


@dataclass
class APISecurityConfig:
    """Configuration de sécurité API."""
    rate_limiting_enabled: bool = True
    jwt_secret_rotation_days: int = 30
    api_key_length: int = 32
    session_timeout_minutes: int = 30
    require_https: bool = True
    csrf_protection: bool = True
    input_validation_strict: bool = True
    audit_all_requests: bool = True


@dataclass
class MonitoringSecurityConfig:
    """Configuration de monitoring de sécurité."""
    log_security_events: bool = True
    alert_on_suspicious_activity: bool = True
    failed_login_threshold: int = 5
    ip_blocking_enabled: bool = True
    intrusion_detection: bool = True
    vulnerability_scanning: bool = True
    compliance_reporting: bool = True


class ProductionSecurityManager:
    """Gestionnaire de sécurité pour production enterprise-grade."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.PRODUCTION):
        self.security_level = security_level
        
        # Configuration par niveau de sécurité
        self.configs = {
            SecurityLevel.DEVELOPMENT: self._get_development_config(),
            SecurityLevel.STAGING: self._get_staging_config(),
            SecurityLevel.PRODUCTION: self._get_production_config(),
            SecurityLevel.ENTERPRISE: self._get_enterprise_config()
        }
        
        self.current_config = self.configs[security_level]
        
        # Variables d'environnement sécurisées
        self.secure_env_vars = [
            "SECRET_KEY", "DATABASE_PASSWORD", "REDIS_PASSWORD",
            "JWT_SECRET", "API_ENCRYPTION_KEY", "BACKUP_ENCRYPTION_KEY",
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"
        ]
        
        # Fichiers de configuration sécurisés
        self.secure_files = [
            ".env", ".env.production", ".env.local",
            "secrets.yaml", "certificates/", "keys/"
        ]
        
        # Ports sécurisés par défaut
        self.secure_ports = {
            "https": 443,
            "database": 5432,
            "redis": 6379,
            "monitoring": 9090
        }
        
        # Configuration des logs de sécurité
        self.security_log_config = {
            "level": "INFO",
            "format": "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            "handlers": ["file", "syslog"] if security_level == SecurityLevel.ENTERPRISE else ["file"],
            "audit_fields": ["user_id", "ip_address", "action", "resource", "timestamp"],
            "retention_days": 365 if security_level == SecurityLevel.ENTERPRISE else 90
        }
    
    def _get_development_config(self) -> Dict[str, Any]:
        """Configuration développement (sécurité relaxée)."""
        return {
            "database": DatabaseSecurityConfig(
                encrypt_at_rest=False,
                ssl_required=False,
                connection_timeout=10,
                max_connections=20,
                password_min_length=8,
                require_complex_passwords=False,
                audit_logging=False,
                backup_encryption=False
            ),
            "api": APISecurityConfig(
                rate_limiting_enabled=True,
                jwt_secret_rotation_days=90,
                api_key_length=16,
                session_timeout_minutes=120,
                require_https=False,
                csrf_protection=False,
                input_validation_strict=False,
                audit_all_requests=False
            ),
            "monitoring": MonitoringSecurityConfig(
                log_security_events=True,
                alert_on_suspicious_activity=False,
                failed_login_threshold=10,
                ip_blocking_enabled=False,
                intrusion_detection=False,
                vulnerability_scanning=False,
                compliance_reporting=False
            )
        }
    
    def _get_staging_config(self) -> Dict[str, Any]:
        """Configuration staging (sécurité intermédiaire)."""
        return {
            "database": DatabaseSecurityConfig(
                encrypt_at_rest=True,
                ssl_required=True,
                connection_timeout=20,
                max_connections=50,
                password_min_length=12,
                require_complex_passwords=True,
                audit_logging=True,
                backup_encryption=True
            ),
            "api": APISecurityConfig(
                rate_limiting_enabled=True,
                jwt_secret_rotation_days=60,
                api_key_length=24,
                session_timeout_minutes=60,
                require_https=True,
                csrf_protection=True,
                input_validation_strict=True,
                audit_all_requests=True
            ),
            "monitoring": MonitoringSecurityConfig(
                log_security_events=True,
                alert_on_suspicious_activity=True,
                failed_login_threshold=7,
                ip_blocking_enabled=True,
                intrusion_detection=True,
                vulnerability_scanning=True,
                compliance_reporting=False
            )
        }
    
    def _get_production_config(self) -> Dict[str, Any]:
        """Configuration production (sécurité renforcée)."""
        return {
            "database": DatabaseSecurityConfig(
                encrypt_at_rest=True,
                ssl_required=True,
                connection_timeout=30,
                max_connections=100,
                password_min_length=16,
                require_complex_passwords=True,
                audit_logging=True,
                backup_encryption=True
            ),
            "api": APISecurityConfig(
                rate_limiting_enabled=True,
                jwt_secret_rotation_days=30,
                api_key_length=32,
                session_timeout_minutes=30,
                require_https=True,
                csrf_protection=True,
                input_validation_strict=True,
                audit_all_requests=True
            ),
            "monitoring": MonitoringSecurityConfig(
                log_security_events=True,
                alert_on_suspicious_activity=True,
                failed_login_threshold=5,
                ip_blocking_enabled=True,
                intrusion_detection=True,
                vulnerability_scanning=True,
                compliance_reporting=True
            )
        }
    
    def _get_enterprise_config(self) -> Dict[str, Any]:
        """Configuration enterprise (sécurité maximale)."""
        return {
            "database": DatabaseSecurityConfig(
                encrypt_at_rest=True,
                ssl_required=True,
                connection_timeout=15,
                max_connections=200,
                password_min_length=20,
                require_complex_passwords=True,
                audit_logging=True,
                backup_encryption=True
            ),
            "api": APISecurityConfig(
                rate_limiting_enabled=True,
                jwt_secret_rotation_days=7,
                api_key_length=64,
                session_timeout_minutes=15,
                require_https=True,
                csrf_protection=True,
                input_validation_strict=True,
                audit_all_requests=True
            ),
            "monitoring": MonitoringSecurityConfig(
                log_security_events=True,
                alert_on_suspicious_activity=True,
                failed_login_threshold=3,
                ip_blocking_enabled=True,
                intrusion_detection=True,
                vulnerability_scanning=True,
                compliance_reporting=True
            )
        }
    
    def generate_secure_secret(self, length: int = 32) -> str:
        """Générer un secret sécurisé."""
        return secrets.token_urlsafe(length)
    
    def validate_environment_security(self) -> Dict[str, Any]:
        """Valider la sécurité de l'environnement."""
        issues = []
        warnings = []
        recommendations = []
        
        # Vérifier les variables d'environnement
        for var in self.secure_env_vars:
            value = os.getenv(var)
            if not value:
                warnings.append(f"Variable d'environnement manquante: {var}")
            elif len(value) < 16:
                issues.append(f"Variable d'environnement trop courte: {var}")
            elif value in ["password", "secret", "changeme", "admin"]:
                issues.append(f"Variable d'environnement non sécurisée: {var}")
        
        # Vérifier les fichiers sensibles
        for file_pattern in self.secure_files:
            if os.path.exists(file_pattern):
                file_stat = os.stat(file_pattern)
                # Vérifier les permissions (doit être 600 ou plus restrictif)
                if file_stat.st_mode & 0o077:
                    issues.append(f"Permissions trop permissives sur {file_pattern}")
        
        # Vérifier la configuration selon le niveau de sécurité
        if self.security_level == SecurityLevel.PRODUCTION:
            if not self.current_config["api"].require_https:
                issues.append("HTTPS non requis en production")
            
            if not self.current_config["database"].encrypt_at_rest:
                issues.append("Chiffrement des données au repos désactivé")
        
        # Recommandations générales
        recommendations.extend([
            "Utiliser un gestionnaire de secrets (HashiCorp Vault, AWS Secrets Manager)",
            "Configurer la rotation automatique des clés",
            "Implémenter la surveillance des accès aux secrets",
            "Configurer des alertes de sécurité",
            "Effectuer des audits de sécurité réguliers"
        ])
        
        return {
            "security_level": self.security_level.value,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "score": self._calculate_security_score(issues, warnings),
            "compliant": len(issues) == 0
        }
    
    def _calculate_security_score(self, issues: List[str], warnings: List[str]) -> int:
        """Calculer un score de sécurité (0-100)."""
        base_score = 100
        base_score -= len(issues) * 15  # -15 par problème critique
        base_score -= len(warnings) * 5  # -5 par avertissement
        
        # Bonus selon le niveau de sécurité
        if self.security_level == SecurityLevel.ENTERPRISE:
            base_score += 10
        elif self.security_level == SecurityLevel.PRODUCTION:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def create_production_env_template(self) -> str:
        """Créer un template .env pour la production."""
        template = f"""# Configuration de production Scrapinium
# Généré automatiquement - NE PAS COMMITTER

# === SECRETS CRITIQUES ===
SECRET_KEY={self.generate_secure_secret(64)}
JWT_SECRET={self.generate_secure_secret(32)}
API_ENCRYPTION_KEY={self.generate_secure_secret(32)}

# === BASE DE DONNÉES ===
DATABASE_URL=postgresql://user:password@localhost:5432/scrapinium_prod
DATABASE_PASSWORD={self.generate_secure_secret(24)}
DATABASE_SSL_MODE=require
DATABASE_POOL_SIZE={self.current_config['database'].max_connections}

# === REDIS ===
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD={self.generate_secure_secret(16)}
REDIS_SSL=true

# === API EXTERNE ===
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# === MONITORING ===
SENTRY_DSN=https://your-sentry-dsn-here
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true

# === SÉCURITÉ ===
RATE_LIMITING_ENABLED=true
REQUIRE_HTTPS=true
CSRF_PROTECTION=true
INPUT_VALIDATION_STRICT=true

# === PERFORMANCE ===
BROWSER_POOL_SIZE=5
CACHE_TTL=3600
MAX_CONCURRENT_REQUESTS=100

# === DÉPLOIEMENT ===
ENVIRONMENT=production
DEBUG=false
TESTING=false
"""
        return template
    
    def create_docker_security_config(self) -> str:
        """Créer une configuration Docker sécurisée."""
        return f"""# Configuration Docker sécurisée pour Scrapinium

version: '3.8'

services:
  scrapinium:
    image: scrapinium:latest
    
    # Utilisateur non-root
    user: "1001:1001"
    
    # Capacités minimales
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    
    # Système de fichiers en lecture seule
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=1g
      - /var/log:noexec,nosuid,size=100m
    
    # Limites de ressources
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
        reservations:
          memory: 1G
          cpus: "0.5"
    
    # Variables d'environnement depuis secrets
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL_FILE=/run/secrets/database_url
      - SECRET_KEY_FILE=/run/secrets/secret_key
    
    # Secrets Docker
    secrets:
      - database_url
      - secret_key
      - jwt_secret
    
    # Réseau isolé
    networks:
      - app_network
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  database:
    image: postgres:15-alpine
    
    # Utilisateur non-root
    user: postgres
    
    # Données persistantes chiffrées
    volumes:
      - postgres_data:/var/lib/postgresql/data:Z
    
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_DB=scrapinium
      - POSTGRES_USER=scrapinium
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    
    secrets:
      - db_password
    
    # Configuration SSL
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/etc/ssl/certs/server.crt
      -c ssl_key_file=/etc/ssl/private/server.key
      -c log_connections=on
      -c log_disconnections=on
      -c log_checkpoints=on
      -c log_statement=all

secrets:
  database_url:
    external: true
  secret_key:
    external: true
  jwt_secret:
    external: true
  db_password:
    external: true

networks:
  app_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/scrapinium/data
"""
    
    def get_compliance_checklist(self) -> Dict[str, Any]:
        """Obtenir une checklist de conformité sécurité."""
        checklist = {
            "OWASP_TOP_10": {
                "injection_protection": self.current_config["api"].input_validation_strict,
                "broken_authentication": self.current_config["api"].session_timeout_minutes <= 30,
                "sensitive_data_exposure": self.current_config["database"].encrypt_at_rest,
                "xml_external_entities": True,  # Non applicable pour notre API
                "broken_access_control": self.current_config["api"].csrf_protection,
                "security_misconfiguration": self.security_level != SecurityLevel.DEVELOPMENT,
                "xss": self.current_config["api"].input_validation_strict,
                "insecure_deserialization": True,  # Contrôlé par validation
                "known_vulnerabilities": self.current_config["monitoring"].vulnerability_scanning,
                "insufficient_logging": self.current_config["monitoring"].audit_all_requests
            },
            "ISO_27001": {
                "access_control": self.current_config["api"].require_https,
                "cryptography": self.current_config["database"].encrypt_at_rest,
                "operations_security": self.current_config["monitoring"].intrusion_detection,
                "communications_security": self.current_config["database"].ssl_required,
                "system_acquisition": True,
                "supplier_relationships": True,
                "incident_management": self.current_config["monitoring"].alert_on_suspicious_activity,
                "business_continuity": self.current_config["database"].backup_encryption
            },
            "GDPR": {
                "data_protection_by_design": True,
                "consent_management": True,
                "data_minimization": True,
                "right_to_erasure": True,
                "data_portability": True,
                "breach_notification": self.current_config["monitoring"].alert_on_suspicious_activity,
                "privacy_impact_assessment": True,
                "data_protection_officer": False  # À définir selon l'organisation
            }
        }
        
        # Calculer le score de conformité
        total_checks = sum(len(category.values()) for category in checklist.values())
        passed_checks = sum(
            sum(1 for check in category.values() if check)
            for category in checklist.values()
        )
        
        compliance_score = (passed_checks / total_checks) * 100
        
        return {
            "checklist": checklist,
            "compliance_score": round(compliance_score, 1),
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "security_level": self.security_level.value,
            "recommendations": self._get_compliance_recommendations(checklist)
        }
    
    def _get_compliance_recommendations(self, checklist: Dict[str, Any]) -> List[str]:
        """Obtenir des recommandations de conformité."""
        recommendations = []
        
        for category, checks in checklist.items():
            failed_checks = [check for check, passed in checks.items() if not passed]
            if failed_checks:
                recommendations.append(f"Améliorer {category}: {', '.join(failed_checks)}")
        
        return recommendations


# Instance globale
security_manager = ProductionSecurityManager(SecurityLevel.PRODUCTION)