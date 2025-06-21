"""Styles pour l'interface Scrapinium - Thème sombre élégant."""



# Palette de couleurs du thème sombre
class Colors:
    # Couleurs principales
    PRIMARY = "#6366f1"  # Indigo moderne
    PRIMARY_DARK = "#4f46e5"
    PRIMARY_LIGHT = "#818cf8"

    # Couleurs de fond
    BG_PRIMARY = "#0f0f23"  # Bleu très sombre
    BG_SECONDARY = "#1a1a2e"  # Bleu sombre
    BG_TERTIARY = "#16213e"  # Bleu-gris
    BG_CARD = "#1e2139"  # Cartes
    BG_INPUT = "#242846"  # Champs de saisie

    # Couleurs de texte
    TEXT_PRIMARY = "#f1f5f9"  # Blanc cassé
    TEXT_SECONDARY = "#cbd5e1"  # Gris clair
    TEXT_MUTED = "#94a3b8"  # Gris moyen
    TEXT_DISABLED = "#64748b"  # Gris foncé

    # Couleurs d'état
    SUCCESS = "#10b981"
    ERROR = "#ef4444"
    WARNING = "#f59e0b"
    INFO = "#3b82f6"

    # Couleurs d'accentuation
    ACCENT = "#e879f9"  # Magenta
    ACCENT_SECONDARY = "#06b6d4"  # Cyan

    # Bordures
    BORDER = "#334155"
    BORDER_LIGHT = "#475569"
    BORDER_FOCUS = PRIMARY


