"""Composants UI réutilisables pour Scrapinium."""

from typing import Any

import reflex as rx

from ..models.enums import OutputFormat
from .styles import Animations, BaseStyles, Colors, Layout


class ScrapiniumComponents:
    """Composants UI personnalisés pour Scrapinium."""

    @staticmethod
    def logo(size: str = "24px") -> rx.Component:
        """Logo Scrapinium."""
        return rx.hstack(
            rx.box(
                "🕸️",
                font_size=size,
            ),
            rx.text(
                "Scrapinium",
                font_size=size,
                font_weight="700",
                color=Colors.TEXT_PRIMARY,
                margin_left="8px",
            ),
            align_items="center",
        )

    @staticmethod
    def status_badge(status: str) -> rx.Component:
        """Badge de statut avec couleur."""
        return rx.badge(
            status.upper(),
            style=BaseStyles.status_badge(status),
        )

    @staticmethod
    def progress_bar(percentage: float, label: str = None) -> rx.Component:
        """Barre de progression élégante."""
        return rx.vstack(
            rx.cond(
                label,
                rx.hstack(
                    rx.text(label, **BaseStyles.text("small")),
                    rx.text(f"{percentage:.0f}%", **BaseStyles.text("small")),
                    justify="space-between",
                    width="100%",
                ),
            ),
            rx.box(
                rx.box(
                    style={
                        **BaseStyles.progress_fill(percentage),
                        "transition": "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
                    }
                ),
                style=BaseStyles.progress_bar(),
                width="100%",
            ),
            width="100%",
            spacing="4px",
        )

    @staticmethod
    def loading_spinner(size: str = "20px") -> rx.Component:
        """Spinner de chargement."""
        return rx.box(
            style={
                "width": size,
                "height": size,
                "border": f"2px solid {Colors.BG_TERTIARY}",
                "border_top": f"2px solid {Colors.PRIMARY}",
                "border_radius": "50%",
                "animation": "spin 1s linear infinite",
                "@keyframes spin": {
                    "0%": {"transform": "rotate(0deg)"},
                    "100%": {"transform": "rotate(360deg)"},
                },
            }
        )

    @staticmethod
    def primary_button(
        text: str,
        on_click=None,
        loading: bool = False,
        disabled: bool = False,
        icon: str = None,
    ) -> rx.Component:
        """Bouton principal avec état de chargement."""
        button_style = BaseStyles.button_primary()

        if disabled or loading:
            button_style.update(
                {
                    "opacity": "0.6",
                    "cursor": "not-allowed",
                    "_hover": {},
                }
            )

        content = []

        if loading:
            content.append(ScrapiniumComponents.loading_spinner("16px"))
        elif icon:
            content.append(rx.text(icon, font_size="16px"))

        content.append(
            rx.text(
                text,
                margin_left="8px" if (loading or icon) else "0",
            )
        )

        return rx.button(
            rx.hstack(*content, align_items="center"),
            on_click=on_click if not (disabled or loading) else None,
            style=button_style,
        )

    @staticmethod
    def secondary_button(text: str, on_click=None, icon: str = None) -> rx.Component:
        """Bouton secondaire."""
        content = []

        if icon:
            content.append(rx.text(icon, font_size="16px"))

        content.append(
            rx.text(
                text,
                margin_left="8px" if icon else "0",
            )
        )

        return rx.button(
            rx.hstack(*content, align_items="center"),
            on_click=on_click,
            style=BaseStyles.button_secondary(),
        )

    @staticmethod
    def card(
        children: list[rx.Component], title: str = None, elevated: bool = False, **props
    ) -> rx.Component:
        """Carte avec titre optionnel."""
        card_content = []

        if title:
            card_content.append(rx.heading(title, **BaseStyles.heading(3)))

        card_content.extend(children)

        return rx.box(
            rx.vstack(*card_content, spacing="16px", align_items="start"),
            style=BaseStyles.card(elevated),
            **props,
        )

    @staticmethod
    def input_field(
        placeholder: str,
        value: str = "",
        on_change=None,
        type_: str = "text",
        required: bool = False,
        disabled: bool = False,
    ) -> rx.Component:
        """Champ de saisie stylisé."""
        input_style = BaseStyles.input()

        if disabled:
            input_style.update(
                {
                    "opacity": "0.6",
                    "cursor": "not-allowed",
                }
            )

        return rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            type=type_,
            required=required,
            disabled=disabled,
            style=input_style,
        )

    @staticmethod
    def select_field(
        options: list[dict[str, str]],
        value: str = "",
        on_change=None,
        placeholder: str = "Sélectionnez...",
    ) -> rx.Component:
        """Champ de sélection."""
        return rx.select(
            options,
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            style=BaseStyles.select(),
        )

    @staticmethod
    def format_selector() -> rx.Component:
        """Sélecteur de format de sortie."""
        format_options = [
            {"label": "📝 Markdown", "value": OutputFormat.MARKDOWN.value},
            {"label": "📄 JSON", "value": OutputFormat.JSON.value},
            {"label": "🏷️ XML", "value": OutputFormat.XML.value},
            {"label": "📊 CSV", "value": OutputFormat.CSV.value},
            {"label": "📋 HTML", "value": OutputFormat.HTML.value},
            {"label": "📃 Texte", "value": OutputFormat.PLAIN_TEXT.value},
        ]

        return ScrapiniumComponents.select_field(
            options=format_options,
            placeholder="Format de sortie",
        )

    @staticmethod
    def task_card(task_data: dict[str, Any]) -> rx.Component:
        """Carte d'affichage d'une tâche de scraping."""
        status = task_data.get("status", "pending")
        url = task_data.get("url", "")
        created_at = task_data.get("created_at", "")
        progress = task_data.get("progress", 0)

        # Titre tronqué de l'URL
        display_url = url[:50] + "..." if len(url) > 50 else url

        return ScrapiniumComponents.card(
            [
                # En-tête avec URL et statut
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            display_url,
                            font_weight="600",
                            color=Colors.TEXT_PRIMARY,
                            font_size="14px",
                        ),
                        rx.text(
                            f"Créé le {created_at}",
                            **BaseStyles.text("small"),
                        ),
                        align_items="start",
                        spacing="4px",
                    ),
                    ScrapiniumComponents.status_badge(status),
                    justify="space-between",
                    align_items="start",
                    width="100%",
                ),
                # Barre de progression si en cours
                rx.cond(
                    status == "running",
                    ScrapiniumComponents.progress_bar(progress, "Progression"),
                ),
                # Boutons d'action
                rx.hstack(
                    ScrapiniumComponents.secondary_button(
                        "Voir détails",
                        icon="👁️",
                    ),
                    rx.cond(
                        status == "completed",
                        ScrapiniumComponents.secondary_button(
                            "Télécharger",
                            icon="💾",
                        ),
                    ),
                    spacing="8px",
                ),
            ],
            elevated=True,
        )

    @staticmethod
    def stats_card(
        title: str, value: str, icon: str, trend: str = None
    ) -> rx.Component:
        """Carte de statistique."""
        return ScrapiniumComponents.card(
            [
                rx.hstack(
                    rx.text(icon, font_size="24px"),
                    rx.vstack(
                        rx.text(title, **BaseStyles.text("small")),
                        rx.text(
                            value,
                            font_size="24px",
                            font_weight="700",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.cond(
                            trend,
                            rx.text(trend, **BaseStyles.text("small")),
                        ),
                        align_items="start",
                        spacing="4px",
                    ),
                    align_items="center",
                    spacing="12px",
                ),
            ],
        )

    @staticmethod
    def empty_state(
        icon: str,
        title: str,
        description: str,
        action_text: str = None,
        on_action=None,
    ) -> rx.Component:
        """État vide avec action."""
        content = [
            rx.text(icon, font_size="48px", opacity="0.5"),
            rx.text(
                title,
                font_size="20px",
                font_weight="600",
                color=Colors.TEXT_PRIMARY,
                text_align="center",
            ),
            rx.text(
                description,
                **BaseStyles.text("body"),
                text_align="center",
                max_width="400px",
            ),
        ]

        if action_text and on_action:
            content.append(
                ScrapiniumComponents.primary_button(
                    action_text,
                    on_click=on_action,
                )
            )

        return rx.vstack(
            *content,
            align_items="center",
            spacing="16px",
            padding="48px 24px",
            style={**Layout.flex_center(), "min_height": "300px"},
        )

    @staticmethod
    def notification(
        message: str,
        type_: str = "info",
        show: bool = True,
        on_close=None,
    ) -> rx.Component:
        """Notification toast."""
        if not show:
            return rx.fragment()

        type_colors = {
            "success": Colors.SUCCESS,
            "error": Colors.ERROR,
            "warning": Colors.WARNING,
            "info": Colors.INFO,
        }

        type_icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
        }

        color = type_colors.get(type_, Colors.INFO)
        icon = type_icons.get(type_, "ℹ️")

        return rx.box(
            rx.hstack(
                rx.text(icon, font_size="16px"),
                rx.text(
                    message,
                    font_size="14px",
                    color=Colors.TEXT_PRIMARY,
                    flex="1",
                ),
                rx.button(
                    "✕",
                    on_click=on_close,
                    style={
                        "background": "transparent",
                        "border": "none",
                        "color": Colors.TEXT_MUTED,
                        "cursor": "pointer",
                        "padding": "0",
                        "font_size": "16px",
                    },
                ),
                align_items="center",
                spacing="12px",
            ),
            style={
                "position": "fixed",
                "top": "24px",
                "right": "24px",
                "background": Colors.BG_CARD,
                "border": f"1px solid {color}",
                "border_left": f"4px solid {color}",
                "border_radius": "8px",
                "padding": "16px",
                "box_shadow": "0 10px 25px rgba(0, 0, 0, 0.3)",
                "z_index": "1000",
                "min_width": "300px",
                "max_width": "500px",
                **Animations.slide_up(),
            },
        )
