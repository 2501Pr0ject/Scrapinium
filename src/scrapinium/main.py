"""Point d'entrée principal de Scrapinium."""

from threading import Thread

import uvicorn

from scrapinium.api.app import create_app
from scrapinium.config.settings import settings
from scrapinium.ui.app import create_ui_app


def run_api():
    """Lance l'API FastAPI."""
    app = create_app()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info" if settings.debug else "warning",
    )


def run_ui():
    """Lance l'interface Reflex."""
    ui_app = create_ui_app()
    ui_app.run(
        host="0.0.0.0",
        port=3000,
        debug=settings.debug,
    )


def main():
    """Point d'entrée principal."""
    print(f"🚀 Démarrage de {settings.app_name} v{settings.app_version}")

    # Configuration du logging
    settings.setup_logging()

    # Démarrer l'API en arrière-plan
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()

    print(f"✅ API FastAPI démarrée sur http://localhost:{settings.port}")
    print("📖 Documentation API: http://localhost:8000/docs")
    print("🌐 Interface utilisateur sur http://localhost:3000")

    # Démarrer l'interface utilisateur
    run_ui()


if __name__ == "__main__":
    main()
