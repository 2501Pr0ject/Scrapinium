"""Interface Streamlit moderne pour Scrapinium."""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

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
        tab1, tab2 = st.tabs(["📊 Dashboard", "📜 Historique"])
        
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
                                else:
                                    st.error(f"❌ {result_data['error']}")
            else:
                st.info("📝 Aucune tâche dans l'historique")
    
    # Section de test rapide
    st.divider()
    st.header("🧪 Tests Rapides")
    
    col3, col4, col5 = st.columns(3)
    
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

if __name__ == "__main__":
    main()