#!/usr/bin/env python3
"""Point d'entrée pour l'interface Reflex de Scrapinium."""

import sys
import os

# Ajouter le src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import reflex as rx
from scrapinium.ui.app import app

if __name__ == "__main__":
    # Nouvelle syntaxe Reflex 0.7+
    rx.run(app, host="0.0.0.0", port=3000)