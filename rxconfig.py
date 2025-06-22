"""Configuration pour Reflex."""

import reflex as rx

config = rx.Config(
    app_name="scrapinium",
    tailwind=None,  # Pas d'utilisation de Tailwind pour éviter les warnings
    backend_port=3000,
    frontend_port=3001,
    db_url="sqlite:///reflex.db"
)