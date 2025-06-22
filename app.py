"""Application Reflex moderne pour Scrapinium."""

import reflex as rx
import asyncio
import httpx
from typing import List, Dict, Any

# Configuration API
API_BASE_URL = "http://localhost:8000"

class ScrapiniumState(rx.State):
    """État de l'application Scrapinium."""
    
    # Formulaire de scraping
    url: str = ""
    task_type: str = "content_extraction"
    
    # État du scraping
    is_scraping: bool = False
    current_result: str = ""
    
    # Stats système
    system_stats: Dict[str, Any] = {}
    
    # Liste des tâches
    recent_tasks: List[Dict[str, Any]] = []
    
    async def start_scraping(self):
        """Lance une tâche de scraping."""
        if not self.url:
            self.current_result = "❌ Veuillez entrer une URL valide"
            return
            
        self.is_scraping = True
        self.current_result = "🔄 Scraping en cours..."
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/scrape",
                    json={
                        "url": self.url,
                        "task_type": self.task_type,
                        "priority": "normal"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.current_result = f"""✅ Scraping réussi !
                    
Task ID: {result.get('task_id', 'N/A')}
Message: {result.get('message', 'N/A')}
Status: {response.status_code}
URL: {self.url}
Timestamp: {result.get('timestamp', 'N/A')}"""
                    
                    # Ajouter à l'historique
                    self.recent_tasks.insert(0, {
                        "url": self.url,
                        "status": "success",
                        "task_id": result.get('task_id', 'N/A'),
                        "timestamp": result.get('timestamp', 'N/A')
                    })
                    
                    # Garder seulement les 10 dernières tâches
                    self.recent_tasks = self.recent_tasks[:10]
                    
                else:
                    self.current_result = f"❌ Erreur {response.status_code}: {response.text}"
                    
        except Exception as e:
            self.current_result = f"❌ Erreur de connexion: {str(e)}"
        
        finally:
            self.is_scraping = False
    
    async def load_stats(self):
        """Charge les statistiques système."""
        try:
            async with httpx.AsyncClient() as client:
                # Health check
                health_response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
                health_data = health_response.json() if health_response.status_code == 200 else {}
                
                # Stats générales
                stats_response = await client.get(f"{API_BASE_URL}/stats", timeout=5.0)
                stats_data = stats_response.json() if stats_response.status_code == 200 else {}
                
                self.system_stats = {
                    "health": health_data,
                    "stats": stats_data,
                    "timestamp": "Maintenant"
                }
                
        except Exception as e:
            self.system_stats = {"error": f"Erreur de chargement: {str(e)}"}


def header() -> rx.Component:
    """Header de l'application."""
    return rx.hstack(
        rx.heading("🕸️ Scrapinium", size="lg", color="blue.500"),
        rx.spacer(),
        rx.badge("Prototype v2.0", color_scheme="green"),
        width="100%",
        padding="1rem",
        bg="gray.900",
        border_bottom="1px solid",
        border_color="gray.700",
        position="sticky",
        top="0",
        z_index="999"
    )


def scraping_form() -> rx.Component:
    """Formulaire de scraping."""
    return rx.card(
        rx.vstack(
            rx.heading("🚀 Nouveau Scraping", size="md", color="blue.400"),
            
            rx.vstack(
                rx.text("URL à scraper:", font_weight="bold"),
                rx.input(
                    placeholder="https://example.com",
                    value=ScrapiniumState.url,
                    on_change=ScrapiniumState.set_url,
                    width="100%"
                ),
                
                rx.text("Type de tâche:", font_weight="bold"),
                rx.select(
                    ["content_extraction", "data_extraction", "full_page"],
                    value=ScrapiniumState.task_type,
                    on_change=ScrapiniumState.set_task_type,
                    width="100%"
                ),
                
                rx.button(
                    rx.cond(
                        ScrapiniumState.is_scraping,
                        "🔄 Scraping...",
                        "🚀 Lancer le Scraping"
                    ),
                    on_click=ScrapiniumState.start_scraping,
                    disabled=ScrapiniumState.is_scraping,
                    color_scheme="blue",
                    width="100%",
                    size="lg"
                ),
                
                spacing="1rem",
                width="100%"
            ),
            
            spacing="1rem",
            width="100%"
        ),
        width="100%",
        bg="gray.800",
        border="1px solid",
        border_color="gray.600"
    )


def system_status() -> rx.Component:
    """Statut du système."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("📊 Statut Système", size="md", color="green.400"),
                rx.button(
                    "🔄 Actualiser",
                    on_click=ScrapiniumState.load_stats,
                    size="sm",
                    color_scheme="green"
                ),
                justify="between",
                width="100%"
            ),
            
            rx.cond(
                ScrapiniumState.system_stats,
                rx.vstack(
                    rx.text(f"API: {ScrapiniumState.system_stats.get('health', {}).get('api', 'unknown')}"),
                    rx.text(f"Ollama: {ScrapiniumState.system_stats.get('health', {}).get('ollama', 'unknown')}"),
                    rx.text(f"Database: {ScrapiniumState.system_stats.get('health', {}).get('database', 'unknown')}"),
                    rx.text(f"Tâches actives: {ScrapiniumState.system_stats.get('stats', {}).get('tasks', {}).get('active', 0)}"),
                    spacing="0.5rem",
                    align="start",
                    width="100%"
                ),
                rx.text("🔄 Chargement des stats...")
            ),
            
            spacing="1rem",
            width="100%"
        ),
        width="100%",
        bg="gray.800",
        border="1px solid",
        border_color="gray.600"
    )


def results_panel() -> rx.Component:
    """Panel des résultats."""
    return rx.card(
        rx.vstack(
            rx.heading("📋 Résultats", size="md", color="purple.400"),
            
            rx.text_area(
                value=ScrapiniumState.current_result,
                placeholder="Les résultats apparaîtront ici...",
                width="100%",
                height="200px",
                is_read_only=True,
                bg="gray.900",
                border="1px solid",
                border_color="gray.600"
            ),
            
            spacing="1rem",
            width="100%"
        ),
        width="100%",
        bg="gray.800",
        border="1px solid",
        border_color="gray.600"
    )


def recent_tasks_panel() -> rx.Component:
    """Panel des tâches récentes."""
    return rx.card(
        rx.vstack(
            rx.heading("📜 Tâches Récentes", size="md", color="orange.400"),
            
            rx.cond(
                ScrapiniumState.recent_tasks,
                rx.vstack(
                    rx.foreach(
                        ScrapiniumState.recent_tasks,
                        lambda task: rx.box(
                            rx.text(f"🌐 {task['url']}", font_weight="bold"),
                            rx.text(f"📝 ID: {task['task_id']}"),
                            rx.text(f"⏰ {task['timestamp']}"),
                            padding="0.5rem",
                            border="1px solid",
                            border_color="gray.600",
                            border_radius="md",
                            bg="gray.900"
                        )
                    ),
                    spacing="0.5rem",
                    width="100%"
                ),
                rx.text("Aucune tâche récente", style={"font-style": "italic"})
            ),
            
            spacing="1rem",
            width="100%"
        ),
        width="100%",
        bg="gray.800",
        border="1px solid",
        border_color="gray.600"
    )


def index() -> rx.Component:
    """Page principale."""
    return rx.box(
        header(),
        
        rx.container(
            rx.vstack(
                rx.grid(
                    scraping_form(),
                    system_status(),
                    columns=[1, 2],
                    spacing="2rem",
                    width="100%"
                ),
                
                results_panel(),
                
                recent_tasks_panel(),
                
                spacing="2rem",
                width="100%"
            ),
            max_width="1200px",
            padding="2rem"
        ),
        
        bg="gray.900",
        color="white",
        min_height="100vh"
    )


# Configuration de l'app
app = rx.App(
    style={
        "font_family": "Inter, system-ui, sans-serif",
    }
)

# Ajouter la page
app.add_page(index, route="/")

# Auto-charger les stats au démarrage
app.add_page(
    index,
    route="/",
    on_load=ScrapiniumState.load_stats
)