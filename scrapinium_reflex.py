"""Interface Reflex simplifiée pour Scrapinium."""

import reflex as rx
import httpx
from typing import List, Dict, Any


class ScrapiniumState(rx.State):
    """État principal de l'application."""
    
    # Formulaire
    url: str = ""
    task_type: str = "content_extraction"
    
    # Résultats
    is_loading: bool = False
    result_text: str = "Aucun résultat pour le moment..."
    
    # Stats
    api_status: str = "Inconnu"
    db_status: str = "Inconnu"
    
    def set_url(self, value: str):
        """Met à jour l'URL."""
        self.url = value
    
    def set_task_type(self, value: str):
        """Met à jour le type de tâche."""
        self.task_type = value
    
    async def start_scraping(self):
        """Lance le scraping."""
        if not self.url:
            self.result_text = "❌ Veuillez entrer une URL"
            return
        
        self.is_loading = True
        self.result_text = "🔄 Scraping en cours..."
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/scrape",
                    json={
                        "url": self.url,
                        "task_type": self.task_type,
                        "priority": "normal"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.result_text = f"""✅ Scraping réussi !
                    
Task ID: {data.get('task_id', 'N/A')}
Message: {data.get('message', 'N/A')}
URL: {self.url}
Status: {response.status_code}"""
                else:
                    self.result_text = f"❌ Erreur {response.status_code}"
                    
        except Exception as e:
            self.result_text = f"❌ Erreur: {str(e)}"
        
        self.is_loading = False
    
    async def load_stats(self):
        """Charge les statistiques."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    self.api_status = data.get("api", "Erreur")
                    self.db_status = data.get("database", "Erreur")
                else:
                    self.api_status = "Erreur"
                    self.db_status = "Erreur"
        except:
            self.api_status = "Déconnecté"
            self.db_status = "Déconnecté"


def index():
    """Page principale."""
    return rx.center(
        rx.vstack(
            # Header
            rx.heading("🕸️ Scrapinium - Interface Reflex", size="2xl", color="blue"),
            rx.text("Web Scraping Intelligent", color="gray"),
            
            rx.divider(),
            
            # Grille principale
            rx.hstack(
                # Colonne gauche - Formulaire
                rx.vstack(
                    rx.card(
                        rx.vstack(
                            rx.heading("🚀 Nouveau Scraping", size="lg"),
                            
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
                                    ScrapiniumState.is_loading,
                                    "🔄 Scraping...",
                                    "🚀 Lancer le Scraping"
                                ),
                                on_click=ScrapiniumState.start_scraping,
                                disabled=ScrapiniumState.is_loading,
                                width="100%",
                                color_scheme="blue"
                            ),
                            
                            spacing="4",
                            width="100%"
                        ),
                        width="100%"
                    ),
                    
                    # Stats système
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.heading("📊 Système", size="lg"),
                                rx.button(
                                    "🔄",
                                    on_click=ScrapiniumState.load_stats,
                                    size="sm"
                                ),
                                justify="between",
                                width="100%"
                            ),
                            
                            rx.text(f"API: {ScrapiniumState.api_status}"),
                            rx.text(f"Database: {ScrapiniumState.db_status}"),
                            
                            spacing="2",
                            width="100%"
                        ),
                        width="100%"
                    ),
                    
                    spacing="4",
                    width="400px"
                ),
                
                # Colonne droite - Résultats
                rx.vstack(
                    rx.card(
                        rx.vstack(
                            rx.heading("📋 Résultats", size="lg"),
                            
                            rx.text_area(
                                value=ScrapiniumState.result_text,
                                width="100%",
                                height="400px",
                                is_read_only=True
                            ),
                            
                            spacing="4",
                            width="100%"
                        ),
                        width="100%"
                    ),
                    
                    width="500px"
                ),
                
                spacing="8",
                align="start"
            ),
            
            spacing="6",
            width="100%",
            max_width="1000px"
        ),
        padding="4"
    )


# Créer l'app
app = rx.App()
app.add_page(index, route="/")


if __name__ == "__main__":
    # Pour le développement local
    app.run(host="0.0.0.0", port=3000)