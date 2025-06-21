"""Service principal de scraping orchestrant tous les composants avec cache."""

import asyncio
from datetime import datetime
from typing import Any, Optional
import hashlib

from ..config import get_logger
from ..llm import generate_with_ollama
from ..models.enums import OutputFormat, TaskStatus
from ..models.schemas import ContentExtraction, ScrapingTaskCreate
from ..cache import get_cache_manager
from ..cache.models import generate_cache_key, CacheLevel
from .browser import PageScraper, browser_manager
from .extractor import content_extractor

logger = get_logger("scraping.service")


class ScrapingService:
    """Service principal de scraping avec cache multi-niveau."""

    def __init__(self):
        self.logger = logger
        self.page_scraper = PageScraper(browser_manager)
        self.content_extractor = content_extractor
        self._active_tasks: dict[str, asyncio.Task] = {}
        self.cache_manager = None  # Sera initialisé lors du premier usage

    async def _ensure_cache_manager(self):
        """Assure que le gestionnaire de cache est initialisé."""
        if self.cache_manager is None:
            self.cache_manager = await get_cache_manager()
    
    def _generate_cache_key(self, task_data: ScrapingTaskCreate) -> str:
        """Génère une clé de cache pour une tâche de scraping."""
        cache_params = {
            "output_format": task_data.output_format.value,
            "llm_provider": task_data.llm_provider.value if task_data.llm_provider else None,
            "use_llm": getattr(task_data, 'use_llm', True),
            "custom_instructions": getattr(task_data, 'custom_instructions', None),
        }
        return generate_cache_key(str(task_data.url), cache_params)
    
    async def scrape_url(
        self,
        task_data: ScrapingTaskCreate,
        task_id: str = None,
        progress_callback: Optional[callable] = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Scrape une URL complètement.

        Args:
            task_data: Données de la tâche de scraping
            task_id: ID de la tâche pour le suivi
            progress_callback: Callback pour reporter le progrès

        Returns:
            Dict contenant tous les résultats du scraping
        """
        start_time = datetime.utcnow()
        url = str(task_data.url)

        try:
            self.logger.info(f"🚀 Début du scraping complet: {url}")

            if progress_callback:
                await progress_callback(task_id, 10, "Initialisation du navigateur")

            # Étape 1: Scraping de la page avec Playwright
            self.logger.debug("📄 Étape 1: Récupération de la page")
            page_data = await self.page_scraper.fetch_page(url)

            if page_data.get("error"):
                raise Exception(f"Erreur de navigation: {page_data['error']}")

            if not page_data.get("html"):
                raise Exception("Aucun contenu HTML récupéré")

            if progress_callback:
                await progress_callback(
                    task_id, 40, "Page récupérée, extraction du contenu"
                )

            # Étape 2: Extraction du contenu principal
            self.logger.debug("🔍 Étape 2: Extraction du contenu principal")
            content_extraction = self.content_extractor.extract_main_content(
                page_data["html"], url
            )

            if progress_callback:
                await progress_callback(task_id, 70, "Contenu extrait, formatage final")

            # Étape 3: Extraction des données structurées
            self.logger.debug("📊 Étape 3: Extraction des données structurées")
            structured_data = self.content_extractor.extract_structured_data(
                page_data["html"]
            )

            # Étape 4: Structuration intelligente avec LLM (si nécessaire)
            if (
                task_data.llm_provider
                and task_data.output_format == OutputFormat.MARKDOWN
            ):
                self.logger.debug("🧠 Étape 4a: Structuration intelligente avec LLM")
                try:
                    structured_by_llm = await self._enhance_with_llm(
                        content_extraction.content, task_data.output_format
                    )
                    content_extraction.content = structured_by_llm
                    if progress_callback:
                        await progress_callback(
                            task_id, 80, "Structuration LLM terminée"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Structuration LLM échouée, utilisation du contenu original: {e}"
                    )

            # Étape 5: Formatage selon le format demandé
            self.logger.debug(f"📝 Étape 5: Formatage en {task_data.output_format}")
            formatted_content = await self._format_content(
                content_extraction, page_data, task_data.output_format
            )

            if progress_callback:
                await progress_callback(task_id, 95, "Finalisation des résultats")

            # Calculer les métriques finales
            end_time = datetime.utcnow()
            total_execution_time = int((end_time - start_time).total_seconds() * 1000)

            # Assembler le résultat final
            result = {
                "status": TaskStatus.COMPLETED,
                "url": url,
                "output_format": task_data.output_format,
                "structured_content": formatted_content,
                "raw_content": page_data["html"],
                "task_metadata": {
                    "title": content_extraction.title,
                    "author": content_extraction.author,
                    "word_count": content_extraction.word_count,
                    "reading_time_minutes": content_extraction.reading_time_minutes,
                    "language": content_extraction.language,
                    "tags": content_extraction.tags,
                    "page_metadata": {
                        "status_code": page_data.get("status_code"),
                        "final_url": url,
                        "page_title": page_data.get("title"),
                        "meta_description": page_data.get("meta", {}).get(
                            "description"
                        ),
                        "links_count": len(page_data.get("links", [])),
                        "images_count": len(page_data.get("images", [])),
                    },
                    "structured_data": structured_data,
                    "scraping_timestamp": start_time.isoformat(),
                    "completion_timestamp": end_time.isoformat(),
                },
                "execution_time_ms": total_execution_time,
                "content_size_bytes": len(page_data["html"])
                if page_data["html"]
                else 0,
                "tokens_used": self._estimate_tokens_used(formatted_content),
                "error_message": None,
                "error_details": None,
            }

            if progress_callback:
                await progress_callback(task_id, 100, "Scraping terminé avec succès")

            self.logger.info(
                f"✅ Scraping terminé avec succès: {url} "
                f"({total_execution_time}ms, {content_extraction.word_count} mots)"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Erreur lors du scraping de {url}: {error_msg}")

            if progress_callback:
                await progress_callback(task_id, 100, f"Erreur: {error_msg}")

            # Calculer le temps d'exécution même en cas d'erreur
            end_time = datetime.utcnow()
            total_execution_time = int((end_time - start_time).total_seconds() * 1000)

            return {
                "status": TaskStatus.FAILED,
                "url": url,
                "output_format": task_data.output_format,
                "structured_content": None,
                "raw_content": None,
                "task_metadata": {
                    "scraping_timestamp": start_time.isoformat(),
                    "completion_timestamp": end_time.isoformat(),
                },
                "execution_time_ms": total_execution_time,
                "content_size_bytes": 0,
                "tokens_used": None,
                "error_message": error_msg,
                "error_details": {
                    "error_type": type(e).__name__,
                    "url": url,
                    "timestamp": end_time.isoformat(),
                },
            }

    async def scrape_multiple_urls(
        self,
        urls: list[str],
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        max_concurrent: int = 3,
        progress_callback: Optional[callable] = None,
    ) -> list[dict[str, Any]]:
        """
        Scrape plusieurs URLs en parallèle.

        Args:
            urls: Liste des URLs à scraper
            output_format: Format de sortie
            max_concurrent: Nombre maximum de tâches simultanées
            progress_callback: Callback pour le progrès global

        Returns:
            Liste des résultats de scraping
        """
        self.logger.info(
            f"🔄 Scraping de {len(urls)} URLs en parallèle (max {max_concurrent})"
        )

        # Créer un semaphore pour limiter la concurrence
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def scrape_with_semaphore(url: str, index: int):
            async with semaphore:
                task_data = ScrapingTaskCreate(url=url, output_format=output_format)

                result = await self.scrape_url(task_data, task_id=f"batch_{index}")

                if progress_callback:
                    progress = int(((index + 1) / len(urls)) * 100)
                    await progress_callback(
                        "batch_progress",
                        progress,
                        f"Terminé {index + 1}/{len(urls)} URLs",
                    )

                return result

        # Lancer toutes les tâches
        tasks = [scrape_with_semaphore(url, i) for i, url in enumerate(urls)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convertir les exceptions en résultats d'erreur
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "status": TaskStatus.FAILED,
                        "url": urls[i],
                        "error_message": str(result),
                        "execution_time_ms": 0,
                    }
                )
            else:
                processed_results.append(result)

        success_count = sum(
            1 for r in processed_results if r["status"] == TaskStatus.COMPLETED
        )
        self.logger.info(
            f"✅ Scraping batch terminé: {success_count}/{len(urls)} succès"
        )

        return processed_results

    async def _format_content(
        self,
        content_extraction: ContentExtraction,
        page_data: dict[str, Any],
        output_format: OutputFormat,
    ) -> str:
        """
        Formate le contenu selon le format demandé.

        Args:
            content_extraction: Contenu extrait
            page_data: Données brutes de la page
            output_format: Format de sortie désiré

        Returns:
            Contenu formaté selon le format demandé
        """
        try:
            if output_format == OutputFormat.MARKDOWN:
                return self._format_as_markdown(content_extraction, page_data)

            elif output_format == OutputFormat.JSON:
                import json

                return json.dumps(
                    {
                        "title": content_extraction.title,
                        "content": content_extraction.content,
                        "author": content_extraction.author,
                        "publication_date": content_extraction.publication_date,
                        "tags": content_extraction.tags,
                        "language": content_extraction.language,
                        "word_count": content_extraction.word_count,
                        "reading_time_minutes": content_extraction.reading_time_minutes,
                        "url": page_data.get("url"),
                        "extracted_at": datetime.utcnow().isoformat(),
                    },
                    indent=2,
                    ensure_ascii=False,
                )

            elif output_format == OutputFormat.XML:
                return self._format_as_xml(content_extraction, page_data)

            elif output_format == OutputFormat.CSV:
                return self._format_as_csv(content_extraction, page_data)

            elif output_format == OutputFormat.HTML:
                return self._format_as_html(content_extraction, page_data)

            elif output_format == OutputFormat.PLAIN_TEXT:
                return content_extraction.content

            else:
                # Fallback vers Markdown
                return self._format_as_markdown(content_extraction, page_data)

        except Exception as e:
            self.logger.error(f"Erreur lors du formatage en {output_format}: {e}")
            # Fallback vers le texte brut
            return content_extraction.content

    def _format_as_markdown(
        self, content: ContentExtraction, page_data: dict[str, Any]
    ) -> str:
        """Formate le contenu en Markdown."""
        lines = []

        # Titre principal
        if content.title:
            lines.append(f"# {content.title}")
            lines.append("")

        # Métadonnées
        if content.author:
            lines.append(f"**Auteur :** {content.author}")

        if content.publication_date:
            lines.append(f"**Date de publication :** {content.publication_date}")

        if content.language:
            lines.append(f"**Langue :** {content.language}")

        if content.tags:
            tags_str = ", ".join(f"`{tag}`" for tag in content.tags)
            lines.append(f"**Tags :** {tags_str}")

        lines.append(
            f"**Mots :** {content.word_count} | **Lecture :** ~{content.reading_time_minutes} min"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # Contenu principal
        lines.append(content.content)

        return "\n".join(lines)

    def _format_as_xml(
        self, content: ContentExtraction, page_data: dict[str, Any]
    ) -> str:
        """Formate le contenu en XML."""
        import xml.etree.ElementTree as ET

        root = ET.Element("article")

        # Métadonnées
        if content.title:
            title_elem = ET.SubElement(root, "title")
            title_elem.text = content.title

        if content.author:
            author_elem = ET.SubElement(root, "author")
            author_elem.text = content.author

        if content.publication_date:
            date_elem = ET.SubElement(root, "publication_date")
            date_elem.text = content.publication_date

        if content.language:
            lang_elem = ET.SubElement(root, "language")
            lang_elem.text = content.language

        # Tags
        if content.tags:
            tags_elem = ET.SubElement(root, "tags")
            for tag in content.tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = tag

        # Statistiques
        stats_elem = ET.SubElement(root, "statistics")
        word_count_elem = ET.SubElement(stats_elem, "word_count")
        word_count_elem.text = str(content.word_count)
        reading_time_elem = ET.SubElement(stats_elem, "reading_time_minutes")
        reading_time_elem.text = str(content.reading_time_minutes)

        # Contenu principal
        content_elem = ET.SubElement(root, "content")
        content_elem.text = content.content

        return ET.tostring(root, encoding="unicode", method="xml")

    def _format_as_csv(
        self, content: ContentExtraction, page_data: dict[str, Any]
    ) -> str:
        """Formate le contenu en CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow(
            [
                "title",
                "author",
                "publication_date",
                "language",
                "word_count",
                "reading_time_minutes",
                "tags",
                "content",
            ]
        )

        # Données
        writer.writerow(
            [
                content.title or "",
                content.author or "",
                content.publication_date or "",
                content.language or "",
                content.word_count,
                content.reading_time_minutes,
                "; ".join(content.tags) if content.tags else "",
                content.content.replace("\n", " ").replace("\r", " "),
            ]
        )

        return output.getvalue()

    def _format_as_html(
        self, content: ContentExtraction, page_data: dict[str, Any]
    ) -> str:
        """Formate le contenu en HTML."""
        lines = ["<!DOCTYPE html>", "<html>", "<head>", "<meta charset='utf-8'>"]

        if content.title:
            lines.append(f"<title>{content.title}</title>")

        lines.extend(["</head>", "<body>"])

        # Titre principal
        if content.title:
            lines.append(f"<h1>{content.title}</h1>")

        # Métadonnées
        if any([content.author, content.publication_date, content.language]):
            lines.append("<div class='metadata'>")

            if content.author:
                lines.append(f"<p><strong>Auteur :</strong> {content.author}</p>")

            if content.publication_date:
                lines.append(
                    f"<p><strong>Date :</strong> {content.publication_date}</p>"
                )

            if content.language:
                lines.append(f"<p><strong>Langue :</strong> {content.language}</p>")

            lines.append("</div>")

        # Contenu principal
        lines.append("<div class='content'>")
        # Convertir les retours à la ligne en paragraphes
        paragraphs = content.content.split("\n\n")
        for para in paragraphs:
            if para.strip():
                lines.append(f"<p>{para.strip()}</p>")
        lines.append("</div>")

        lines.extend(["</body>", "</html>"])

        return "\n".join(lines)

    async def _enhance_with_llm(self, content: str, output_format: OutputFormat) -> str:
        """
        Améliore le contenu avec structuration LLM.

        Args:
            content: Contenu brut extrait
            output_format: Format de sortie désiré

        Returns:
            Contenu structuré par le LLM
        """
        try:
            # Limiter la taille du contenu pour éviter les timeouts
            max_content_length = 8000  # ~2000 tokens
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
                self.logger.debug(
                    f"Contenu tronqué à {max_content_length} caractères pour le LLM"
                )

            # Instructions spécifiques selon le format
            if output_format == OutputFormat.MARKDOWN:
                instruction = """Tu es un expert en rédaction et structuration de contenu web.

Ton rôle:
- Analyser le contenu fourni et le restructurer de manière claire et logique
- Créer une structure Markdown bien organisée avec des titres, sous-titres appropriés
- Préserver toutes les informations importantes
- Améliorer la lisibilité sans dénaturer le sens
- Utiliser des listes, citations et mise en forme Markdown quand approprié

Règles:
- Garde un style professionnel et informatif
- Utilise des titres hiérarchiques (##, ###, etc.)
- Organise le contenu en sections logiques
- Préserve les liens et références importantes
- Si le contenu est trop court, développe légèrement en restant factuel"""

            else:
                instruction = """Tu es un expert en extraction et structuration de contenu web.
Analyse le contenu fourni et structure-le de manière claire et lisible.
Préserve les informations importantes et organise le contenu logiquement."""

            # Générer avec Ollama
            structured_content = await generate_with_ollama(content, instruction)

            if structured_content and len(structured_content.strip()) > 100:
                self.logger.info(
                    f"✅ Contenu structuré par LLM: {len(structured_content)} caractères"
                )
                return structured_content
            else:
                self.logger.warning(
                    "Réponse LLM trop courte, utilisation du contenu original"
                )
                return content

        except Exception as e:
            self.logger.error(f"Erreur lors de la structuration LLM: {e}")
            return content

    def _estimate_tokens_used(self, content: str) -> int:
        """
        Estime le nombre de tokens utilisés.
        Approximation: 1 token ≈ 4 caractères

        Args:
            content: Contenu à estimer

        Returns:
            Nombre approximatif de tokens
        """
        if not content:
            return 0
        return max(1, len(content) // 4)

    async def cleanup(self):
        """Nettoie les ressources du service."""
        # Annuler les tâches actives
        for task_id, task in self._active_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"Tâche {task_id} annulée")

        self._active_tasks.clear()

        # Nettoyer le navigateur
        await browser_manager.cleanup()


# Instance globale du service
scraping_service = ScrapingService()


async def scrape_url(task_data: ScrapingTaskCreate, **kwargs) -> dict[str, Any]:
    """
    Fonction utilitaire pour scraper une URL.

    Args:
        task_data: Données de la tâche
        **kwargs: Arguments additionnels

    Returns:
        Résultat du scraping
    """
    return await scraping_service.scrape_url(task_data, **kwargs)
