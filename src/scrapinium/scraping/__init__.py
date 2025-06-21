"""Module de scraping pour Scrapinium."""

from .browser import (
    BrowserManager,
    PageScraper,
    browser_manager,
    cleanup_browser,
    quick_scrape,
)
from .extractor import (
    ContentExtractor,
    content_extractor,
    extract_content,
    html_to_markdown,
)
from .service import (
    ScrapingService,
    scrape_url,
    scraping_service,
)

__all__ = [
    # Browser
    "BrowserManager",
    "PageScraper",
    "browser_manager",
    "cleanup_browser",
    "quick_scrape",
    # Extractor
    "ContentExtractor",
    "content_extractor",
    "extract_content",
    "html_to_markdown",
    # Service
    "ScrapingService",
    "scraping_service",
    "scrape_url",
]
