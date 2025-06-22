# Exemple Reflex - Scrapinium (Legacy)

## 📋 Description

Interface web moderne utilisant Reflex (anciennement Pynecone) pour démontrer une approche Python-native du frontend. **Note : Cette implémentation est considérée comme legacy en faveur de l'interface HTML/JS moderne.**

## ⚠️ Statut : Legacy

Cette implémentation Reflex est maintenue pour compatibilité mais n'est plus activement développée. Nous recommandons d'utiliser :

- **Interface HTML/JS moderne** (intégrée dans l'API FastAPI)
- **Exemple Streamlit** pour prototypage rapide
- **API REST directe** pour intégrations

## 🚀 Utilisation

### Prérequis

```bash
# Installer Reflex (si pas déjà fait)
pip install reflex>=0.4.0

# Installer Node.js et npm (requis par Reflex)
# Voir: https://nodejs.org/
```

### Démarrer l'application

```bash
# Depuis la racine du projet
cd examples/reflex
reflex run

# Ou avec configuration spécifique
reflex run --env dev --port 3000
```

L'interface sera disponible sur `http://localhost:3000`

## ✨ Fonctionnalités (Legacy)

### Interface Moderne

- **Design responsive** avec thème sombre élégant
- **Composants réactifs** Python-native
- **États temps réel** avec WebSocket
- **Navigation fluide** entre les pages
- **Glassmorphism** et animations CSS

### Fonctionnalités Principales

- **Formulaire de scraping** avec validation en temps réel
- **Affichage des résultats** avec syntax highlighting
- **Dashboard de statistiques** avec graphiques
- **Gestion des tâches** avec états visuels
- **Configuration LLM** intégrée

## 🏗️ Architecture

### Structure Reflex

```
examples/reflex/
├── scrapinium_reflex.py    # Application principale
├── rxconfig.py            # Configuration Reflex
├── README.md              # Cette documentation
└── assets/                # Assets statiques (auto-généré)
```

### Composants Principaux

```python
# scrapinium_reflex.py

class ScrapiniumApp(rx.State):
    """État principal de l'application"""
    current_url: str = ""
    scraping_result: str = ""
    is_loading: bool = False
    task_status: str = "idle"
    
    def scrape_url(self):
        """Déclencher le scraping"""
        
    def update_status(self):
        """Mettre à jour le statut"""
```

### Pages Disponibles

1. **Index** (`/`) - Page principale de scraping
2. **Dashboard** (`/dashboard`) - Statistiques et monitoring  
3. **Settings** (`/settings`) - Configuration de l'application
4. **About** (`/about`) - Informations sur Scrapinium

## 🎨 Design System

### Thème Sombre Élégant

```python
# Configuration du thème
theme = {
    "primary_color": "#6366f1",      # Indigo moderne
    "secondary_color": "#8b5cf6",    # Violet
    "background": "#0f172a",         # Slate très sombre
    "surface": "#1e293b",            # Slate sombre
    "text_primary": "#f8fafc",       # Blanc cassé
    "text_secondary": "#cbd5e1",     # Gris clair
}
```

### Composants Personnalisés

- **Cards glassmorphism** avec blur et transparence
- **Buttons avec gradients** et hover effects
- **Progress bars animées** pour le scraping
- **Toasts notifications** pour les retours utilisateur
- **Modal dialogs** pour les détails

## ⚙️ Configuration

### rxconfig.py

```python
import reflex as rx

config = rx.Config(
    app_name="scrapinium_reflex",
    port=3000,
    env=rx.Env.DEV,
    api_url="http://localhost:8000",  # API Scrapinium
    frontend_packages=[
        "framer-motion",
        "lucide-react",
        "@heroicons/react",
    ],
    tailwind={
        "theme": {
            "extend": {
                "colors": {
                    "primary": "#6366f1",
                    "secondary": "#8b5cf6"
                }
            }
        }
    }
)
```

### Variables d'Environnement

```bash
# Reflex
REFLEX_ENV=development
REFLEX_PORT=3000
REFLEX_HOST=localhost

# Scrapinium API
SCRAPINIUM_API_URL=http://localhost:8000
SCRAPINIUM_WS_URL=ws://localhost:8000/ws
```

## 🔄 Migration Recommandée

### Vers Interface Moderne

L'interface HTML/JS moderne offre :

- **Performance supérieure** sans overhead Reflex
- **Bundle size réduit** avec assets optimisés
- **SEO amélioré** avec rendu côté serveur
- **Maintenance simplifiée** sans dépendances Node.js

### Code de Migration

```python
# Ancien (Reflex)
def scrape_button():
    return rx.button(
        "Scraper",
        on_click=ScrapiniumApp.scrape_url,
        bg="primary",
        color="white"
    )

# Nouveau (HTML/JS)
<button 
    onclick="startScraping()" 
    class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
    Scraper
</button>
```

## 🚀 Avantages Historiques

### Python-Native

- **Logique frontend en Python** sans JavaScript
- **Partage de code** entre frontend et backend
- **Type safety** complet avec Python
- **Écosystème Python** disponible côté frontend

### Reflex Features

- **State management** réactif intégré
- **Component system** modulaire
- **Real-time updates** via WebSocket
- **Styling** avec Tailwind CSS intégré

## 📉 Limitations (Pourquoi Legacy)

### Performance

- **Bundle size important** avec React + Python transpilation
- **Latence WebSocket** pour chaque interaction
- **Memory overhead** du transpiler Python→JS
- **Temps de build** élevé pour le développement

### Maintenance

- **Dépendances Node.js** requises côté développement
- **Debugging complexe** avec stack Python→JS
- **Écosystème immature** comparé à React/Vue natif
- **Documentation limitée** pour cas avancés

### Alternatives Modernes

- **Interface HTML/JS** : Plus rapide, plus simple
- **Streamlit** : Prototypage rapide, zéro config
- **API REST** : Intégration dans outils existants

## 📚 Ressources

### Documentation

- [Reflex Documentation](https://reflex.dev/docs/)
- [Migration vers HTML/JS](../../docs/MIGRATION.md)
- [Interface moderne](../../docs/UI.md)

### Support

Cette interface legacy est maintenue pour compatibilité uniquement. Pour le support :

1. **Problèmes Reflex** → [Reflex GitHub Issues](https://github.com/reflex-dev/reflex/issues)
2. **Migration aide** → [Scrapinium Discussions](https://github.com/your-username/scrapinium/discussions)
3. **Alternative moderne** → Utiliser l'interface HTML/JS intégrée

---

**Recommandation** : Migrer vers l'interface HTML/JS moderne pour de meilleures performances et une maintenance simplifiée.