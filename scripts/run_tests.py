#!/usr/bin/env python3
"""Script de lancement des tests Scrapinium avec différents niveaux."""

import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(cmd, description=""):
    """Exécuter une commande et afficher le résultat."""
    print(f"\n{'='*60}")
    print(f"🔧 {description if description else cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    duration = time.time() - start_time
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print(f"\n⏱️  Durée: {duration:.2f}s")
    print(f"📊 Code de retour: {result.returncode}")
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Lanceur de tests Scrapinium")
    parser.add_argument("--level", choices=["unit", "integration", "all", "fast"], 
                       default="fast", help="Niveau de tests à exécuter")
    parser.add_argument("--coverage", action="store_true", 
                       help="Activer la couverture de code")
    parser.add_argument("--parallel", action="store_true", 
                       help="Exécuter les tests en parallèle")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Mode verbeux")
    parser.add_argument("--markers", "-m", type=str, 
                       help="Filtrer par markers pytest")
    
    args = parser.parse_args()
    
    # Configuration de base
    base_cmd = "python -m pytest"
    
    if args.verbose:
        base_cmd += " -v"
    else:
        base_cmd += " -q"
    
    # Configuration selon le niveau
    if args.level == "unit":
        base_cmd += " -m 'unit and not slow'"
        description = "Tests unitaires rapides"
    elif args.level == "integration":
        base_cmd += " -m 'integration'"
        description = "Tests d'intégration"
    elif args.level == "fast":
        base_cmd += " -m 'not slow'"
        description = "Tests rapides (unit + integration sans slow)"
    else:  # all
        description = "Tous les tests"
    
    # Markers personnalisés
    if args.markers:
        base_cmd += f" -m '{args.markers}'"
        description += f" (markers: {args.markers})"
    
    # Couverture de code
    if args.coverage:
        base_cmd += " --cov=src/scrapinium --cov-report=html --cov-report=term"
        description += " avec couverture"
    
    # Tests parallèles
    if args.parallel:
        base_cmd += " -n auto"
        description += " en parallèle"
    
    # Ajouter options communes
    base_cmd += " --tb=short --disable-warnings"
    
    # Répertoire de tests
    base_cmd += " tests/"
    
    print(f"🚀 Lancement: {description}")
    print(f"📂 Répertoire de travail: {Path.cwd()}")
    print(f"🔧 Commande: {base_cmd}")
    
    # Exécuter les tests
    success = run_command(base_cmd, description)
    
    if success:
        print(f"\n✅ Tests réussis!")
        
        # Afficher un résumé des markers disponibles
        if args.level == "all":
            print(f"\n📋 Markers disponibles:")
            markers_info = {
                "unit": "Tests unitaires rapides",
                "integration": "Tests d'intégration", 
                "performance": "Tests de performance",
                "slow": "Tests lents nécessitant des ressources",
                "api": "Tests de l'API REST",
                "scraping": "Tests de scraping web",
                "cache": "Tests du système de cache",
                "memory": "Tests de gestion mémoire",
                "security": "Tests de sécurité"
            }
            
            for marker, desc in markers_info.items():
                print(f"  • {marker:12} - {desc}")
        
        sys.exit(0)
    else:
        print(f"\n❌ Tests échoués!")
        sys.exit(1)


if __name__ == "__main__":
    main()