"""Gestionnaire de navigateur avec Playwright optimisé avec pool."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional, List
from urllib.parse import urlparse
from dataclasses import dataclass
import time
from collections import deque

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from ..config import get_logger, settings
from ..utils.memory import get_memory_monitor
from ..utils.cleanup import get_resource_cleaner, ResourceType

logger = get_logger("scraping.browser")


@dataclass
class BrowserPoolStats:
    """Statistiques du pool de navigateurs."""
    total_browsers: int = 0
    active_browsers: int = 0
    available_browsers: int = 0
    total_requests: int = 0
    avg_wait_time_ms: float = 0.0
    peak_usage: int = 0


class BrowserPool:
    """Pool de navigateurs pour améliorer les performances de concurrence."""
    
    def __init__(self, pool_size: int = None):
        self.pool_size = pool_size or min(settings.max_concurrent_requests, 5)
        self.browsers: List[Browser] = []
        self.available_browsers = asyncio.Queue(maxsize=self.pool_size)
        self.playwright: Optional[Playwright] = None
        self._pool_lock = asyncio.Lock()
        self._is_initialized = False
        self._stats = BrowserPoolStats()
        self._wait_times = deque(maxlen=100)  # Garder les 100 derniers temps d'attente
        
        # Monitoring mémoire et nettoyage
        self.memory_monitor = get_memory_monitor()
        self.resource_cleaner = get_resource_cleaner()
        
    async def initialize(self):
        """Initialise le pool de navigateurs."""
        if self._is_initialized:
            return
            
        async with self._pool_lock:
            if self._is_initialized:
                return
                
            try:
                logger.info(f"🚀 Initialisation du pool de {self.pool_size} navigateurs...")
                self.playwright = await async_playwright().start()
                
                # Créer tous les navigateurs du pool
                for i in range(self.pool_size):
                    browser = await self.playwright.chromium.launch(
                        headless=True,
                        args=[
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--disable-features=VizDisplayCompositor",
                            "--disable-background-timer-throttling",
                            "--disable-backgrounding-occluded-windows",
                            "--disable-renderer-backgrounding",
                            "--memory-pressure-off",  # Désactiver la gestion mémoire agressive
                            "--max_old_space_size=512",  # Limiter la mémoire JS
                        ],
                    )
                    self.browsers.append(browser)
                    await self.available_browsers.put(browser)
                    
                    # Tracker le navigateur pour surveillance mémoire
                    self.resource_cleaner.tracker.track_resource(
                        browser, ResourceType.BROWSER_CONTEXTS, 50 * 1024 * 1024  # ~50MB par navigateur
                    )
                    
                self._stats.total_browsers = len(self.browsers)
                self._stats.available_browsers = self.available_browsers.qsize()
                self._is_initialized = True
                
                logger.info(f"✅ Pool de {len(self.browsers)} navigateurs initialisé")
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'initialisation du pool: {e}")
                await self.cleanup()
                raise
                
    async def get_browser(self) -> Browser:
        """Récupère un navigateur disponible du pool."""
        if not self._is_initialized:
            await self.initialize()
            
        start_time = time.time()
        
        try:
            browser = await asyncio.wait_for(
                self.available_browsers.get(), 
                timeout=30.0  # Timeout de 30 secondes
            )
            
            wait_time_ms = (time.time() - start_time) * 1000
            self._wait_times.append(wait_time_ms)
            
            # Mettre à jour les statistiques
            self._stats.active_browsers += 1
            self._stats.available_browsers = self.available_browsers.qsize()
            self._stats.total_requests += 1
            self._stats.peak_usage = max(self._stats.peak_usage, self._stats.active_browsers)
            self._stats.avg_wait_time_ms = sum(self._wait_times) / len(self._wait_times)
            
            logger.debug(f"📊 Navigateur acquis (attente: {wait_time_ms:.1f}ms, actifs: {self._stats.active_browsers})")
            return browser
            
        except asyncio.TimeoutError:
            raise Exception("Timeout: aucun navigateur disponible dans le pool")
            
    async def return_browser(self, browser: Browser):
        """Remet un navigateur dans le pool."""
        try:
            # Vérifier que le navigateur est encore valide
            if browser.is_connected():
                await self.available_browsers.put(browser)
                self._stats.active_browsers -= 1
                self._stats.available_browsers = self.available_browsers.qsize()
                logger.debug(f"📊 Navigateur rendu (actifs: {self._stats.active_browsers})")
            else:
                # Navigateur déconnecté, le remplacer
                await self._replace_browser(browser)
                
        except Exception as e:
            logger.warning(f"Erreur lors du retour du navigateur: {e}")
            await self._replace_browser(browser)
            
    async def _replace_browser(self, old_browser: Browser):
        """Remplace un navigateur défaillant."""
        try:
            # Fermer l'ancien navigateur
            if old_browser and old_browser.is_connected():
                await old_browser.close()
                
            # Créer un nouveau navigateur
            new_browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-features=VizDisplayCompositor",
                ],
            )
            
            # L'ajouter au pool
            await self.available_browsers.put(new_browser)
            
            # Mettre à jour la liste des navigateurs
            if old_browser in self.browsers:
                index = self.browsers.index(old_browser)
                self.browsers[index] = new_browser
            else:
                self.browsers.append(new_browser)
                
            self._stats.active_browsers -= 1
            self._stats.available_browsers = self.available_browsers.qsize()
            
            logger.info("🔄 Navigateur remplacé dans le pool")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du remplacement du navigateur: {e}")
            
    async def get_stats(self) -> BrowserPoolStats:
        """Retourne les statistiques du pool."""
        self._stats.available_browsers = self.available_browsers.qsize()
        return self._stats
        
    async def cleanup(self):
        """Nettoie tous les navigateurs du pool."""
        async with self._pool_lock:
            logger.info("🧹 Nettoyage du pool de navigateurs...")
            
            # Fermer tous les navigateurs
            for browser in self.browsers:
                try:
                    if browser and browser.is_connected():
                        await browser.close()
                except Exception as e:
                    logger.warning(f"Erreur lors de la fermeture du navigateur: {e}")
                    
            self.browsers.clear()
            
            # Vider la queue
            while not self.available_browsers.empty():
                try:
                    self.available_browsers.get_nowait()
                except asyncio.QueueEmpty:
                    break
                    
            # Arrêter Playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    logger.warning(f"Erreur lors de l'arrêt de Playwright: {e}")
                finally:
                    self.playwright = None
                    
            self._is_initialized = False
            self._stats = BrowserPoolStats()
            
            logger.info("✅ Pool de navigateurs nettoyé")
            
    @asynccontextmanager
    async def get_browser_context(self, **options):
        """Gestionnaire de contexte pour obtenir un navigateur du pool."""
        browser = None
        try:
            browser = await self.get_browser()
            yield browser
        finally:
            if browser:
                await self.return_browser(browser)


class BrowserManager:
    """Gestionnaire de navigateur Playwright optimisé avec pool."""

    def __init__(self, pool_size: int = None):
        self.browser_pool = BrowserPool(pool_size)
        self._context_pool: List[BrowserContext] = []
        self._available_contexts = asyncio.Queue(maxsize=10)  # Pool de contextes
        self._context_lock = asyncio.Lock()

    async def initialize(self):
        """Initialise le gestionnaire et le pool de navigateurs."""
        await self.browser_pool.initialize()
        
    async def cleanup(self):
        """Nettoie le pool de navigateurs et les contextes."""
        # Nettoyer les contextes
        while not self._available_contexts.empty():
            try:
                context = self._available_contexts.get_nowait()
                if context:
                    await context.close()
            except (asyncio.QueueEmpty, Exception) as e:
                if not isinstance(e, asyncio.QueueEmpty):
                    logger.warning(f"Erreur lors du nettoyage du contexte: {e}")
                break
                
        # Nettoyer le pool de navigateurs
        await self.browser_pool.cleanup()
        
    async def get_stats(self) -> dict:
        """Retourne les statistiques du gestionnaire."""
        pool_stats = await self.browser_pool.get_stats()
        return {
            "browser_pool": {
                "total_browsers": pool_stats.total_browsers,
                "active_browsers": pool_stats.active_browsers,
                "available_browsers": pool_stats.available_browsers,
                "total_requests": pool_stats.total_requests,
                "avg_wait_time_ms": pool_stats.avg_wait_time_ms,
                "peak_usage": pool_stats.peak_usage,
            },
            "context_pool": {
                "available_contexts": self._available_contexts.qsize(),
                "total_contexts": len(self._context_pool),
            }
        }

    @asynccontextmanager
    async def create_context(self, **options):
        """Crée un contexte de navigateur temporaire avec pool."""
        if not self.browser_pool._is_initialized:
            await self.browser_pool.initialize()

        # Options par défaut optimisées
        default_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": settings.user_agent,
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "accept_downloads": False,  # Désactiver les téléchargements
            "bypass_csp": True,  # Contourner CSP pour l'extraction
        }
        default_options.update(options)

        # Essayer de réutiliser un contexte existant
        context = None
        try:
            context = self._available_contexts.get_nowait()
            logger.debug("♻️ Contexte réutilisé du pool")
        except asyncio.QueueEmpty:
            # Créer un nouveau contexte
            async with self.browser_pool.get_browser_context() as browser:
                context = await browser.new_context(**default_options)
                logger.debug("📄 Nouveau contexte créé")

        try:
            yield context
        finally:
            if context:
                try:
                    # Nettoyer les pages ouvertes
                    for page in context.pages:
                        await page.close()
                    
                    # Remettre le contexte dans le pool si il y a de la place
                    if self._available_contexts.qsize() < 5:
                        await self._available_contexts.put(context)
                        logger.debug("♻️ Contexte remis dans le pool")
                    else:
                        await context.close()
                        logger.debug("🧹 Contexte fermé (pool plein)")
                except Exception as e:
                    logger.warning(f"Erreur lors de la gestion du contexte: {e}")
                    try:
                        await context.close()
                    except:
                        pass

    @asynccontextmanager
    async def create_page(
        self, context: Optional[BrowserContext] = None, **context_options
    ):
        """Crée une page temporaire optimisée."""
        if context:
            # Utiliser le contexte fourni
            page = await context.new_page()
            try:
                # Configurer la page pour les performances
                await self._optimize_page(page)
                yield page
            finally:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Erreur lors de la fermeture de la page: {e}")
        else:
            # Créer un nouveau contexte
            async with self.create_context(**context_options) as ctx:
                page = await ctx.new_page()
                try:
                    # Configurer la page pour les performances
                    await self._optimize_page(page)
                    yield page
                finally:
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Erreur lors de la fermeture de la page: {e}")
                        
    async def _optimize_page(self, page: Page):
        """Optimise une page pour les performances."""
        # Désactiver les animations CSS
        await page.add_style_tag(content="""
            *, *::before, *::after {
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
            }
        """)
        
        # Configurer les timeouts
        page.set_default_timeout(settings.request_timeout * 1000)
        page.set_default_navigation_timeout(settings.request_timeout * 1000)


class PageScraper:
    """Scraper pour une page web spécifique avec optimisations."""

    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.logger = get_logger("scraping.page")
        self._request_cache = {}  # Cache simple pour les requêtes récentes
        self._cache_ttl = 300  # 5 minutes de cache

    async def fetch_page(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_for_timeout: int = 10000,
        **page_options,
    ) -> dict[str, Any]:
        """
        Récupère le contenu d'une page web.

        Args:
            url: URL à scraper
            wait_for_selector: Sélecteur CSS à attendre
            wait_for_timeout: Timeout en millisecondes
            **page_options: Options additionnelles pour le contexte

        Returns:
            Dict contenant le HTML, les métadonnées et les métriques
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info(f"🌐 Début du scraping: {url}")

            # Valider l'URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"URL invalide: {url}")

            async with self.browser_manager.create_page(**page_options) as page:
                # Configuration de la page (déjà optimisée par create_page)
                await self._configure_page(page)

                # Navigation vers la page
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=settings.request_timeout * 1000,
                )

                if not response:
                    raise Exception("Aucune réponse reçue du serveur")

                # Vérifier le statut HTTP
                if response.status >= 400:
                    raise Exception(
                        f"Erreur HTTP {response.status}: {response.status_text}"
                    )

                # Attendre un sélecteur spécifique si demandé
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(
                            wait_for_selector, timeout=wait_for_timeout
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Sélecteur '{wait_for_selector}' non trouvé: {e}"
                        )

                # Attendre que la page soit complètement chargée
                await page.wait_for_load_state("networkidle", timeout=wait_for_timeout)

                # Extraire le contenu
                content_data = await self._extract_content(page)

                # Calculer les métriques
                end_time = asyncio.get_event_loop().time()
                execution_time = int((end_time - start_time) * 1000)

                result = {
                    "url": url,
                    "status_code": response.status,
                    "html": content_data["html"],
                    "title": content_data["title"],
                    "meta": content_data["meta"],
                    "links": content_data["links"],
                    "images": content_data["images"],
                    "execution_time_ms": execution_time,
                    "content_size": len(content_data["html"]),
                    "timestamp": asyncio.get_event_loop().time(),
                }

                self.logger.info(
                    f"✅ Scraping terminé: {url} "
                    f"({execution_time}ms, {result['content_size']} bytes)"
                )

                return result

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            execution_time = int((end_time - start_time) * 1000)

            self.logger.error(f"❌ Erreur lors du scraping de {url}: {e}")

            return {
                "url": url,
                "status_code": None,
                "html": None,
                "title": None,
                "meta": {},
                "links": [],
                "images": [],
                "execution_time_ms": execution_time,
                "content_size": 0,
                "timestamp": asyncio.get_event_loop().time(),
                "error": str(e),
            }

    async def _configure_page(self, page: Page):
        """Configure la page avec les bonnes options optimisées."""
        # Bloquer les ressources non nécessaires pour accélérer le chargement
        await page.route("**/*", self._handle_route)
        
        # Configurer l'intercept des requêtes pour le cache
        await page.route("**/*", self._handle_cache_route)

        # Définir des timeouts (déjà fait dans _optimize_page)
        # page.set_default_timeout(settings.request_timeout * 1000)
        # page.set_default_navigation_timeout(settings.request_timeout * 1000)

    async def _handle_route(self, route, request):
        """Gère le routage des requêtes pour optimiser le chargement."""
        # Bloquer certains types de ressources non critiques
        resource_type = request.resource_type
        url = request.url

        # Bloquer complètement les images non essentielles
        if resource_type == "image" and "favicon" not in url.lower():
            await route.abort()
            return
            
        # Bloquer les médias lourds
        if resource_type in ["media", "font"]:
            await route.abort()
            return

        # Bloquer les trackers et publicités (liste étendue)
        blocked_domains = [
            "google-analytics.com", "googletagmanager.com", "facebook.com",
            "doubleclick.net", "googlesyndication.com", "amazon-adsystem.com",
            "adsystem.amazon.com", "twitter.com", "linkedin.com", "instagram.com",
            "pinterest.com", "tiktok.com", "snapchat.com", "hotjar.com",
            "fullstory.com", "intercom.io", "zendesk.com", "drift.com"
        ]

        if any(domain in url for domain in blocked_domains):
            await route.abort()
            return
            
        # Bloquer les requêtes de tracking par pattern
        if any(pattern in url for pattern in ["analytics", "tracking", "pixel", "beacon"]):
            await route.abort()
            return

        # Continuer avec la requête
        await route.continue_()
        
    async def _handle_cache_route(self, route, request):
        """Gère le cache des requêtes pour éviter les doublons."""
        url = request.url
        
        # Vérifier le cache pour les ressources statiques
        if request.resource_type in ["stylesheet", "script", "font"]:
            cache_key = f"{url}_{request.resource_type}"
            if cache_key in self._request_cache:
                cached_time = self._request_cache[cache_key]
                if time.time() - cached_time < self._cache_ttl:
                    # Requête récente, on peut l'ignorer pour certains types
                    if request.resource_type == "font":
                        await route.abort()
                        return
                        
            # Mettre en cache
            self._request_cache[cache_key] = time.time()
            
        await route.continue_()

    async def _extract_content(self, page: Page) -> dict[str, Any]:
        """Extrait le contenu principal de la page."""
        try:
            # Exécuter du JavaScript pour extraire les données
            content_data = await page.evaluate("""
                () => {
                    // Titre de la page
                    const title = document.title || '';

                    // Métadonnées
                    const meta = {};
                    document.querySelectorAll('meta').forEach(el => {
                        const name = el.getAttribute('name') || el.getAttribute('property');
                        const content = el.getAttribute('content');
                        if (name && content) {
                            meta[name] = content;
                        }
                    });

                    // Liens
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(el => {
                        links.push({
                            text: el.textContent.trim(),
                            href: el.href,
                            title: el.title || ''
                        });
                    });

                    // Images
                    const images = [];
                    document.querySelectorAll('img[src]').forEach(el => {
                        images.push({
                            src: el.src,
                            alt: el.alt || '',
                            title: el.title || ''
                        });
                    });

                    return {
                        title,
                        meta,
                        links: links.slice(0, 50), // Limiter à 50 liens
                        images: images.slice(0, 20) // Limiter à 20 images
                    };
                }
            """)

            # HTML complet de la page
            html = await page.content()

            # Limiter la taille du contenu
            if len(html) > settings.max_content_size:
                self.logger.warning(
                    f"Contenu tronqué: {len(html)} > {settings.max_content_size} bytes"
                )
                html = html[: settings.max_content_size]

            return {
                "html": html,
                "title": content_data.get("title", ""),
                "meta": content_data.get("meta", {}),
                "links": content_data.get("links", []),
                "images": content_data.get("images", []),
            }

        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction du contenu: {e}")

            # Fallback : récupérer au moins le HTML
            try:
                html = await page.content()
                return {
                    "html": html[: settings.max_content_size],
                    "title": "",
                    "meta": {},
                    "links": [],
                    "images": [],
                }
            except Exception:
                return {
                    "html": "",
                    "title": "",
                    "meta": {},
                    "links": [],
                    "images": [],
                }


# Instance globale du gestionnaire de navigateur avec pool optimisé
browser_manager = BrowserManager(pool_size=min(settings.max_concurrent_requests, 3))


async def cleanup_browser():
    """Nettoie le pool de navigateurs global."""
    await browser_manager.cleanup()
    
    
async def get_browser_stats():
    """Retourne les statistiques du pool de navigateurs."""
    return await browser_manager.get_stats()


def get_browser_pool():
    """Retourne l'instance du gestionnaire de navigateurs."""
    return browser_manager


# Fonction utilitaire pour scraper rapidement une URL
async def quick_scrape(url: str, **options) -> dict[str, Any]:
    """
    Scrape rapidement une URL.

    Args:
        url: URL à scraper
        **options: Options additionnelles

    Returns:
        Données extraites de la page
    """
    scraper = PageScraper(browser_manager)
    return await scraper.fetch_page(url, **options)
