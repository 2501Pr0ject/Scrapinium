"""Validateurs stricts pour les entrées de l'API."""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from pydantic import BaseModel, HttpUrl, validator, Field
from ..exceptions import ValidationError, SecurityError
from ..utils.logging import get_logger

logger = get_logger("validators")


# Constantes de validation
MAX_URL_LENGTH = 2000
MAX_STRING_LENGTH = 10000
MAX_INSTRUCTIONS_LENGTH = 5000
ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_DOMAINS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "10.", "172.16.", "192.168.", "169.254.",
    "metadata.google.internal", "169.254.169.254"
}


class ScrapingTaskRequest(BaseModel):
    """Modèle validé pour les requêtes de scraping."""
    
    url: HttpUrl = Field(..., description="URL à scraper")
    output_format: str = Field(default="markdown", regex="^(text|markdown|json|html)$")
    use_llm: bool = Field(default=False)
    custom_instructions: Optional[str] = Field(default=None, max_length=MAX_INSTRUCTIONS_LENGTH)
    llm_provider: Optional[str] = Field(default=None, regex="^(ollama|openai|anthropic|gemini)?$")
    priority: Optional[str] = Field(default="normal", regex="^(low|normal|high)$")
    use_cache: bool = Field(default=True)
    timeout: Optional[int] = Field(default=60, ge=10, le=300)
    
    @validator('url')
    def validate_url_security(cls, v):
        """Validation sécurisée de l'URL."""
        url_str = str(v)
        
        # Vérifier la longueur
        if len(url_str) > MAX_URL_LENGTH:
            raise ValidationError(f"URL trop longue (max {MAX_URL_LENGTH} caractères)")
        
        # Parser l'URL
        try:
            parsed = urlparse(url_str)
        except Exception as e:
            raise ValidationError(f"URL malformée: {e}")
        
        # Vérifier le schéma
        if parsed.scheme not in ALLOWED_SCHEMES:
            raise SecurityError(f"Schéma d'URL non autorisé: {parsed.scheme}")
        
        # Vérifier les domaines bloqués
        hostname = parsed.netloc.lower()
        for blocked in BLOCKED_DOMAINS:
            if hostname == blocked or hostname.startswith(blocked):
                raise SecurityError(f"Domaine bloqué: {hostname}")
        
        # Vérifier les IPs privées
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                raise SecurityError(f"Adresse IP non autorisée: {ip}")
        except ipaddress.AddressValueError:
            # Ce n'est pas une IP, c'est un nom de domaine - OK
            pass
        
        # Vérifier les caractères dangereux
        dangerous_chars = ["<", ">", "\"", "'", "&", "\x00", "\x01", "\x02"]
        for char in dangerous_chars:
            if char in url_str:
                raise SecurityError(f"Caractère dangereux détecté dans l'URL: {repr(char)}")
        
        return v
    
    @validator('custom_instructions')
    def validate_instructions(cls, v):
        """Validation des instructions personnalisées."""
        if v is None:
            return v
        
        # Vérifier la longueur
        if len(v) > MAX_INSTRUCTIONS_LENGTH:
            raise ValidationError(f"Instructions trop longues (max {MAX_INSTRUCTIONS_LENGTH} caractères)")
        
        # Vérifier les caractères de contrôle
        control_chars = re.findall(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', v)
        if control_chars:
            raise SecurityError("Caractères de contrôle détectés dans les instructions")
        
        # Vérifier les patterns suspects
        suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'file://',
            r'ftp://',
            r'\$\{.*\}',  # Template injection
            r'\{\{.*\}\}',  # Template injection
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise SecurityError(f"Pattern suspect détecté dans les instructions: {pattern}")
        
        return v.strip()


class MLAnalysisRequest(BaseModel):
    """Modèle validé pour les requêtes d'analyse ML."""
    
    html: str = Field(..., min_length=10, max_length=2000000)  # Max 2MB
    url: HttpUrl = Field(..., description="URL de la page")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    response_time: Optional[float] = Field(default=None, ge=0, le=60)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('html')
    def validate_html_content(cls, v):
        """Validation du contenu HTML."""
        
        # Vérifier les caractères de contrôle dangereux
        dangerous_control_chars = re.findall(r'[\x00-\x08\x0E-\x1F]', v)
        if dangerous_control_chars:
            raise SecurityError("Caractères de contrôle dangereux détectés dans le HTML")
        
        # Vérifier la présence minimale de balises HTML
        if not re.search(r'<[^>]+>', v):
            raise ValidationError("Le contenu ne semble pas être du HTML valide")
        
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Réutiliser la validation d'URL de ScrapingTaskRequest."""
        return ScrapingTaskRequest.validate_url_security(v)
    
    @validator('headers')
    def validate_headers(cls, v):
        """Validation des headers HTTP."""
        if not v:
            return v
        
        # Limiter le nombre de headers
        if len(v) > 50:
            raise ValidationError("Trop de headers (max 50)")
        
        for key, value in v.items():
            # Validation des clés
            if not re.match(r'^[a-zA-Z0-9\-_]+$', key):
                raise SecurityError(f"Nom de header invalide: {key}")
            
            # Validation des valeurs
            if len(str(value)) > 1000:
                raise ValidationError(f"Valeur de header trop longue pour {key}")
            
            # Vérifier les caractères de contrôle
            if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', str(value)):
                raise SecurityError(f"Caractères de contrôle dans la valeur du header {key}")
        
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validation des métadonnées."""
        if not v:
            return v
        
        # Limiter la taille des métadonnées
        if len(str(v)) > 10000:
            raise ValidationError("Métadonnées trop volumineuses (max 10KB)")
        
        # Vérifier que c'est sérialisable en JSON
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Métadonnées non sérialisables: {e}")
        
        return v


class TaskIdValidator:
    """Validateur pour les IDs de tâches."""
    
    @staticmethod
    def validate_task_id(task_id: str) -> str:
        """Valider un ID de tâche."""
        if not task_id:
            raise ValidationError("ID de tâche requis")
        
        if len(task_id) < 10 or len(task_id) > 100:
            raise ValidationError("ID de tâche doit faire entre 10 et 100 caractères")
        
        # Vérifier le format UUID ou alphanumérique
        if not re.match(r'^[a-zA-Z0-9\-_]+$', task_id):
            raise SecurityError("Format d'ID de tâche invalide")
        
        return task_id


class LimitValidator:
    """Validateur pour les paramètres de limite."""
    
    @staticmethod
    def validate_limit(limit: Optional[int], default: int = 50, max_limit: int = 1000) -> int:
        """Valider un paramètre de limite."""
        if limit is None:
            return default
        
        if not isinstance(limit, int):
            raise ValidationError("La limite doit être un entier")
        
        if limit < 1:
            raise ValidationError("La limite doit être positive")
        
        if limit > max_limit:
            raise ValidationError(f"Limite trop élevée (max {max_limit})")
        
        return limit


def validate_request_size(content_length: Optional[int], max_size: int = 50 * 1024 * 1024) -> None:
    """Valider la taille de la requête."""
    if content_length is None:
        return
    
    if content_length > max_size:
        raise ValidationError(f"Requête trop volumineuse (max {max_size // 1024 // 1024}MB)")


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Nettoyer et sécuriser une chaîne de caractères."""
    if not isinstance(value, str):
        value = str(value)
    
    # Supprimer les caractères de contrôle
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # Décoder les entités HTML
    import html
    value = html.unescape(value)
    
    # Limiter la longueur
    if len(value) > max_length:
        value = value[:max_length]
        logger.warning(f"Chaîne tronquée à {max_length} caractères")
    
    return value.strip()


def validate_file_upload(filename: str, content: bytes, allowed_types: List[str]) -> None:
    """Valider un fichier uploadé."""
    
    # Vérifier le nom de fichier
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        raise SecurityError("Nom de fichier invalide")
    
    # Vérifier l'extension
    if not any(filename.lower().endswith(ext) for ext in allowed_types):
        raise ValidationError(f"Type de fichier non autorisé. Types autorisés: {allowed_types}")
    
    # Vérifier la taille
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise ValidationError("Fichier trop volumineux (max 10MB)")
    
    # Vérifier les magic bytes pour les types communs
    magic_bytes = {
        '.txt': [b''],  # Texte peut commencer par n'importe quoi
        '.json': [b'{', b'['],
        '.html': [b'<!', b'<h', b'<H'],
        '.xml': [b'<?', b'<r', b'<R'],
    }
    
    ext = '.' + filename.split('.')[-1].lower()
    if ext in magic_bytes:
        valid_start = any(content.startswith(magic) for magic in magic_bytes[ext])
        if not valid_start and ext != '.txt':
            raise SecurityError(f"Contenu du fichier ne correspond pas à l'extension {ext}")


def create_request_validator(model_class):
    """Décorateur pour valider automatiquement les requêtes."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extraire l'objet request
            request_data = None
            for arg in args:
                if hasattr(arg, 'dict'):  # C'est probablement un modèle Pydantic
                    request_data = arg
                    break
            
            if request_data is None:
                raise ValidationError("Aucune donnée de requête trouvée")
            
            # Valider avec le modèle
            try:
                validated_data = model_class(**request_data.dict())
                # Remplacer l'argument original par les données validées
                new_args = list(args)
                for i, arg in enumerate(args):
                    if hasattr(arg, 'dict'):
                        new_args[i] = validated_data
                        break
                args = tuple(new_args)
            except Exception as e:
                logger.error(f"Validation error: {e}")
                raise ValidationError(f"Erreur de validation: {e}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator