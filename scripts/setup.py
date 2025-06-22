#!/usr/bin/env python3
"""
Script de setup pour Scrapinium.
Configure l'environnement de développement complet.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> bool:
    """Exécute une commande shell."""
    print(f"🔧 {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur: {e}")
        return False


def setup_python_environment():
    """Configure l'environnement Python."""
    print("🐍 Configuration de l'environnement Python...")
    
    # Vérifier Python
    if not run_command("python --version"):
        print("❌ Python n'est pas installé")
        return False
    
    # Installer les dépendances
    run_command("pip install --upgrade pip")
    run_command("pip install -r requirements.txt")
    run_command("pip install -r requirements-dev.txt")
    
    return True


def setup_playwright():
    """Configure Playwright."""
    print("🎭 Configuration de Playwright...")
    
    run_command("playwright install")
    run_command("playwright install-deps")
    
    return True


def setup_pre_commit():
    """Configure les hooks pre-commit."""
    print("🔍 Configuration des hooks pre-commit...")
    
    run_command("pre-commit install")
    run_command("pre-commit install --hook-type commit-msg")
    
    return True


def setup_environment_file():
    """Configure le fichier .env."""
    print("⚙️ Configuration du fichier .env...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists() and not env_file.exists():
        run_command("cp .env.example .env")
        print("✅ Fichier .env créé depuis .env.example")
        print("⚠️ N'oubliez pas de configurer vos variables d'environnement !")
    
    return True


def setup_database():
    """Configure la base de données."""
    print("🗄️ Configuration de la base de données...")
    
    # TODO: Ajouter la configuration de la base de données
    print("ℹ️ Configuration de la base de données à faire manuellement")
    
    return True


def verify_setup():
    """Vérifie que le setup est correct."""
    print("✅ Vérification du setup...")
    
    checks = [
        ("Python", "python --version"),
        ("Pip", "pip --version"),
        ("Playwright", "playwright --version"),
        ("Pre-commit", "pre-commit --version"),
    ]
    
    all_good = True
    for name, cmd in checks:
        if run_command(cmd, check=False):
            print(f"✅ {name} : OK")
        else:
            print(f"❌ {name} : ÉCHEC")
            all_good = False
    
    return all_good


def main():
    """Point d'entrée principal."""
    print("🚀 Setup de Scrapinium")
    print("=" * 50)
    
    # Vérifier qu'on est dans le bon dossier
    if not Path("pyproject.toml").exists():
        print("❌ Ce script doit être exécuté depuis la racine du projet")
        sys.exit(1)
    
    steps = [
        ("Configuration Python", setup_python_environment),
        ("Configuration Playwright", setup_playwright),
        ("Configuration Pre-commit", setup_pre_commit),
        ("Configuration .env", setup_environment_file),
        ("Configuration Base de données", setup_database),
        ("Vérification", verify_setup),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"❌ Échec de l'étape : {step_name}")
            sys.exit(1)
    
    print("\n🎉 Setup terminé avec succès !")
    print("\n📝 Prochaines étapes :")
    print("1. Configurer le fichier .env avec vos paramètres")
    print("2. Démarrer les services (Redis, PostgreSQL si nécessaire)")
    print("3. Lancer l'application : uvicorn src.scrapinium.api.app:app --reload")
    print("4. Visiter http://localhost:8000")


if __name__ == "__main__":
    main()