"""Gestionnaire d'exceptions centralisé pour l'API FastAPI."""

import traceback
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..exceptions import (
    ScrapiniumException, 
    HTTPException as ScrapiniumHTTPException,
    ValidationError,
    SecurityError,
    RateLimitError,
    ServiceUnavailableError
)
from ..utils.logging import get_logger
from ..models.schemas import APIResponse

logger = get_logger("exception_handler")


async def scrapinium_exception_handler(
    request: Request, 
    exc: ScrapiniumException
) -> JSONResponse:
    """Gestionnaire pour les exceptions Scrapinium personnalisées."""
    
    # Log de l'erreur avec contexte
    logger.error(
        f"ScrapiniumException: {exc.message}",
        extra={
            "exception_type": type(exc).__name__,
            "details": exc.details,
            "url": str(request.url),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # Déterminer le code de statut HTTP
    status_code = 500  # Défaut
    if isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, SecurityError):
        status_code = 403
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, ServiceUnavailableError):
        status_code = 503
    elif isinstance(exc, ScrapiniumHTTPException):
        status_code = exc.status_code
    
    # Créer la réponse
    response_data = APIResponse.error_response(
        message=exc.message,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )


async def http_exception_handler(
    request: Request, 
    exc: HTTPException
) -> JSONResponse:
    """Gestionnaire pour les exceptions HTTP FastAPI."""
    
    logger.warning(
        f"HTTPException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "url": str(request.url),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    response_data = APIResponse.error_response(
        message=str(exc.detail)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data.model_dump()
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """Gestionnaire pour toutes les autres exceptions non gérées."""
    
    # Log détaillé de l'erreur
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "url": str(request.url),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # En production, ne pas exposer les détails internes
    message = "Une erreur interne s'est produite"
    details = None
    
    # En développement, fournir plus de détails
    try:
        from ..config.settings import get_settings
        settings = get_settings()
        if settings.debug:
            message = f"Erreur interne: {str(exc)}"
            details = traceback.format_exc()
    except Exception:
        pass  # Fallback si impossible de récupérer les settings
    
    response_data = APIResponse.error_response(
        message=message,
        details=details
    )
    
    return JSONResponse(
        status_code=500,
        content=response_data.model_dump()
    )


def setup_exception_handlers(app):
    """Configurer tous les gestionnaires d'exceptions pour l'app FastAPI."""
    
    # Gestionnaires par ordre de spécificité (du plus spécifique au plus général)
    app.add_exception_handler(ScrapiniumException, scrapinium_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured")


def create_error_response(
    message: str, 
    details: str = None, 
    status_code: int = 500
) -> JSONResponse:
    """Créer une réponse d'erreur standardisée."""
    
    response_data = APIResponse.error_response(
        message=message,
        details=details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )


def handle_validation_error(field: str, value: Any, message: str) -> ValidationError:
    """Helper pour créer des erreurs de validation standardisées."""
    return ValidationError(
        message=f"Erreur de validation pour '{field}': {message}",
        details=f"Valeur reçue: {value}"
    )


def handle_security_error(threat_type: str, details: str) -> SecurityError:
    """Helper pour créer des erreurs de sécurité standardisées."""
    return SecurityError(
        message=f"Violation de sécurité détectée: {threat_type}",
        details=details
    )


def handle_rate_limit_error(limit: int, window: str) -> RateLimitError:
    """Helper pour créer des erreurs de rate limiting standardisées."""
    return RateLimitError(
        message=f"Limite de débit dépassée: {limit} requêtes par {window}",
        details="Veuillez réessayer plus tard"
    )