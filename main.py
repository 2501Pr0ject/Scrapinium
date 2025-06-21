#!/usr/bin/env python3
"""Point d'entrée principal pour Scrapinium."""

import uvicorn
from scrapinium.api.app import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )