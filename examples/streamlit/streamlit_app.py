"""Interface Streamlit moderne pour Scrapinium."""

import streamlit as st
import requests
import json
import time
import io
from datetime import datetime
from typing import Dict, Any
import asyncio
from src.scrapinium.ml import MLPipeline

# Configuration
API_BASE_URL = "http://localhost:8000"

# Initialiser le pipeline ML
@st.cache_resource
def get_ml_pipeline():
    """Initialise et cache le pipeline ML."""
    return MLPipeline()

# Configuration de la page
st.set_page_config(
    page_title="🕸️ Scrapinium",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le thème sombre
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #3b82f6;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #475569;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #10b981;
        font-weight: bold;
    }
    .error-message {
        color: #ef4444;
        font-weight: bold;
    }
    .info-message {
        color: #3b82f6;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def call_api(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Appelle l'API Scrapinium."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            return {"error": f"Méthode {method} non supportée"}
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Erreur {response.status_code}: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Erreur de connexion: {str(e)}"}


def analyze_content_with_ml(html_content: str, url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Analyse le contenu avec le pipeline ML."""
    try:
        ml_pipeline = get_ml_pipeline()
        
        # Créer un event loop si nécessaire
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Analyser le contenu
        result = loop.run_until_complete(
            ml_pipeline.analyze_page(
                html=html_content,
                url=url,
                headers=headers or {}
            )
        )
        
        return {
            'success': True,
            'analysis': {
                'page_type': result.classification.page_type.value,
                'confidence': result.classification.confidence,
                'quality': result.classification.quality.value,
                'language': result.classification.language,
                'word_count': result.content_features.word_count,
                'readability_score': result.content_features.readability_score,
                'completeness_score': result.content_features.completeness_score,
                'bot_challenges': [c.value for c in result.bot_detection.challenges],
                'recommendations': result.recommendations,
                'topics': result.content_features.topics,
                'top_keywords': result.content_features.keywords[:10],
                'processing_time': result.processing_time,
                'global_confidence': result.confidence_score
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_download_files(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée les fichiers de téléchargement dans différents formats."""
    content = data.get('content', '')
    url = data.get('url', 'unknown')
    metadata = data.get('metadata', {})
    
    # Nettoyer le nom de fichier
    filename_base = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('?', '_')[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    downloads = {}
    
    # 1. Fichier texte brut
    txt_content = f"""SCRAPINIUM - Résultat d'extraction
=====================================

URL: {url}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Format: {data.get('output_format', 'text')}
Mots: {metadata.get('word_count', 'N/A')}
Taille: {metadata.get('content_size', 'N/A')} bytes

CONTENU:
--------
{content}
"""
    downloads['txt'] = {
        'content': txt_content,
        'filename': f"scrapinium_{filename_base}_{timestamp}.txt",
        'mime': 'text/plain'
    }
    
    # 2. Fichier JSON structuré
    json_content = {
        "scrapinium_export": {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "format": data.get('output_format', 'text'),
            "metadata": metadata,
            "content": content
        }
    }
    downloads['json'] = {
        'content': json.dumps(json_content, indent=2, ensure_ascii=False),
        'filename': f"scrapinium_{filename_base}_{timestamp}.json",
        'mime': 'application/json'
    }
    
    # 3. Fichier Markdown
    md_content = f"""# Scrapinium - Extraction de {url}

**URL:** {url}  
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Format:** {data.get('output_format', 'text')}  
**Mots:** {metadata.get('word_count', 'N/A')}  
**Taille:** {metadata.get('content_size', 'N/A')} bytes  

---

## Contenu extrait

{content}

---

*Généré par Scrapinium - Web Scraping Intelligent*
"""
    downloads['md'] = {
        'content': md_content,
        'filename': f"scrapinium_{filename_base}_{timestamp}.md",
        'mime': 'text/markdown'
    }
    
    # 4. Fichier CSV (pour les données structurées)
    csv_content = f"""URL,Date,Format,Mots,Taille,Contenu
"{url}","{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}","{data.get('output_format', 'text')}","{metadata.get('word_count', 'N/A')}","{metadata.get('content_size', 'N/A')}","{content.replace('"', '""')}"
"""
    downloads['csv'] = {
        'content': csv_content,
        'filename': f"scrapinium_{filename_base}_{timestamp}.csv",
        'mime': 'text/csv'
    }
    
    return downloads

def main():
    """Interface principale."""
    
    # Header
    st.markdown('<h1 class="main-header">🕸️ Scrapinium</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748b; font-size: 1.2rem;">Web Scraping Intelligent avec IA</p>', unsafe_allow_html=True)
    
    # Sidebar pour les stats système
    with st.sidebar:
        st.header("📊 Statut Système")
        
        if st.button("🔄 Actualiser Stats", use_container_width=True):
            with st.spinner("Chargement..."):
                health_data = call_api("/health")
                st.session_state['health_data'] = health_data
        
        # Afficher les stats
        if 'health_data' in st.session_state:
            health = st.session_state['health_data']
            if 'error' not in health:
                st.metric("🔵 API", health.get('api', 'unknown'))
                st.metric("🔴 Ollama", health.get('ollama', 'unknown'))
                st.metric("🟢 Database", health.get('database', 'unknown'))
            else:
                st.error(health['error'])
        
        st.divider()
        
        # Stats générales
        st.header("📈 Statistiques")
        if st.button("📊 Charger Stats", use_container_width=True):
            with st.spinner("Chargement..."):
                stats_data = call_api("/stats")
                st.session_state['stats_data'] = stats_data
        
        if 'stats_data' in st.session_state:
            stats = st.session_state['stats_data']
            if 'error' not in stats:
                tasks = stats.get('tasks', {})
                browser_pool = stats.get('browser_pool', {})
                cache = stats.get('cache', {})
                
                st.metric("🎯 Tâches actives", tasks.get('active', 0))
                st.metric("🌐 Navigateurs", browser_pool.get('active_browsers', 0))
                st.metric("💾 Cache entries", cache.get('total_entries', 0))
            else:
                st.error(stats['error'])
    
    # Interface principale
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🚀 Nouveau Scraping")
        
        with st.form("scraping_form"):
            url = st.text_input(
                "🌐 URL à scraper",
                placeholder="https://example.com",
                help="Entrez l'URL complète du site à scraper"
            )
            
            task_type = st.selectbox(
                "📋 Type de tâche",
                ["content_extraction", "data_extraction", "full_page"],
                help="Choisissez le type d'extraction à effectuer"
            )
            
            priority = st.selectbox(
                "⚡ Priorité",
                ["normal", "high", "low"],
                help="Priorité de la tâche"
            )
            
            submit_button = st.form_submit_button("🚀 Lancer le Scraping", use_container_width=True)
            
            if submit_button:
                if not url:
                    st.error("❌ Veuillez entrer une URL valide")
                else:
                    with st.spinner("🔄 Scraping en cours..."):
                        result = call_api("/scrape", "POST", {
                            "url": url,
                            "task_type": task_type,
                            "priority": priority
                        })
                        
                        if 'error' not in result:
                            st.success("✅ Scraping lancé avec succès !")
                            
                            # Afficher la réponse initiale
                            st.json(result)
                            
                            # Récupérer l'ID de la tâche
                            task_id = result.get('data', {}).get('task_id')
                            
                            if task_id:
                                # Attendre et récupérer le résultat
                                with st.spinner("⏳ Récupération du résultat..."):
                                    # Attendre un peu que la tâche se termine
                                    time.sleep(3)
                                    
                                    # Récupérer le résultat complet
                                    result_data = call_api(f"/scrape/{task_id}/result")
                                    
                                    if 'error' not in result_data:
                                        st.success("📋 Résultat complet récupéré !")
                                        
                                        # Afficher le résultat dans un expander
                                        with st.expander("📄 Contenu extrait", expanded=True):
                                            data = result_data.get('data', {})
                                            
                                            col_a, col_b = st.columns(2)
                                            with col_a:
                                                st.write(f"**URL:** {data.get('url', 'N/A')}")
                                                st.write(f"**Format:** {data.get('output_format', 'N/A')}")
                                            with col_b:
                                                metadata = data.get('metadata', {})
                                                st.write(f"**Mots:** {metadata.get('word_count', 'N/A')}")
                                                st.write(f"**Taille:** {metadata.get('content_size', 'N/A')} bytes")
                                            
                                            # Contenu extrait
                                            content = data.get('content', '')
                                            if content:
                                                st.text_area(
                                                    "Contenu extrait:",
                                                    content[:2000] + "..." if len(content) > 2000 else content,
                                                    height=200
                                                )
                                                
                                                # Boutons de téléchargement
                                                st.subheader("💾 Télécharger les résultats")
                                                downloads = create_download_files(data)
                                                
                                                col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
                                                
                                                with col_dl1:
                                                    st.download_button(
                                                        "📄 TXT",
                                                        data=downloads['txt']['content'],
                                                        file_name=downloads['txt']['filename'],
                                                        mime=downloads['txt']['mime'],
                                                        use_container_width=True
                                                    )
                                                
                                                with col_dl2:
                                                    st.download_button(
                                                        "📊 JSON",
                                                        data=downloads['json']['content'],
                                                        file_name=downloads['json']['filename'],
                                                        mime=downloads['json']['mime'],
                                                        use_container_width=True
                                                    )
                                                
                                                with col_dl3:
                                                    st.download_button(
                                                        "📝 MD",
                                                        data=downloads['md']['content'],
                                                        file_name=downloads['md']['filename'],
                                                        mime=downloads['md']['mime'],
                                                        use_container_width=True
                                                    )
                                                
                                                with col_dl4:
                                                    st.download_button(
                                                        "📋 CSV",
                                                        data=downloads['csv']['content'],
                                                        file_name=downloads['csv']['filename'],
                                                        mime=downloads['csv']['mime'],
                                                        use_container_width=True
                                                    )
                                    else:
                                        st.warning(f"⏳ Tâche en cours... Réessayez dans quelques secondes")
                            
                            # Ajouter à l'historique
                            if 'scraping_history' not in st.session_state:
                                st.session_state['scraping_history'] = []
                            
                            st.session_state['scraping_history'].insert(0, {
                                "url": url,
                                "task_type": task_type,
                                "priority": priority,
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "result": result,
                                "task_id": task_id
                            })
                            
                            # Garder seulement les 10 dernières
                            st.session_state['scraping_history'] = st.session_state['scraping_history'][:10]
                            
                        else:
                            st.error(f"❌ {result['error']}")
    
    with col2:
        st.header("📋 Résultats & Historique")
        
        # Onglets pour les résultats
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📜 Historique", "🤖 Analyse ML"])
        
        with tab1:
            st.subheader("⚡ Métriques Live")
            
            if st.button("🔄 Actualiser Métriques", use_container_width=True):
                with st.spinner("Chargement des métriques..."):
                    metrics = call_api("/performance/metrics/live")
                    st.session_state['live_metrics'] = metrics
            
            if 'live_metrics' in st.session_state:
                metrics = st.session_state['live_metrics']
                if 'error' not in metrics:
                    if 'data' in metrics:
                        data = metrics['data']
                        current = data.get('current_metrics', {})
                        
                        # Métriques système
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("💾 Mémoire (MB)", f"{current.get('memory_usage_mb', 0):.1f}")
                        with col_b:
                            st.metric("🔄 Cache Hit Rate", f"{current.get('cache_hit_rate', 0):.1%}")
                        with col_c:
                            st.metric("⚡ Opérations", current.get('total_operations', 0))
                else:
                    st.error(metrics['error'])
        
        with tab2:
            st.subheader("📜 Historique des Tâches")
            
            if 'scraping_history' in st.session_state and st.session_state['scraping_history']:
                for i, task in enumerate(st.session_state['scraping_history']):
                    with st.expander(f"🌐 {task['url']} - {task['timestamp']}"):
                        col_x, col_y = st.columns(2)
                        with col_x:
                            st.write(f"**Type:** {task['task_type']}")
                            st.write(f"**Priorité:** {task['priority']}")
                        with col_y:
                            st.write(f"**Task ID:** {task.get('task_id', 'N/A')}")
                            st.write(f"**Message:** {task['result'].get('message', 'N/A')}")
                        
                        # Bouton pour récupérer le résultat
                        if task.get('task_id') and st.button(f"📄 Voir le résultat", key=f"result_{i}"):
                            with st.spinner("Récupération du résultat..."):
                                result_data = call_api(f"/scrape/{task['task_id']}/result")
                                
                                if 'error' not in result_data:
                                    data = result_data.get('data', {})
                                    
                                    st.success("✅ Résultat récupéré !")
                                    
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.write(f"**Format:** {data.get('output_format', 'N/A')}")
                                    with col_b:
                                        metadata = data.get('metadata', {})
                                        st.write(f"**Mots:** {metadata.get('word_count', 'N/A')}")
                                    
                                    content = data.get('content', '')
                                    if content:
                                        st.text_area(
                                            "Contenu:",
                                            content[:1000] + "..." if len(content) > 1000 else content,
                                            height=150,
                                            key=f"content_{i}"
                                        )
                                        
                                        # Boutons de téléchargement pour l'historique
                                        downloads = create_download_files(data)
                                        
                                        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
                                        
                                        with col_h1:
                                            st.download_button(
                                                "📄 TXT",
                                                data=downloads['txt']['content'],
                                                file_name=downloads['txt']['filename'],
                                                mime=downloads['txt']['mime'],
                                                key=f"txt_{i}",
                                                use_container_width=True
                                            )
                                        
                                        with col_h2:
                                            st.download_button(
                                                "📊 JSON",
                                                data=downloads['json']['content'],
                                                file_name=downloads['json']['filename'],
                                                mime=downloads['json']['mime'],
                                                key=f"json_{i}",
                                                use_container_width=True
                                            )
                                        
                                        with col_h3:
                                            st.download_button(
                                                "📝 MD",
                                                data=downloads['md']['content'],
                                                file_name=downloads['md']['filename'],
                                                mime=downloads['md']['mime'],
                                                key=f"md_{i}",
                                                use_container_width=True
                                            )
                                        
                                        with col_h4:
                                            st.download_button(
                                                "📋 CSV",
                                                data=downloads['csv']['content'],
                                                file_name=downloads['csv']['filename'],
                                                mime=downloads['csv']['mime'],
                                                key=f"csv_{i}",
                                                use_container_width=True
                                            )
                                else:
                                    st.error(f"❌ {result_data['error']}")
            else:
                st.info("📝 Aucune tâche dans l'historique")
        
        with tab3:
            st.subheader("🤖 Analyse ML de Contenu")
            
            # Section pour analyser une URL spécifique
            with st.form("ml_analysis_form"):
                analysis_url = st.text_input(
                    "🌐 URL à analyser avec ML",
                    placeholder="https://example.com/article",
                    help="Entrez l'URL pour une analyse ML complète"
                )
                
                advanced_options = st.expander("⚙️ Options avancées")
                with advanced_options:
                    enable_bot_detection = st.checkbox("🛡️ Détection anti-bot", value=True)
                    enable_content_analysis = st.checkbox("📊 Analyse de contenu", value=True)
                    enable_classification = st.checkbox("🏷️ Classification de page", value=True)
                
                analyze_button = st.form_submit_button("🔬 Analyser avec ML")
                
                if analyze_button and analysis_url:
                    with st.spinner("🤖 Analyse ML en cours..."):
                        # Récupérer le contenu de la page
                        scrape_result = call_api("/scrape", "POST", {
                            "url": analysis_url,
                            "task_type": "full_page",
                            "priority": "high"
                        })
                        
                        if 'error' not in scrape_result:
                            task_id = scrape_result.get('data', {}).get('task_id')
                            
                            if task_id:
                                # Attendre le résultat
                                time.sleep(3)
                                result_data = call_api(f"/scrape/{task_id}/result")
                                
                                if 'error' not in result_data:
                                    # Analyser avec ML
                                    page_data = result_data.get('data', {})
                                    html_content = page_data.get('html', '')
                                    
                                    if html_content:
                                        ml_analysis = analyze_content_with_ml(
                                            html_content=html_content,
                                            url=analysis_url
                                        )
                                        
                                        if ml_analysis['success']:
                                            analysis = ml_analysis['analysis']
                                            
                                            st.success("✅ Analyse ML terminée !")
                                            
                                            # Affichage des résultats
                                            col_ml1, col_ml2, col_ml3 = st.columns(3)
                                            
                                            with col_ml1:
                                                st.metric(
                                                    "🏷️ Type de page", 
                                                    analysis['page_type'].title(),
                                                    f"Confiance: {analysis['confidence']:.1%}"
                                                )
                                            
                                            with col_ml2:
                                                st.metric(
                                                    "⭐ Qualité",
                                                    analysis['quality'].title(),
                                                    f"Score: {analysis['readability_score']:.0f}/100"
                                                )
                                            
                                            with col_ml3:
                                                st.metric(
                                                    "🌍 Langue",
                                                    analysis['language'].upper(),
                                                    f"{analysis['word_count']} mots"
                                                )
                                            
                                            # Détails de l'analyse
                                            if enable_classification:
                                                with st.expander("🏷️ Classification détaillée", expanded=True):
                                                    col_c1, col_c2 = st.columns(2)
                                                    
                                                    with col_c1:
                                                        st.write(f"**Type détecté:** {analysis['page_type']}")
                                                        st.write(f"**Confiance:** {analysis['confidence']:.1%}")
                                                        st.write(f"**Qualité:** {analysis['quality']}")
                                                        st.write(f"**Langue:** {analysis['language']}")
                                                    
                                                    with col_c2:
                                                        st.write(f"**Lisibilité:** {analysis['readability_score']:.0f}/100")
                                                        st.write(f"**Complétude:** {analysis['completeness_score']:.0f}/100")
                                                        st.write(f"**Confiance globale:** {analysis['global_confidence']:.1%}")
                                                        st.write(f"**Temps d'analyse:** {analysis['processing_time']:.2f}s")
                                            
                                            if enable_bot_detection and analysis['bot_challenges']:
                                                with st.expander("🛡️ Détection anti-bot", expanded=True):
                                                    st.warning(f"⚠️ {len(analysis['bot_challenges'])} défi(s) anti-bot détecté(s)")
                                                    
                                                    for challenge in analysis['bot_challenges']:
                                                        st.write(f"• {challenge.replace('_', ' ').title()}")
                                            
                                            if enable_content_analysis:
                                                with st.expander("📊 Analyse de contenu", expanded=True):
                                                    
                                                    # Sujets détectés
                                                    if analysis['topics']:
                                                        st.write("**🎯 Sujets identifiés:**")
                                                        for topic in analysis['topics']:
                                                            st.write(f"• {topic.title()}")
                                                    
                                                    # Mots-clés principaux
                                                    if analysis['top_keywords']:
                                                        st.write("**🔑 Mots-clés principaux:**")
                                                        keywords_text = ", ".join([f"{kw[0]} ({kw[1]})" for kw in analysis['top_keywords']])
                                                        st.write(keywords_text)
                                            
                                            # Recommandations
                                            if analysis['recommendations']:
                                                with st.expander("💡 Recommandations", expanded=True):
                                                    for rec in analysis['recommendations']:
                                                        st.write(f"• {rec}")
                                        
                                        else:
                                            st.error(f"❌ Erreur ML: {ml_analysis['error']}")
                                    else:
                                        st.error("❌ Contenu HTML non disponible")
                                else:
                                    st.error(f"❌ {result_data['error']}")
                            else:
                                st.error("❌ Task ID non trouvé")
                        else:
                            st.error(f"❌ {scrape_result['error']}")
            
            st.divider()
            
            # Section des métriques ML
            st.subheader("📈 Métriques ML du Pipeline")
            
            if st.button("🔄 Actualiser Métriques ML"):
                with st.spinner("Chargement des métriques ML..."):
                    try:
                        ml_pipeline = get_ml_pipeline()
                        metrics = ml_pipeline.get_performance_metrics()
                        st.session_state['ml_metrics'] = metrics
                    except Exception as e:
                        st.error(f"Erreur lors du chargement des métriques: {str(e)}")
            
            if 'ml_metrics' in st.session_state:
                metrics = st.session_state['ml_metrics']
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("🔬 Analyses totales", metrics.get('total_analyses', 0))
                
                with col_m2:
                    st.metric("⏱️ Temps moyen", f"{metrics.get('avg_processing_time', 0):.2f}s")
                
                with col_m3:
                    st.metric("✅ Taux de succès", f"{metrics.get('success_rate', 0):.1%}")
                
                with col_m4:
                    st.metric("🎯 Confiance moyenne", f"{metrics.get('avg_confidence_score', 0):.1%}")
                
                # Distribution des types de pages
                if 'page_types_distribution' in metrics:
                    st.write("**📊 Distribution des types de pages:**")
                    page_dist = metrics['page_types_distribution']
                    if page_dist:
                        for page_type, count in page_dist.items():
                            st.write(f"• {page_type.title()}: {count}")
                    else:
                        st.info("Aucune donnée disponible")
    
    # Section de test rapide
    st.divider()
    st.header("🧪 Tests Rapides")
    
    col3, col4, col5, col6 = st.columns(4)
    
    with col3:
        if st.button("🏥 Test Health", use_container_width=True):
            with st.spinner("Test en cours..."):
                result = call_api("/health")
                if 'error' not in result:
                    st.success("✅ API accessible")
                else:
                    st.error(f"❌ {result['error']}")
    
    with col4:
        if st.button("📊 Test Stats", use_container_width=True):
            with st.spinner("Test en cours..."):
                result = call_api("/stats")
                if 'error' not in result:
                    st.success("✅ Stats disponibles")
                else:
                    st.error(f"❌ {result['error']}")
    
    with col5:
        if st.button("🌐 Test Scraping", use_container_width=True):
            with st.spinner("Test scraping httpbin.org..."):
                result = call_api("/scrape", "POST", {
                    "url": "https://httpbin.org/html",
                    "task_type": "content_extraction",
                    "priority": "normal"
                })
                if 'error' not in result:
                    st.success("✅ Scraping test réussi")
                    st.json(result)
                else:
                    st.error(f"❌ {result['error']}")
    
    with col6:
        if st.button("🤖 Test ML", use_container_width=True):
            with st.spinner("Test ML en cours..."):
                try:
                    ml_pipeline = get_ml_pipeline()
                    
                    # Test avec du contenu HTML simple
                    test_html = """
                    <html>
                    <head><title>Test Article</title></head>
                    <body>
                    <h1>Article de Test</h1>
                    <p>Ceci est un article de test pour vérifier le fonctionnement du pipeline ML.</p>
                    <p>Il contient plusieurs paragraphes avec du contenu de qualité.</p>
                    </body>
                    </html>
                    """
                    
                    # Créer un event loop si nécessaire
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(
                        ml_pipeline.analyze_page(
                            html=test_html,
                            url="https://test.example.com",
                            headers={}
                        )
                    )
                    
                    st.success("✅ Pipeline ML fonctionnel")
                    st.write(f"Type détecté: {result.classification.page_type.value}")
                    st.write(f"Confiance: {result.confidence_score:.1%}")
                    
                except Exception as e:
                    st.error(f"❌ Erreur ML: {str(e)}")

if __name__ == "__main__":
    main()