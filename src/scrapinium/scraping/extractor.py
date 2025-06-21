"""Extracteur de contenu intelligent avec BeautifulSoup et Readability."""

import re
from typing import Any, Optional
from urllib.parse import urljoin

import html2text
from bs4 import BeautifulSoup
from readability import Document

from ..config import get_logger
from ..models.schemas import ContentExtraction

logger = get_logger("scraping.extractor")


class ContentExtractor:
    """Extracteur de contenu principal d'une page web."""

    def __init__(self):
        self.logger = logger

        # Configuration html2text pour Markdown
        self.html_to_markdown = html2text.HTML2Text()
        self.html_to_markdown.ignore_links = False
        self.html_to_markdown.ignore_images = False
        self.html_to_markdown.body_width = 0  # Pas de wrap
        self.html_to_markdown.unicode_snob = True

    def extract_main_content(self, html: str, url: str = None) -> ContentExtraction:
        """
        Extrait le contenu principal d'une page HTML.

        Args:
            html: HTML brut de la page
            url: URL de la page (pour résoudre les liens relatifs)

        Returns:
            ContentExtraction avec le contenu structuré
        """
        try:
            self.logger.debug("🔍 Extraction du contenu principal...")

            if not html or not html.strip():
                return self._empty_extraction("HTML vide ou invalide")

            # Utiliser Readability pour extraire le contenu principal
            doc = Document(html)
            main_content_html = doc.content()
            title = doc.title()

            # Parser avec BeautifulSoup
            soup = BeautifulSoup(main_content_html, "html.parser")

            # Nettoyer le HTML
            cleaned_soup = self._clean_html(soup)

            # Extraire les métadonnées de l'HTML original
            original_soup = BeautifulSoup(html, "html.parser")
            metadata = self._extract_metadata(original_soup)

            # Résoudre les liens relatifs
            if url:
                self._resolve_relative_urls(cleaned_soup, url)

            # Convertir en texte propre
            content_text = self._html_to_text(cleaned_soup)

            if not content_text.strip():
                return self._empty_extraction("Aucun contenu textuel trouvé")

            # Créer l'extraction
            extraction = ContentExtraction(
                title=title or metadata.get("title", "").strip(),
                content=content_text,
                author=metadata.get("author"),
                publication_date=metadata.get("publication_date"),
                tags=metadata.get("tags", []),
                language=metadata.get("language"),
                word_count=len(content_text.split()),
            )

            self.logger.info(
                f"✅ Contenu extrait: {extraction.word_count} mots, "
                f"{extraction.reading_time_minutes}min de lecture"
            )

            return extraction

        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'extraction: {e}")
            return self._empty_extraction(f"Erreur: {str(e)}")

    def extract_structured_data(self, html: str) -> dict[str, Any]:
        """
        Extrait les données structurées (JSON-LD, microdata, etc.).

        Args:
            html: HTML de la page

        Returns:
            Dict contenant les données structurées trouvées
        """
        soup = BeautifulSoup(html, "html.parser")
        structured_data = {}

        try:
            # JSON-LD
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            if json_ld_scripts:
                import json

                json_ld_data = []
                for script in json_ld_scripts:
                    try:
                        data = json.loads(script.string)
                        json_ld_data.append(data)
                    except (json.JSONDecodeError, AttributeError):
                        continue

                if json_ld_data:
                    structured_data["json_ld"] = json_ld_data

            # Open Graph
            og_data = {}
            og_tags = soup.find_all(
                "meta", property=lambda x: x and x.startswith("og:")
            )
            for tag in og_tags:
                property_name = tag.get("property", "").replace("og:", "")
                content = tag.get("content", "")
                if property_name and content:
                    og_data[property_name] = content

            if og_data:
                structured_data["open_graph"] = og_data

            # Twitter Cards
            twitter_data = {}
            twitter_tags = soup.find_all(
                "meta", attrs={"name": lambda x: x and x.startswith("twitter:")}
            )
            for tag in twitter_tags:
                name = tag.get("name", "").replace("twitter:", "")
                content = tag.get("content", "")
                if name and content:
                    twitter_data[name] = content

            if twitter_data:
                structured_data["twitter"] = twitter_data

        except Exception as e:
            self.logger.warning(
                f"Erreur lors de l'extraction des données structurées: {e}"
            )

        return structured_data

    def convert_to_markdown(self, html: str, url: str = None) -> str:
        """
        Convertit le HTML en Markdown.

        Args:
            html: HTML à convertir
            url: URL de base pour résoudre les liens relatifs

        Returns:
            Contenu en format Markdown
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Résoudre les URLs relatives
            if url:
                self._resolve_relative_urls(soup, url)

            # Nettoyer le HTML
            cleaned_soup = self._clean_html(soup)

            # Convertir en Markdown
            markdown = self.html_to_markdown.handle(str(cleaned_soup))

            # Nettoyer le Markdown
            markdown = self._clean_markdown(markdown)

            return markdown

        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion en Markdown: {e}")
            return ""

    def _clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Nettoie le HTML en supprimant les éléments indésirables."""

        # Éléments à supprimer complètement
        unwanted_tags = [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "iframe",
            "object",
            "embed",
            "form",
            "input",
            "button",
            "select",
            "textarea",
            "noscript",
            "canvas",
        ]

        for tag_name in unwanted_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Supprimer les éléments avec certaines classes/IDs
        unwanted_selectors = [
            '[class*="comment"]',
            '[class*="sidebar"]',
            '[class*="footer"]',
            '[class*="header"]',
            '[class*="navigation"]',
            '[class*="menu"]',
            '[class*="ad"]',
            '[class*="advertisement"]',
            '[class*="popup"]',
            '[id*="comment"]',
            '[id*="sidebar"]',
            '[id*="footer"]',
            '[id*="header"]',
            '[id*="navigation"]',
            '[id*="menu"]',
        ]

        for selector in unwanted_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception:
                continue

        # Nettoyer les attributs inutiles
        for tag in soup.find_all():
            if hasattr(tag, "attrs"):
                # Garder seulement les attributs essentiels
                essential_attrs = ["href", "src", "alt", "title"]
                tag.attrs = {k: v for k, v in tag.attrs.items() if k in essential_attrs}

        return soup

    def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extrait les métadonnées de la page."""
        metadata = {}

        try:
            # Titre
            title_tag = soup.find("title")
            if title_tag:
                metadata["title"] = title_tag.get_text().strip()

            # Métadonnées standard
            meta_tags = soup.find_all("meta")
            for tag in meta_tags:
                name = tag.get("name", "").lower()
                property_name = tag.get("property", "").lower()
                content = tag.get("content", "").strip()

                if not content:
                    continue

                # Auteur
                if name in ["author", "creator"] or property_name == "article:author":
                    metadata["author"] = content

                # Description
                elif name == "description" or property_name == "og:description":
                    metadata["description"] = content

                # Mots-clés/tags
                elif name in ["keywords", "tags"]:
                    tags = [tag.strip() for tag in content.split(",")]
                    metadata["tags"] = tags

                # Langue
                elif name == "language" or property_name == "og:locale":
                    metadata["language"] = content

                # Date de publication
                elif (
                    name in ["date", "publish-date", "publication-date"]
                    or property_name == "article:published_time"
                ):
                    metadata["publication_date"] = self._parse_date(content)

            # Langue depuis l'attribut lang
            html_tag = soup.find("html")
            if html_tag and html_tag.get("lang"):
                metadata["language"] = html_tag.get("lang")

        except Exception as e:
            self.logger.warning(f"Erreur lors de l'extraction des métadonnées: {e}")

        return metadata

    def _resolve_relative_urls(self, soup: BeautifulSoup, base_url: str):
        """Résout les URLs relatives en URLs absolues."""
        try:
            # Liens
            for link in soup.find_all("a", href=True):
                link["href"] = urljoin(base_url, link["href"])

            # Images
            for img in soup.find_all("img", src=True):
                img["src"] = urljoin(base_url, img["src"])

        except Exception as e:
            self.logger.warning(f"Erreur lors de la résolution des URLs: {e}")

    def _html_to_text(self, soup: BeautifulSoup) -> str:
        """Convertit le HTML en texte propre."""
        try:
            # Supprimer les scripts et styles restants
            for script in soup(["script", "style"]):
                script.decompose()

            # Obtenir le texte
            text = soup.get_text()

            # Nettoyer le texte
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion en texte: {e}")
            return ""

    def _clean_markdown(self, markdown: str) -> str:
        """Nettoie le contenu Markdown."""
        try:
            # Supprimer les lignes vides multiples
            markdown = re.sub(r"\n\s*\n\s*\n", "\n\n", markdown)

            # Supprimer les espaces en fin de ligne
            markdown = re.sub(r" +$", "", markdown, flags=re.MULTILINE)

            # Nettoyer les liens vides
            markdown = re.sub(r"\[\]\([^)]*\)", "", markdown)

            return markdown.strip()

        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage du Markdown: {e}")
            return markdown

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse une date depuis une chaîne de caractères."""
        try:
            from dateutil.parser import parse

            parsed_date = parse(date_str)
            return parsed_date.isoformat()
        except Exception:
            return None

    def _empty_extraction(self, reason: str) -> ContentExtraction:
        """Retourne une extraction vide avec un message d'erreur."""
        self.logger.warning(f"Extraction vide: {reason}")
        return ContentExtraction(
            title="",
            content=f"Échec de l'extraction: {reason}",
            word_count=0,
            reading_time_minutes=0,
        )


# Instance globale de l'extracteur
content_extractor = ContentExtractor()


def extract_content(html: str, url: str = None) -> ContentExtraction:
    """
    Fonction utilitaire pour extraire le contenu.

    Args:
        html: HTML de la page
        url: URL de la page

    Returns:
        ContentExtraction avec le contenu principal
    """
    return content_extractor.extract_main_content(html, url)


def html_to_markdown(html: str, url: str = None) -> str:
    """
    Fonction utilitaire pour convertir HTML en Markdown.

    Args:
        html: HTML à convertir
        url: URL de base

    Returns:
        Contenu en Markdown
    """
    return content_extractor.convert_to_markdown(html, url)
