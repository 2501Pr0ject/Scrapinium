"""Validators pour Scrapinium."""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Valide une URL.

    Args:
        url: URL à valider

    Returns:
        Tuple (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL vide"

    url = url.strip()

    # Vérifier le format
    try:
        parsed = urlparse(url)

        if not parsed.scheme:
            return False, "Protocole manquant (http/https)"

        if parsed.scheme not in ["http", "https"]:
            return False, "Protocole non supporté (seuls http/https sont acceptés)"

        if not parsed.netloc:
            return False, "Nom de domaine manquant"

        # Vérifier la longueur
        if len(url) > 2048:
            return False, "URL trop longue (max 2048 caractères)"

        # Vérifier les caractères dangereux
        dangerous_patterns = [
            r"javascript:",
            r"data:",
            r"file:",
            r"ftp:",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, url.lower()):
                return False, "Protocole non autorisé détecté"

        return True, None

    except Exception as e:
        return False, f"Format d'URL invalide: {str(e)}"


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier.

    Args:
        filename: Nom de fichier à nettoyer

    Returns:
        Nom de fichier sécurisé
    """
    # Remplacer les caractères dangereux
    safe_filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Limiter la longueur
    if len(safe_filename) > 255:
        safe_filename = safe_filename[:255]

    # S'assurer qu'il n'est pas vide
    if not safe_filename.strip():
        safe_filename = "untitled"

    return safe_filename.strip()


def validate_content_length(
    content: str, max_length: int = 100000
) -> tuple[bool, Optional[str]]:
    """
    Valide la longueur du contenu.

    Args:
        content: Contenu à valider
        max_length: Longueur maximale autorisée

    Returns:
        Tuple (is_valid, error_message)
    """
    if not content:
        return False, "Contenu vide"

    if len(content) > max_length:
        return False, f"Contenu trop long ({len(content)} > {max_length} caractères)"

    return True, None
