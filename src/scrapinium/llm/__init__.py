"""Module LLM pour Scrapinium - Ollama local uniquement."""

from .ollama import generate_with_ollama, ollama_client

__all__ = [
    "ollama_client",
    "generate_with_ollama",
]
