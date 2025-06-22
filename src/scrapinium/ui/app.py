"""Application Reflex principale pour Scrapinium."""

import asyncio
from typing import Any, Optional

import httpx
import reflex as rx

from ..config import settings
from ..models.enums import OutputFormat
from .components import ScrapiniumComponents
from .styles import BaseStyles, Colors, Layout


class ScrapiniumState(rx.State):
    """État global de l'application Scrapinium."""

    # Configuration de scraping
    url: str = ""
    output_format: str = OutputFormat.MARKDOWN.value
    use_llm: bool = True

    # État des tâches
    tasks: list[dict[str, Any]] = []
    current_task: Optional[dict[str, Any]] = None
    is_scraping: bool = False
    scraping_progress: float = 0
    scraping_message: str = ""

    # État de l'interface
    show_notification: bool = False
    notification_message: str = ""
    notification_type: str = "info"
    active_tab: str = "scraper"

    # Résultats
    current_result: str = ""
    show_result_modal: bool = False

    def set_url(self, value: str):
        """Met à jour l'URL."""
        self.url = value

    def set_output_format(self, value: str):
        """Met à jour le format de sortie."""
        self.output_format = value

    def toggle_llm(self):
        """Active/désactive l'utilisation du LLM."""
        self.use_llm = not self.use_llm

    def set_active_tab(self, tab: str):
        """Change l'onglet actif."""
        self.active_tab = tab

    async def start_scraping(self):
        """Démarre le scraping d'une URL."""
        if not self.url.strip():
            self.show_notification_message("Veuillez saisir une URL", "error")
            return

        self.is_scraping = True
        self.scraping_progress = 0
        self.scraping_message = "Initialisation..."

        try:
            # Appeler l'API FastAPI
            async with httpx.AsyncClient() as client:
                # Démarrer le scraping
                response = await client.post(
                    f"http://localhost:{settings.port}/scrape",
                    json={
                        "url": self.url,
                        "output_format": self.output_format,
                        "llm_provider": "ollama" if self.use_llm else None,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    task_id = result["data"]["task_id"]

                    # Suivre le progrès de la tâche
                    await self.track_task_progress(task_id, client)
                else:
                    self.show_notification_message(
                        "Erreur lors du démarrage du scraping", "error"
                    )
                    self.is_scraping = False

        except Exception as e:
            self.show_notification_message(f"Erreur de connexion: {str(e)}", "error")
            self.is_scraping = False

    async def track_task_progress(self, task_id: str, client: httpx.AsyncClient):
        """Suit le progrès d'une tâche de scraping."""
        try:
            while self.is_scraping:
                # Vérifier le statut de la tâche
                response = await client.get(
                    f"http://localhost:{settings.port}/scrape/{task_id}",
                    timeout=10.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    task_data = result["data"]

                    self.scraping_progress = task_data.get("progress", 0)
                    self.scraping_message = task_data.get("message", "En cours...")

                    if task_data["status"] in ["completed", "failed", "cancelled"]:
                        # Tâche terminée
                        await self.handle_task_completion(task_id, task_data, client)
                        break

                # Attendre avant la prochaine vérification
                await asyncio.sleep(2)

        except Exception as e:
            self.show_notification_message(f"Erreur de suivi: {str(e)}", "error")
            self.is_scraping = False

    async def handle_task_completion(
        self, task_id: str, task_data: dict[str, Any], client: httpx.AsyncClient
    ):
        """Gère la fin d'une tâche de scraping."""
        try:
            if task_data["status"] == "completed":
                # Récupérer le résultat
                response = await client.get(
                    f"http://localhost:{settings.port}/scrape/{task_id}/result",
                    timeout=10.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    result_data = result["data"]

                    # Ajouter la tâche aux résultats
                    new_task = {
                        "id": task_id,
                        "url": task_data["url"],
                        "status": "completed",
                        "output_format": task_data["output_format"],
                        "created_at": "maintenant",
                        "progress": 100,
                        "result": result_data["content"],
                    }

                    self.tasks = [new_task] + self.tasks
                    self.current_result = result_data["content"]
                    self.show_notification_message(
                        "Scraping terminé avec succès!", "success"
                    )
                else:
                    self.show_notification_message(
                        "Erreur lors de la récupération du résultat", "error"
                    )

            elif task_data["status"] == "failed":
                error_msg = task_data.get("error", "Erreur inconnue")
                self.show_notification_message(f"Scraping échoué: {error_msg}", "error")

            elif task_data["status"] == "cancelled":
                self.show_notification_message("Scraping annulé", "warning")

        except Exception as e:
            self.show_notification_message(
                f"Erreur lors de la finalisation: {str(e)}", "error"
            )

        finally:
            self.is_scraping = False
            self.url = ""

    async def load_tasks(self):
        """Charge la liste des tâches depuis l'API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{settings.port}/tasks",
                    timeout=10.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    api_tasks = result["data"]["tasks"]

                    # Convertir les tâches de l'API au format de l'interface
                    self.tasks = [
                        {
                            "id": task.get("id", ""),
                            "url": task.get("url", ""),
                            "status": task.get("status", "unknown"),
                            "output_format": task.get("output_format", ""),
                            "created_at": task.get("created_at", ""),
                            "progress": task.get("progress", 0),
                        }
                        for task in api_tasks
                    ]

        except Exception as e:
            self.show_notification_message(
                f"Erreur de chargement des tâches: {str(e)}", "error"
            )

    def show_notification_message(self, message: str, type_: str = "info"):
        """Affiche une notification."""
        self.notification_message = message
        self.notification_type = type_
        self.show_notification = True

    def hide_notification(self):
        """Cache la notification."""
        self.show_notification = False

    async def show_result(self, task_id: str):
        """Affiche le résultat d'une tâche."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{settings.port}/scrape/{task_id}/result",
                    timeout=10.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    result_data = result["data"]
                    self.current_result = result_data["content"]
                    self.show_result_modal = True
                else:
                    self.show_notification_message("Résultat non disponible", "error")

        except Exception as e:
            self.show_notification_message(f"Erreur de récupération: {str(e)}", "error")

    def close_result_modal(self):
        """Ferme la modal de résultat."""
        self.show_result_modal = False


def navbar() -> rx.Component:
    """Barre de navigation."""
    return rx.box(
        rx.hstack(
            ScrapiniumComponents.logo("28px"),
            rx.spacer(),
            rx.hstack(
                rx.link(
                    rx.button(
                        "📚 Docs",
                        style=BaseStyles.button_secondary(),
                    ),
                    href="/docs",
                ),
                rx.button(
                    "⚙️ Paramètres",
                    style=BaseStyles.button_secondary(),
                ),
                spacing="12px",
            ),
            align_items="center",
            width="100%",
            padding="0 24px",
            height="64px",
        ),
        style={
            "background": Colors.BG_SECONDARY,
            "border_bottom": f"1px solid {Colors.BORDER}",
            "position": "sticky",
            "top": "0",
            "z_index": "100",
        },
    )


def scraper_form() -> rx.Component:
    """Formulaire de scraping principal."""
    return ScrapiniumComponents.card(
        [
            rx.vstack(
                # Champ URL
                rx.vstack(
                    rx.text("URL à scraper", **BaseStyles.text("caption")),
                    ScrapiniumComponents.input_field(
                        placeholder="https://example.com/article",
                        value=ScrapiniumState.url,
                        on_change=ScrapiniumState.set_url,
                        disabled=ScrapiniumState.is_scraping,
                    ),
                    align_items="start",
                    spacing="8px",
                    width="100%",
                ),
                # Options
                rx.hstack(
                    # Format de sortie
                    rx.vstack(
                        rx.text("Format de sortie", **BaseStyles.text("caption")),
                        ScrapiniumComponents.select_field(
                            options=[
                                {
                                    "label": "📝 Markdown",
                                    "value": OutputFormat.MARKDOWN.value,
                                },
                                {"label": "📄 JSON", "value": OutputFormat.JSON.value},
                                {"label": "🏷️ XML", "value": OutputFormat.XML.value},
                                {"label": "📊 CSV", "value": OutputFormat.CSV.value},
                                {"label": "📋 HTML", "value": OutputFormat.HTML.value},
                                {
                                    "label": "📃 Texte",
                                    "value": OutputFormat.PLAIN_TEXT.value,
                                },
                            ],
                            value=ScrapiniumState.output_format,
                            on_change=ScrapiniumState.set_output_format,
                        ),
                        align_items="start",
                        spacing="8px",
                        flex="1",
                    ),
                    # Option LLM
                    rx.vstack(
                        rx.text("Structuration IA", **BaseStyles.text("caption")),
                        rx.hstack(
                            rx.switch(
                                checked=ScrapiniumState.use_llm,
                                on_change=ScrapiniumState.toggle_llm,
                            ),
                            rx.text(
                                "Ollama (local)",
                                **BaseStyles.text("small"),
                            ),
                            align_items="center",
                            spacing="8px",
                        ),
                        align_items="start",
                        spacing="8px",
                    ),
                    spacing="24px",
                    width="100%",
                ),
                # Barre de progression (si scraping en cours)
                rx.cond(
                    ScrapiniumState.is_scraping,
                    ScrapiniumComponents.progress_bar(
                        ScrapiniumState.scraping_progress,
                        ScrapiniumState.scraping_message,
                    ),
                ),
                # Bouton de scraping
                ScrapiniumComponents.primary_button(
                    "Lancer le scraping",
                    on_click=ScrapiniumState.start_scraping,
                    loading=ScrapiniumState.is_scraping,
                    disabled=ScrapiniumState.is_scraping,
                    icon="🚀",
                ),
                spacing="24px",
                align_items="start",
                width="100%",
            ),
        ],
        title="🕸️ Nouveau scraping",
        elevated=True,
    )


def recent_tasks() -> rx.Component:
    """Liste des tâches récentes."""
    return ScrapiniumComponents.card(
        [
            rx.cond(
                ScrapiniumState.tasks.length() > 0,
                rx.vstack(
                    rx.foreach(
                        ScrapiniumState.tasks,
                        lambda task: task_item(task),
                    ),
                    spacing="16px",
                    width="100%",
                ),
                ScrapiniumComponents.empty_state(
                    icon="📋",
                    title="Aucune tâche",
                    description="Vos tâches de scraping apparaîtront ici après avoir lancé votre premier scraping.",
                ),
            ),
        ],
        title="📋 Tâches récentes",
    )


def task_item(task: dict[str, Any]) -> rx.Component:
    """Élément de tâche individuel."""
    return rx.box(
        rx.hstack(
            # Informations de la tâche
            rx.vstack(
                rx.text(
                    task["url"][:60] + "..." if len(task["url"]) > 60 else task["url"],
                    font_weight="600",
                    color=Colors.TEXT_PRIMARY,
                    font_size="14px",
                ),
                rx.hstack(
                    ScrapiniumComponents.status_badge(task["status"]),
                    rx.text(
                        f"Format: {task['output_format']}",
                        **BaseStyles.text("small"),
                    ),
                    spacing="12px",
                ),
                align_items="start",
                spacing="4px",
                flex="1",
            ),
            # Actions
            rx.hstack(
                rx.button(
                    "👁️",
                    on_click=ScrapiniumState.show_result(task["id"]),
                    style={
                        "background": "transparent",
                        "border": f"1px solid {Colors.BORDER}",
                        "border_radius": "6px",
                        "padding": "8px",
                        "cursor": "pointer",
                        "_hover": {"background": Colors.BG_TERTIARY},
                    },
                ),
                rx.cond(
                    task["status"] == "completed",
                    rx.button(
                        "💾",
                        style={
                            "background": "transparent",
                            "border": f"1px solid {Colors.BORDER}",
                            "border_radius": "6px",
                            "padding": "8px",
                            "cursor": "pointer",
                            "_hover": {"background": Colors.BG_TERTIARY},
                        },
                    ),
                ),
                spacing="8px",
            ),
            justify="space-between",
            align_items="center",
            width="100%",
        ),
        style={
            "background": Colors.BG_TERTIARY,
            "border_radius": "8px",
            "padding": "16px",
            "border": f"1px solid {Colors.BORDER}",
            "transition": "all 0.2s ease",
            "_hover": {
                "background": Colors.BG_INPUT,
                "border_color": Colors.BORDER_LIGHT,
            },
        },
    )


def stats_overview() -> rx.Component:
    """Vue d'ensemble des statistiques."""
    return rx.hstack(
        ScrapiniumComponents.stats_card(
            title="Total des tâches",
            value="12",
            icon="📊",
            trend="+2 cette semaine",
        ),
        ScrapiniumComponents.stats_card(
            title="Succès",
            value="11",
            icon="✅",
            trend="91.7% taux de réussite",
        ),
        ScrapiniumComponents.stats_card(
            title="Tokens utilisés",
            value="2.4K",
            icon="🧠",
            trend="Ollama (gratuit)",
        ),
        spacing="24px",
        width="100%",
    )


def result_modal() -> rx.Component:
    """Modal d'affichage des résultats."""
    return rx.cond(
        ScrapiniumState.show_result_modal,
        rx.box(
            rx.box(
                rx.vstack(
                    # En-tête
                    rx.hstack(
                        rx.text(
                            "Résultat du scraping",
                            **BaseStyles.heading(2),
                        ),
                        rx.button(
                            "✕",
                            on_click=ScrapiniumState.close_result_modal,
                            style={
                                "background": "transparent",
                                "border": "none",
                                "color": Colors.TEXT_MUTED,
                                "cursor": "pointer",
                                "font_size": "18px",
                            },
                        ),
                        justify="space-between",
                        align_items="center",
                        width="100%",
                    ),
                    # Contenu
                    rx.box(
                        rx.text(
                            ScrapiniumState.current_result,
                            **BaseStyles.text("body"),
                            white_space="pre-wrap",
                        ),
                        style={
                            **BaseStyles.code_block(),
                            "max_height": "400px",
                            "overflow_y": "auto",
                        },
                        width="100%",
                    ),
                    # Actions
                    rx.hstack(
                        ScrapiniumComponents.secondary_button(
                            "Fermer",
                            on_click=ScrapiniumState.close_result_modal,
                        ),
                        ScrapiniumComponents.primary_button(
                            "Télécharger",
                            icon="💾",
                        ),
                        justify="end",
                        spacing="12px",
                        width="100%",
                    ),
                    spacing="24px",
                    width="100%",
                ),
                style={
                    **BaseStyles.card(elevated=True),
                    "width": "90vw",
                    "max_width": "800px",
                    "max_height": "80vh",
                    "overflow_y": "auto",
                },
            ),
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100vw",
                "height": "100vh",
                "background": "rgba(0, 0, 0, 0.8)",
                "z_index": "1000",
                **Layout.flex_center(),
            },
        ),
    )


def main_layout() -> rx.Component:
    """Layout principal de l'application."""
    return rx.box(
        # Notification
        ScrapiniumComponents.notification(
            message=ScrapiniumState.notification_message,
            type_=ScrapiniumState.notification_type,
            show=ScrapiniumState.show_notification,
            on_close=ScrapiniumState.hide_notification,
        ),
        # Barre de navigation
        navbar(),
        # Contenu principal
        rx.container(
            rx.vstack(
                # Statistiques
                stats_overview(),
                # Contenu principal en deux colonnes
                rx.hstack(
                    # Colonne gauche - Formulaire
                    rx.vstack(
                        scraper_form(),
                        spacing="24px",
                        flex="1",
                    ),
                    # Colonne droite - Tâches
                    rx.vstack(
                        recent_tasks(),
                        spacing="24px",
                        flex="1",
                    ),
                    spacing="24px",
                    align_items="start",
                    width="100%",
                ),
                spacing="32px",
                width="100%",
            ),
            max_width="1200px",
            padding="32px 24px",
        ),
        # Modal de résultats
        result_modal(),
        style=BaseStyles.container(),
        width="100%",
        min_height="100vh",
    )


def create_ui_app():
    """Crée l'application Reflex."""
    app = rx.App(
        style={
            "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
    )

    app.add_page(main_layout, route="/")

    return app


# Instance globale de l'app
app = create_ui_app()
