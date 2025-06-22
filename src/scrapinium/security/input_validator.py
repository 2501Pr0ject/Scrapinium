"""Validation renforcée et sanitisation avancée des inputs."""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import ipaddress
from urllib.parse import urlparse
import base64
import json

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Niveaux de validation."""
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class ValidationResult:
    """Résultat de validation."""
    is_valid: bool
    sanitized_value: Any
    errors: List[str]
    warnings: List[str]
    risk_score: float  # 0-10, 10 = très risqué


class AdvancedInputValidator:
    """Validateur d'inputs enterprise-grade."""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.STRICT):
        self.level = level
        self.max_string_length = 10000
        self.max_url_length = 2048
        self.max_json_depth = 10
        self.max_array_length = 1000
        
        # Patterns malveillants détaillés
        self.sql_injection_patterns = [
            r"(?i)(union\s+select|drop\s+table|insert\s+into|delete\s+from)",
            r"(?i)(or\s+\d+\s*=\s*\d+|and\s+\d+\s*=\s*\d+)",
            r"(?i)('|\"|\`)\s*(or|and)\s*('|\"|\`)",
            r"(?i)(exec\s*\(|execute\s*\(|sp_executesql)",
            r"(?i)(xp_cmdshell|sp_oacreate)",
            r"(?i)(information_schema|sys\.tables|sys\.columns)",
            r"(?i)(waitfor\s+delay|benchmark\s*\()",
            r"(?i)(load_file\s*\(|into\s+outfile)",
        ]
        
        self.xss_patterns = [
            r"(?i)<script[^>]*>.*?</script>",
            r"(?i)<iframe[^>]*>.*?</iframe>",
            r"(?i)javascript\s*:",
            r"(?i)vbscript\s*:",
            r"(?i)data\s*:\s*text/html",
            r"(?i)on\w+\s*=",  # onclick, onload, etc.
            r"(?i)<\s*img[^>]+src\s*=\s*[\"']javascript:",
            r"(?i)<\s*svg[^>]*>.*?</svg>",
            r"(?i)eval\s*\(|setTimeout\s*\(|setInterval\s*\(",
            r"(?i)<\s*object[^>]*>|<\s*embed[^>]*>",
        ]
        
        self.path_traversal_patterns = [
            r"\.\.[\\/]",
            r"[\\/]\.\.[\\/]",
            r"\.\.%2f|\.\.%5c",
            r"%2e%2e[\\/]",
            r"etc[\\/]passwd",
            r"windows[\\/]system32",
            r"boot\.ini|autoexec\.bat",
        ]
        
        self.command_injection_patterns = [
            r"(?i)(\||\|\||&|&&|;|`|\$\(|\$\{)",
            r"(?i)(cmd\.exe|powershell|bash|sh|zsh)",
            r"(?i)(nc\s|netcat|wget|curl)\s",
            r"(?i)(echo|cat|ls|dir|type)\s",
            r"(?i)(rm\s|del\s|format\s)",
        ]
        
        self.ldap_injection_patterns = [
            r"\*|\(|\)|\\|/",
            r"(?i)(objectclass=|cn=|uid=)",
        ]
        
        # Protocoles dangereux
        self.dangerous_protocols = [
            "javascript", "vbscript", "data", "file", "ftp",
            "gopher", "ldap", "dict", "telnet", "ssh"
        ]
        
        # Domaines et IPs à bloquer
        self.blocked_domains = [
            "localhost", "127.0.0.1", "0.0.0.0", "::1",
            "169.254.0.0/16",  # Link-local
            "10.0.0.0/8",      # Private networks
            "172.16.0.0/12",
            "192.168.0.0/16",
        ]
        
        # Extensions de fichiers dangereuses
        self.dangerous_extensions = [
            ".exe", ".bat", ".cmd", ".com", ".scr", ".pif",
            ".jar", ".jsp", ".asp", ".aspx", ".php", ".py",
            ".pl", ".sh", ".ps1", ".vbs", ".js"
        ]
    
    def sanitize_string(self, value: str, max_length: Optional[int] = None) -> str:
        """Sanitiser une chaîne de caractères."""
        if not isinstance(value, str):
            value = str(value)
        
        # Décoder les entités HTML
        value = html.unescape(value)
        
        # Décoder l'URL
        try:
            value = urllib.parse.unquote(value)
        except:
            pass
        
        # Supprimer les caractères de contrôle
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Limiter la longueur
        max_len = max_length or self.max_string_length
        if len(value) > max_len:
            value = value[:max_len]
            logger.warning(f"Chaîne tronquée à {max_len} caractères")
        
        # Échapper les caractères HTML
        value = html.escape(value, quote=True)
        
        return value.strip()
    
    def validate_url(self, url: str) -> ValidationResult:
        """Valider une URL de manière stricte."""
        errors = []
        warnings = []
        risk_score = 0.0
        
        try:
            # Sanitiser d'abord
            sanitized_url = self.sanitize_string(url, self.max_url_length)
            
            # Vérifier la longueur
            if len(sanitized_url) > self.max_url_length:
                errors.append(f"URL trop longue (max {self.max_url_length})")
                risk_score += 2.0
            
            # Parser l'URL
            parsed = urlparse(sanitized_url)
            
            # Vérifier le protocole
            if not parsed.scheme:
                errors.append("Protocole manquant")
                risk_score += 3.0
            elif parsed.scheme.lower() not in ["http", "https"]:
                if parsed.scheme.lower() in self.dangerous_protocols:
                    errors.append(f"Protocole dangereux: {parsed.scheme}")
                    risk_score += 8.0
                else:
                    warnings.append(f"Protocole non standard: {parsed.scheme}")
                    risk_score += 1.0
            
            # Vérifier le domaine
            if not parsed.netloc:
                errors.append("Domaine manquant")
                risk_score += 3.0
            else:
                # Vérifier contre les domaines bloqués
                domain = parsed.netloc.lower()
                for blocked in self.blocked_domains:
                    if "/" in blocked:  # CIDR
                        try:
                            if ipaddress.ip_address(domain) in ipaddress.ip_network(blocked):
                                errors.append(f"IP bloquée: {domain}")
                                risk_score += 5.0
                        except:
                            pass
                    elif domain == blocked or domain.endswith(f".{blocked}"):
                        errors.append(f"Domaine bloqué: {domain}")
                        risk_score += 5.0
                
                # Vérifier si c'est une IP privée
                try:
                    ip = ipaddress.ip_address(domain)
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        errors.append(f"IP privée/locale non autorisée: {ip}")
                        risk_score += 6.0
                except:
                    pass
            
            # Vérifier le chemin pour path traversal
            if parsed.path:
                for pattern in self.path_traversal_patterns:
                    if re.search(pattern, parsed.path):
                        errors.append("Tentative de path traversal détectée")
                        risk_score += 7.0
                        break
            
            # Vérifier les paramètres de requête
            if parsed.query:
                for pattern in self.sql_injection_patterns + self.xss_patterns:
                    if re.search(pattern, parsed.query):
                        errors.append("Pattern d'injection détecté dans les paramètres")
                        risk_score += 6.0
                        break
            
            # Vérifier l'extension de fichier
            if parsed.path:
                for ext in self.dangerous_extensions:
                    if parsed.path.lower().endswith(ext):
                        warnings.append(f"Extension potentiellement dangereuse: {ext}")
                        risk_score += 2.0
                        break
        
        except Exception as e:
            errors.append(f"Erreur de parsing URL: {str(e)}")
            risk_score += 5.0
            sanitized_url = ""
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized_url if len(errors) == 0 else "",
            errors=errors,
            warnings=warnings,
            risk_score=min(risk_score, 10.0)
        )
    
    def validate_json_payload(self, payload: Dict[str, Any]) -> ValidationResult:
        """Valider un payload JSON."""
        errors = []
        warnings = []
        risk_score = 0.0
        sanitized_payload = {}
        
        try:
            # Vérifier la profondeur
            if self._get_json_depth(payload) > self.max_json_depth:
                errors.append(f"JSON trop profond (max {self.max_json_depth})")
                risk_score += 3.0
            
            # Valider récursivement
            sanitized_payload = self._validate_json_recursive(
                payload, errors, warnings, risk_score
            )
            
        except Exception as e:
            errors.append(f"Erreur de validation JSON: {str(e)}")
            risk_score += 5.0
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized_payload,
            errors=errors,
            warnings=warnings,
            risk_score=min(risk_score, 10.0)
        )
    
    def _validate_json_recursive(self, obj: Any, errors: List[str], warnings: List[str], risk_score: float) -> Any:
        """Valider récursivement un objet JSON."""
        if isinstance(obj, dict):
            sanitized = {}
            for key, value in obj.items():
                # Valider la clé
                if not isinstance(key, str):
                    warnings.append(f"Clé non-string convertie: {key}")
                    key = str(key)
                
                # Sanitiser la clé
                sanitized_key = self.sanitize_string(key, 100)
                if sanitized_key != key:
                    warnings.append(f"Clé sanitisée: {key} -> {sanitized_key}")
                
                # Valider la valeur
                sanitized[sanitized_key] = self._validate_json_recursive(
                    value, errors, warnings, risk_score
                )
            
            return sanitized
        
        elif isinstance(obj, list):
            if len(obj) > self.max_array_length:
                errors.append(f"Array trop long (max {self.max_array_length})")
                obj = obj[:self.max_array_length]
            
            return [
                self._validate_json_recursive(item, errors, warnings, risk_score)
                for item in obj
            ]
        
        elif isinstance(obj, str):
            # Vérifier les patterns d'injection
            risk_found = False
            for pattern_group, group_name in [
                (self.sql_injection_patterns, "SQL injection"),
                (self.xss_patterns, "XSS"),
                (self.command_injection_patterns, "Command injection"),
                (self.ldap_injection_patterns, "LDAP injection")
            ]:
                for pattern in pattern_group:
                    if re.search(pattern, obj):
                        errors.append(f"Pattern {group_name} détecté: {pattern}")
                        risk_found = True
                        break
                if risk_found:
                    break
            
            return self.sanitize_string(obj)
        
        else:
            return obj
    
    def _get_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculer la profondeur d'un objet JSON."""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(value, current_depth + 1)
                for value in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_json_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth
    
    def validate_user_agent(self, user_agent: str) -> ValidationResult:
        """Valider un User-Agent."""
        errors = []
        warnings = []
        risk_score = 0.0
        
        sanitized_ua = self.sanitize_string(user_agent, 500)
        
        # User-Agent manquant ou trop court
        if not sanitized_ua or len(sanitized_ua) < 10:
            warnings.append("User-Agent manquant ou trop court")
            risk_score += 1.0
        
        # User-Agents suspects
        suspicious_patterns = [
            r"(?i)(bot|crawler|spider|scraper)",
            r"(?i)(sqlmap|nikto|nmap|masscan|nessus)",
            r"(?i)(python-requests|curl|wget|libwww)",
            r"(?i)(scanner|audit|pentest)",
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, sanitized_ua):
                warnings.append(f"User-Agent suspect détecté")
                risk_score += 2.0
                break
        
        # Vérifier les caractères de contrôle
        if re.search(r'[\x00-\x1f\x7f-\x9f]', user_agent):
            warnings.append("Caractères de contrôle dans User-Agent")
            risk_score += 1.5
        
        return ValidationResult(
            is_valid=True,  # User-Agent toujours accepté mais noté
            sanitized_value=sanitized_ua,
            errors=errors,
            warnings=warnings,
            risk_score=min(risk_score, 10.0)
        )
    
    def validate_file_upload(self, filename: str, content_type: str, size: int) -> ValidationResult:
        """Valider un upload de fichier."""
        errors = []
        warnings = []
        risk_score = 0.0
        
        # Sanitiser le nom de fichier
        sanitized_filename = self.sanitize_string(filename, 255)
        
        # Vérifier l'extension
        for ext in self.dangerous_extensions:
            if sanitized_filename.lower().endswith(ext):
                errors.append(f"Extension de fichier interdite: {ext}")
                risk_score += 8.0
                break
        
        # Vérifier le double d'extension
        if sanitized_filename.count('.') > 2:
            warnings.append("Fichier avec extensions multiples")
            risk_score += 2.0
        
        # Vérifier la taille
        max_size = 50 * 1024 * 1024  # 50MB
        if size > max_size:
            errors.append(f"Fichier trop volumineux (max {max_size} bytes)")
            risk_score += 5.0
        
        # Vérifier le content-type
        allowed_types = [
            "text/plain", "text/html", "text/css", "text/javascript",
            "application/json", "application/xml", "application/pdf",
            "image/jpeg", "image/png", "image/gif", "image/webp"
        ]
        
        if content_type not in allowed_types:
            warnings.append(f"Type de contenu non recommandé: {content_type}")
            risk_score += 1.0
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized_filename,
            errors=errors,
            warnings=warnings,
            risk_score=min(risk_score, 10.0)
        )
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Obtenir un résumé des validations."""
        total_validations = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        
        all_errors = []
        all_warnings = []
        risk_scores = []
        
        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            risk_scores.append(result.risk_score)
        
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        max_risk = max(risk_scores) if risk_scores else 0
        
        return {
            "total_validations": total_validations,
            "valid_count": valid_count,
            "invalid_count": total_validations - valid_count,
            "success_rate": (valid_count / total_validations * 100) if total_validations > 0 else 100,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "average_risk_score": round(avg_risk, 2),
            "max_risk_score": round(max_risk, 2),
            "risk_level": self._get_risk_level(max_risk),
            "most_common_errors": self._get_most_common(all_errors),
            "most_common_warnings": self._get_most_common(all_warnings)
        }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Déterminer le niveau de risque."""
        if risk_score >= 8.0:
            return "CRITICAL"
        elif risk_score >= 6.0:
            return "HIGH"
        elif risk_score >= 4.0:
            return "MEDIUM"
        elif risk_score >= 2.0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_most_common(self, items: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Obtenir les éléments les plus fréquents."""
        from collections import Counter
        counter = Counter(items)
        return [
            {"message": msg, "count": count}
            for msg, count in counter.most_common(limit)
        ]


# Instance globale
input_validator = AdvancedInputValidator(ValidationLevel.STRICT)