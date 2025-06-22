# Exemple Streamlit - Scrapinium

## 📋 Description

Interface web interactive utilisant Streamlit pour démontrer les capacités de Scrapinium avec une interface utilisateur intuitive.

## 🚀 Utilisation

### Démarrer l'application

```bash
# Depuis la racine du projet
cd examples/streamlit
streamlit run streamlit_app.py

# Ou directement
streamlit run examples/streamlit/streamlit_app.py
```

L'interface sera disponible sur `http://localhost:8501`

## ✨ Fonctionnalités

### Interface Utilisateur

- **Formulaire intuitif** pour configuration du scraping
- **Aperçu en temps réel** des résultats
- **Téléchargement multi-format** (Markdown, Text, JSON, HTML)
- **Dashboard de statistiques** avec graphiques interactifs
- **Historique des tâches** avec recherche et filtres

### ML Dashboard

- **Visualisation des analyses ML** en temps réel
- **Métriques de performance** du pipeline
- **Classification de contenu** avec confiance
- **Détection anti-bot** avec stratégies recommandées
- **Analyse sémantique** avec nuage de mots-clés

## 🎯 Fonctionnalités Principales

### Scraping Intelligent

- **Configuration visuelle** des paramètres de scraping
- **Prévisualisation instantanée** du contenu extrait
- **Support multi-format** d'export
- **Progress bar** en temps réel
- **Gestion d'erreurs** avec messages clairs

### Analyse ML Intégrée

- **Classification automatique** du type de contenu
- **Score de qualité** du contenu extrait
- **Détection des défis anti-bot** avec solutions
- **Métriques de lisibilité** et analyse structurelle
- **Extraction de mots-clés** et topics

### Monitoring & Stats

- **Dashboard système** avec métriques temps réel
- **Graphiques de performance** (cache, mémoire, pool)
- **Historique des analyses** avec tendances
- **Export des statistiques** en CSV/JSON

## 🎨 Interface

### Pages Principales

1. **🏠 Accueil** - Formulaire de scraping principal
2. **📊 Dashboard** - Statistiques et monitoring
3. **🧠 ML Insights** - Analyses et visualisations ML
4. **📈 Performance** - Métriques de performance
5. **📋 Historique** - Journal des tâches

### Composants Interactifs

- **Sélecteurs de format** (Markdown, JSON, HTML, Text)
- **Configuration LLM** avec instructions personnalisées
- **Filtres temps réel** pour l'historique
- **Graphiques interactifs** avec Plotly
- **Téléchargement direct** des résultats

## 🔧 Configuration

### Paramètres Disponibles

```python
# Configuration du scraping
url = st.text_input("URL à scraper")
output_format = st.selectbox("Format", ["markdown", "json", "html", "text"])
use_llm = st.checkbox("Utiliser LLM")
custom_instructions = st.text_area("Instructions personnalisées")

# Configuration ML
enable_ml = st.checkbox("Activer analyse ML")
show_confidence = st.checkbox("Afficher scores de confiance")
detailed_analysis = st.checkbox("Analyse détaillée")
```

### Variables d'Environnement

L'application utilise la même configuration que l'API FastAPI :

```bash
SCRAPINIUM_API_URL=http://localhost:8000
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

## 📊 Visualisations

### Graphiques Disponibles

- **Performance temps réel** : CPU, mémoire, cache
- **Statistiques ML** : Distribution des types de contenu
- **Tendances temporelles** : Évolution des performances
- **Heatmap qualité** : Qualité du contenu par domaine
- **Nuage de mots-clés** : Termes les plus fréquents

### Exports

- **Rapport PDF** des analyses ML
- **Export CSV** des statistiques
- **JSON complet** des métadonnées
- **Images** des graphiques

## 🎯 Cas d'Usage

### Démonstration

Parfait pour :
- **Démonstrations commerciales** de Scrapinium
- **Prototypage rapide** de workflows de scraping
- **Formation utilisateurs** sur les capacités ML
- **Tests interactifs** de nouvelles fonctionnalités

### Production Légère

Adapté pour :
- **Équipes non-techniques** nécessitant une interface simple
- **Scraping occasionnel** avec interface graphique
- **Monitoring visuel** des performances système
- **Validation manuelle** des résultats de scraping

## 🚀 Avantages

### Facilité d'Usage

- **Interface intuitive** sans code requis
- **Configuration visuelle** de tous les paramètres
- **Feedback immédiat** sur les résultats
- **Gestion d'erreurs** claire et compréhensible

### Visualisation

- **Aperçu temps réel** des données extraites
- **Graphiques interactifs** pour l'analyse
- **Export multi-format** en un clic
- **Dashboard complet** de monitoring

### Intégration

- **API Scrapinium** complètement intégrée
- **ML Pipeline** accessible visuellement
- **Compatibilité** avec tous les formats de sortie
- **Extensibilité** pour nouveaux composants

## 📚 Documentation

- [Guide Streamlit](https://docs.streamlit.io/)
- [API Scrapinium](../../docs/API.md)
- [Pipeline ML](../../docs/ML.md)
- [Configuration avancée](../../docs/CONFIGURATION.md)