"""Exceptions personnalisées pour Scrapinium."""


class ScrapiniumException(Exception):
    """Exception de base pour toutes les erreurs Scrapinium."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """Convertir l'exception en dictionnaire pour l'API."""
        result = {"error": self.message}
        if self.details:
            result["details"] = self.details
        return result


class ScrapingError(ScrapiniumException):
    """Erreurs liées au processus de scraping."""
    pass


class BrowserError(ScrapingError):
    """Erreurs liées au navigateur (Playwright)."""
    pass


class ExtractionError(ScrapingError):
    """Erreurs liées à l'extraction de contenu."""
    pass


class LLMError(ScrapiniumException):
    """Erreurs liées aux modèles de langage."""
    pass


class MLPipelineError(ScrapiniumException):
    """Erreurs liées au pipeline ML."""
    pass


class ValidationError(ScrapiniumException):
    """Erreurs de validation des données d'entrée."""
    pass


class SecurityError(ScrapiniumException):
    """Erreurs de sécurité (SSRF, validation, etc.)."""
    pass


class CacheError(ScrapiniumException):
    """Erreurs liées au système de cache."""
    pass


class TaskError(ScrapiniumException):
    """Erreurs liées à la gestion des tâches."""
    pass


class ConfigurationError(ScrapiniumException):
    """Erreurs de configuration."""
    pass


class RateLimitError(ScrapiniumException):
    """Erreurs de limitation de débit."""
    pass


class TimeoutError(ScrapiniumException):
    """Erreurs de timeout."""
    pass


class NetworkError(ScrapiniumException):
    """Erreurs réseau."""
    pass


# Exceptions avec codes d'erreur HTTP spécifiques
class HTTPException(ScrapiniumException):
    """Exception HTTP avec code de statut."""
    
    def __init__(self, status_code: int, message: str, details: str = None):
        self.status_code = status_code
        super().__init__(message, details)


class BadRequestError(HTTPException):
    """Erreur 400 - Requête malformée."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(400, message, details)


class UnauthorizedError(HTTPException):
    """Erreur 401 - Non autorisé."""
    
    def __init__(self, message: str = "Non autorisé", details: str = None):
        super().__init__(401, message, details)


class ForbiddenError(HTTPException):
    """Erreur 403 - Accès interdit."""
    
    def __init__(self, message: str = "Accès interdit", details: str = None):
        super().__init__(403, message, details)


class NotFoundError(HTTPException):
    """Erreur 404 - Ressource non trouvée."""
    
    def __init__(self, message: str = "Ressource non trouvée", details: str = None):
        super().__init__(404, message, details)


class ConflictError(HTTPException):
    """Erreur 409 - Conflit."""
    
    def __init__(self, message: str = "Conflit", details: str = None):
        super().__init__(409, message, details)


class UnprocessableEntityError(HTTPException):
    """Erreur 422 - Entité non traitable."""
    
    def __init__(self, message: str = "Entité non traitable", details: str = None):
        super().__init__(422, message, details)


class TooManyRequestsError(HTTPException):
    """Erreur 429 - Trop de requêtes."""
    
    def __init__(self, message: str = "Trop de requêtes", details: str = None):
        super().__init__(429, message, details)


class InternalServerError(HTTPException):
    """Erreur 500 - Erreur interne du serveur."""
    
    def __init__(self, message: str = "Erreur interne du serveur", details: str = None):
        super().__init__(500, message, details)


class BadGatewayError(HTTPException):
    """Erreur 502 - Mauvaise passerelle."""
    
    def __init__(self, message: str = "Mauvaise passerelle", details: str = None):
        super().__init__(502, message, details)


class ServiceUnavailableError(HTTPException):
    """Erreur 503 - Service indisponible."""
    
    def __init__(self, message: str = "Service indisponible", details: str = None):
        super().__init__(503, message, details)


class GatewayTimeoutError(HTTPException):
    """Erreur 504 - Timeout de passerelle."""
    
    def __init__(self, message: str = "Timeout de passerelle", details: str = None):
        super().__init__(504, message, details)