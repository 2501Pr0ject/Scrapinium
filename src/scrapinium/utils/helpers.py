"""Fonctions utilitaires pour Scrapinium."""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Optional


def generate_task_id() -> str:
    """Génère un ID unique pour une tâche."""
    return str(uuid.uuid4())


def hash_url(url: str) -> str:
    """Génère un hash pour une URL."""
    return hashlib.md5(url.encode()).hexdigest()


def format_timestamp(dt: datetime = None) -> str:
    """Formate un timestamp."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def estimate_reading_time(word_count: int, wpm: int = 200) -> int:
    """
    Estime le temps de lecture.

    Args:
        word_count: Nombre de mots
        wpm: Mots par minute (défaut: 200)

    Returns:
        Temps de lecture en minutes
    """
    if word_count <= 0:
        return 0
    return max(1, round(word_count / wpm))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte.

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter

    Returns:
        Texte tronqué
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def extract_domain(url: str) -> Optional[str]:
    """
    Extrait le domaine d'une URL.

    Args:
        url: URL

    Returns:
        Nom de domaine ou None
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def safe_get(dictionary: dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Récupère une valeur de dictionnaire de manière sécurisée.

    Args:
        dictionary: Dictionnaire
        key: Clé à récupérer
        default: Valeur par défaut

    Returns:
        Valeur ou défaut
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def calculate_file_size(content: str) -> int:
    """
    Calcule la taille d'un contenu en bytes.

    Args:
        content: Contenu

    Returns:
        Taille en bytes
    """
    if not content:
        return 0
    return len(content.encode("utf-8"))


def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier.

    Args:
        size_bytes: Taille en bytes

    Returns:
        Taille formatée (ex: "1.2 KB")
    """
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"