# Styles de base pour les composants
class BaseStyles:
    @staticmethod
    def container() -> dict:
        """Style conteneur principal."""
        return {
            "background": Colors.BG_PRIMARY,
            "min_height": "100vh",
            "color": Colors.TEXT_PRIMARY,
            "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        }

    @staticmethod
    def card(elevated: bool = False) -> dict:
        """Style carte."""
        return {
            "background": Colors.BG_CARD,
            "border_radius": "12px",
            "border": f"1px solid {Colors.BORDER}",
            "box_shadow": "0 10px 15px -3px rgba(0, 0, 0, 0.3)"
            if elevated
            else "0 4px 6px -1px rgba(0, 0, 0, 0.2)",
            "padding": "24px",
        }

    @staticmethod
    def button_primary() -> dict:
        """Style bouton principal."""
        return {
            "background": f"linear-gradient(135deg, {Colors.PRIMARY} 0%, {Colors.PRIMARY_DARK} 100%)",
            "color": "white",
            "border": "none",
            "border_radius": "8px",
            "padding": "12px 24px",
            "font_weight": "600",
            "font_size": "14px",
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "_hover": {
                "background": f"linear-gradient(135deg, {Colors.PRIMARY_DARK} 0%, {Colors.PRIMARY} 100%)",
                "transform": "translateY(-1px)",
                "box_shadow": f"0 8px 25px -8px {Colors.PRIMARY}",
            },
            "_active": {
                "transform": "translateY(0)",
            },
        }

    @staticmethod
    def button_secondary() -> dict:
        """Style bouton secondaire."""
        return {
            "background": "transparent",
            "color": Colors.TEXT_SECONDARY,
            "border": f"1px solid {Colors.BORDER}",
            "border_radius": "8px",
            "padding": "12px 24px",
            "font_weight": "500",
            "font_size": "14px",
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "_hover": {
                "background": Colors.BG_TERTIARY,
                "border_color": Colors.BORDER_LIGHT,
                "color": Colors.TEXT_PRIMARY,
            },
        }

    @staticmethod
    def input() -> dict:
        """Style champ de saisie."""
        return {
            "background": Colors.BG_INPUT,
            "border": f"1px solid {Colors.BORDER}",
            "border_radius": "8px",
            "padding": "12px 16px",
            "font_size": "14px",
            "color": Colors.TEXT_PRIMARY,
            "width": "100%",
            "transition": "all 0.2s ease",
            "_placeholder": {
                "color": Colors.TEXT_DISABLED,
            },
            "_focus": {
                "outline": "none",
                "border_color": Colors.BORDER_FOCUS,
                "box_shadow": f"0 0 0 3px {Colors.PRIMARY}20",
            },
        }

    @staticmethod
    def select() -> dict:
        """Style sélecteur."""
        return {
            **BaseStyles.input(),
            "cursor": "pointer",
        }

    @staticmethod
    def heading(level: int = 1) -> dict:
        """Style titre."""
        sizes = {
            1: "32px",
            2: "24px",
            3: "20px",
            4: "18px",
        }

        return {
            "font_size": sizes.get(level, "16px"),
            "font_weight": "700",
            "color": Colors.TEXT_PRIMARY,
            "line_height": "1.2",
            "margin": "0 0 16px 0",
        }

    @staticmethod
    def text(variant: str = "body") -> dict:
        """Style texte."""
        variants = {
            "body": {
                "font_size": "14px",
                "color": Colors.TEXT_SECONDARY,
                "line_height": "1.5",
            },
            "small": {
                "font_size": "12px",
                "color": Colors.TEXT_MUTED,
                "line_height": "1.4",
            },
            "caption": {
                "font_size": "11px",
                "color": Colors.TEXT_DISABLED,
                "line_height": "1.3",
                "text_transform": "uppercase",
                "letter_spacing": "0.5px",
            },
        }

        return variants.get(variant, variants["body"])

    @staticmethod
    def status_badge(status: str) -> dict:
        """Style badge de statut."""
        status_colors = {
            "completed": Colors.SUCCESS,
            "running": Colors.INFO,
            "pending": Colors.WARNING,
            "failed": Colors.ERROR,
        }

        color = status_colors.get(status, Colors.TEXT_MUTED)

        return {
            "background": f"{color}20",
            "color": color,
            "border": f"1px solid {color}40",
            "border_radius": "16px",
            "padding": "4px 12px",
            "font_size": "12px",
            "font_weight": "600",
            "text_transform": "uppercase",
            "letter_spacing": "0.5px",
        }

    @staticmethod
    def progress_bar() -> dict:
        """Style barre de progression."""
        return {
            "background": Colors.BG_TERTIARY,
            "border_radius": "8px",
            "height": "8px",
            "overflow": "hidden",
        }

    @staticmethod
    def progress_fill(percentage: float) -> dict:
        """Style remplissage barre de progression."""
        return {
            "background": f"linear-gradient(90deg, {Colors.PRIMARY} 0%, {Colors.ACCENT} 100%)",
            "height": "100%",
            "width": f"{percentage}%",
            "transition": "width 0.3s ease",
            "border_radius": "8px",
        }

    @staticmethod
    def sidebar() -> dict:
        """Style sidebar."""
        return {
            "background": Colors.BG_SECONDARY,
            "border_right": f"1px solid {Colors.BORDER}",
            "width": "280px",
            "height": "100vh",
            "padding": "24px",
            "position": "fixed",
            "left": "0",
            "top": "0",
        }

    @staticmethod
    def main_content() -> dict:
        """Style contenu principal."""
        return {
            "margin_left": "280px",
            "padding": "24px",
            "min_height": "100vh",
        }

    @staticmethod
    def code_block() -> dict:
        """Style bloc de code."""
        return {
            "background": Colors.BG_PRIMARY,
            "border": f"1px solid {Colors.BORDER}",
            "border_radius": "8px",
            "padding": "16px",
            "font_family": "'Fira Code', 'JetBrains Mono', 'Monaco', monospace",
            "font_size": "13px",
            "color": Colors.TEXT_PRIMARY,
            "overflow_x": "auto",
            "white_space": "pre",
        }

    @staticmethod
    def floating_action() -> dict:
        """Style bouton d'action flottant."""
        return {
            "position": "fixed",
            "bottom": "24px",
            "right": "24px",
            "background": f"linear-gradient(135deg, {Colors.ACCENT} 0%, {Colors.PRIMARY} 100%)",
            "color": "white",
            "border": "none",
            "border_radius": "50%",
            "width": "56px",
            "height": "56px",
            "box_shadow": "0 8px 32px rgba(0, 0, 0, 0.3)",
            "cursor": "pointer",
            "transition": "all 0.3s ease",
            "_hover": {
                "transform": "scale(1.1)",
                "box_shadow": f"0 12px 40px {Colors.ACCENT}40",
            },
        }


# Animations CSS personnalisées
class Animations:
    @staticmethod
    def fade_in(duration: str = "0.3s") -> dict:
        """Animation fade in."""
        return {
            "animation": f"fadeIn {duration} ease-in-out",
            "@keyframes fadeIn": {
                "from": {"opacity": "0", "transform": "translateY(10px)"},
                "to": {"opacity": "1", "transform": "translateY(0)"},
            },
        }

    @staticmethod
    def slide_up(duration: str = "0.4s") -> dict:
        """Animation slide up."""
        return {
            "animation": f"slideUp {duration} ease-out",
            "@keyframes slideUp": {
                "from": {"opacity": "0", "transform": "translateY(20px)"},
                "to": {"opacity": "1", "transform": "translateY(0)"},
            },
        }

    @staticmethod
    def pulse() -> dict:
        """Animation pulse pour loading."""
        return {
            "animation": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
            "@keyframes pulse": {
                "0%, 100%": {"opacity": "1"},
                "50%": {"opacity": "0.5"},
            },
        }


# Utilitaires de layout
class Layout:
    @staticmethod
    def flex_center() -> dict:
        """Flex centré."""
        return {
            "display": "flex",
            "align_items": "center",
            "justify_content": "center",
        }

    @staticmethod
    def flex_between() -> dict:
        """Flex space-between."""
        return {
            "display": "flex",
            "align_items": "center",
            "justify_content": "space-between",
        }

    @staticmethod
    def flex_column() -> dict:
        """Flex colonne."""
        return {
            "display": "flex",
            "flex_direction": "column",
        }

    @staticmethod
    def grid_responsive() -> dict:
        """Grid responsive."""
        return {
            "display": "grid",
            "grid_template_columns": "repeat(auto-fit, minmax(300px, 1fr))",
            "gap": "24px",
        }
