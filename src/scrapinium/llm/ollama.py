"""Client Ollama simple pour LLM local."""


import httpx

from ..config import get_logger, settings

logger = get_logger("llm.ollama")


class OllamaClient:
    """Client simple pour Ollama local."""

    def __init__(self, model: str = None):
        self.base_url = settings.ollama_host.rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = settings.ollama_timeout

        self.client = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"🤖 Client Ollama: {self.base_url}, modèle: {self.model}")

    async def generate(self, messages: list[dict], temperature: float = 0.7) -> str:
        """
        Génère une réponse simple.

        Args:
            messages: Liste de messages [{"role": "user", "content": "..."}]
            temperature: Température de génération

        Returns:
            Réponse textuelle du LLM
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {"temperature": temperature},
                "stream": False,
            }

            response = await self.client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()

            result = response.json()
            content = result.get("message", {}).get("content", "")

            if not content:
                raise Exception("Réponse vide d'Ollama")

            logger.debug(f"✅ Réponse générée: {len(content)} caractères")
            return content.strip()

        except Exception as e:
            logger.error(f"❌ Erreur Ollama: {e}")
            raise

    async def health_check(self) -> bool:
        """Vérifie si Ollama est accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return True
        except Exception:
            return False

    async def cleanup(self):
        """Ferme le client."""
        await self.client.aclose()


# Instance globale
ollama_client = OllamaClient()


async def generate_with_ollama(content: str, instruction: str = None) -> str:
    """
    Fonction simple pour structurer du contenu avec Ollama.

    Args:
        content: Contenu à structurer
        instruction: Instruction spécifique (optionnel)

    Returns:
        Contenu structuré
    """
    default_instruction = """Tu es un expert en extraction et structuration de contenu web.
Analyse le contenu fourni et structure-le de manière claire et lisible en Markdown.
Préserve les informations importantes et organise le contenu logiquement."""

    messages = [
        {"role": "system", "content": instruction or default_instruction},
        {"role": "user", "content": f"Contenu à structurer:\n\n{content}"},
    ]

    return await ollama_client.generate(messages)
