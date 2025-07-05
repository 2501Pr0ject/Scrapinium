/**
 * Dashboard Scrapinium v0.5.0 - Interface moderne avec métriques temps réel
 * Architecture: Vanilla JS + Chart.js pour les visualisations
 */

class ScrapiniumDashboard {
    constructor() {
        this.config = {
            refreshInterval: 30000, // 30 secondes
            maxDataPoints: 50,
            animationDuration: 300,
            websocketUrl: null,
            useWebSocket: true
        };
        
        this.state = {
            isLoading: false,
            lastUpdate: null,
            connectionStatus: 'disconnected',
            charts: {},
            websocket: null,
            reconnectAttempts: 0,
            maxReconnectAttempts: 5,
            metrics: {
                stats: {},
                browserStats: {},
                cacheStats: {},
                memoryStats: {}
            }
        };
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initialisation Dashboard Scrapinium v0.5.0');
        
        try {
            // Initialiser l'URL WebSocket
            this.initWebSocketUrl();
            
            // Chargement initial des données
            await this.loadAllMetrics();
            
            // Initialisation des graphiques
            await this.initCharts();
            
            // Démarrage WebSocket ou polling
            if (this.config.useWebSocket) {
                this.connectWebSocket();
            } else {
                this.startAutoRefresh();
            }
            
            // Event listeners
            this.setupEventListeners();
            
            console.log('✅ Dashboard initialisé avec succès');
            this.updateConnectionStatus('connected');
            
        } catch (error) {
            console.error('❌ Erreur initialisation dashboard:', error);
            this.showError('Erreur lors du chargement du dashboard', error.message);
        }
    }
    
    async loadAllMetrics() {
        this.state.isLoading = true;
        this.updateLoadingState(true);
        
        try {
            const [stats, browserStats, cacheStats, memoryStats] = await Promise.all([
                this.fetchStats(),
                this.fetchBrowserStats(),
                this.fetchCacheStats(),
                this.fetchMemoryStats()
            ]);
            
            this.state.metrics = { stats, browserStats, cacheStats, memoryStats };
            this.state.lastUpdate = new Date();
            
            this.updateUI();
            
        } catch (error) {
            console.error('Erreur chargement métriques:', error);
            this.updateConnectionStatus('error');
            throw error;
        } finally {
            this.state.isLoading = false;
            this.updateLoadingState(false);
        }
    }
    
    async fetchStats() {
        const response = await fetch('/stats');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        return result.data;
    }
    
    async fetchBrowserStats() {
        try {
            const response = await fetch('/stats/browser');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            return result.data;
        } catch (error) {
            console.warn('Stats navigateur non disponibles:', error);
            return {};
        }
    }
    
    async fetchCacheStats() {
        try {
            const response = await fetch('/stats/cache');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            return result.data;
        } catch (error) {
            console.warn('Stats cache non disponibles:', error);
            return {};
        }
    }
    
    async fetchMemoryStats() {
        try {
            const response = await fetch('/stats/memory');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            return result.data;
        } catch (error) {
            console.warn('Stats mémoire non disponibles:', error);
            return {};
        }
    }
    
    updateUI() {
        this.updatePrimaryStats();
        this.updateBrowserStats();
        this.updateCacheStats();
        this.updateMemoryStats();
        this.updateCharts();
        this.updateLastRefresh();
    }
    
    updatePrimaryStats() {
        const { stats } = this.state.metrics;
        
        this.updateElement('total-tasks', stats.total_tasks || 0);
        this.updateElement('active-tasks', stats.active_tasks || 0);
        this.updateElement('success-rate', `${stats.success_rate || 0}%`);
        this.updateElement('ollama-status', this.getOllamaStatusText(stats.ollama_status));
    }
    
    updateBrowserStats() {
        const { browserStats } = this.state.metrics;
        
        this.updateElement('active-browsers', browserStats.active_browsers || 0);
        this.updateElement('total-browsers', browserStats.total_browsers || 0);
        this.updateElement('avg-wait-time', `${browserStats.avg_wait_time_ms || 0}ms`);
        
        // Barre de progression navigateurs
        this.updateProgressBar('browser-progress', 
            browserStats.active_browsers || 0, 
            Math.max(browserStats.total_browsers || 1, 1)
        );
    }
    
    updateCacheStats() {
        const { cacheStats } = this.state.metrics;
        
        this.updateElement('cache-hit-rate', `${(cacheStats.hit_rate || 0).toFixed(1)}%`);
        this.updateElement('cache-total-requests', cacheStats.total_requests || 0);
        this.updateElement('cache-memory-entries', cacheStats.memory_cache?.entry_count || 0);
        
        // Barre de progression cache
        this.updateProgressBar('cache-progress', 
            Math.min(cacheStats.hit_rate || 0, 100), 
            100
        );
    }
    
    updateMemoryStats() {
        const { memoryStats } = this.state.metrics;
        
        const currentUsage = memoryStats.current_usage?.process_memory_mb || 0;
        const peakUsage = memoryStats.statistics?.peak_usage_mb || 0;
        const trend = memoryStats.statistics?.usage_trend || 'stable';
        
        this.updateElement('memory-current', `${currentUsage.toFixed(1)}MB`);
        this.updateElement('memory-peak', `${peakUsage.toFixed(1)}MB`);
        this.updateElement('memory-trend', trend);
        
        // Indicateur de statut mémoire
        this.updateMemoryStatus(memoryStats.thresholds);
    }
    
    updateMemoryStatus(thresholds) {
        const statusElement = document.querySelector('#memory-status');
        const statusTextElement = document.querySelector('#memory-status-text');
        
        if (!statusElement || !statusTextElement) return;
        
        // Reset classes
        statusElement.className = 'w-2 h-2 rounded-full';
        
        if (thresholds?.critical_reached) {
            statusElement.classList.add('bg-red-400', 'animate-pulse');
            statusTextElement.textContent = 'Critique';
            statusTextElement.className = 'text-xs text-red-400';
        } else if (thresholds?.warning_reached) {
            statusElement.classList.add('bg-yellow-400', 'animate-pulse');
            statusTextElement.textContent = 'Attention';
            statusTextElement.className = 'text-xs text-yellow-400';
        } else {
            statusElement.classList.add('bg-green-400');
            statusTextElement.textContent = 'Normal';
            statusTextElement.className = 'text-xs text-green-400';
        }
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateProgressBar(id, current, max) {
        const progressBar = document.getElementById(id);
        if (progressBar) {
            const percentage = Math.min((current / max) * 100, 100);
            progressBar.style.width = `${percentage}%`;
        }
    }
    
    getOllamaStatusText(status) {
        const statusMap = {
            'connected': '✅ Connecté',
            'disconnected': '❌ Déconnecté',
            'error': '⚠️ Erreur',
            'unknown': '❓ Inconnu'
        };
        return statusMap[status] || statusMap['unknown'];
    }
    
    async initCharts() {
        // Chart.js sera ajouté plus tard pour les graphiques avancés
        console.log('📊 Initialisation des graphiques (Chart.js requis)');
        
        // Pour l'instant, on utilise des indicateurs visuels simples
        this.initSimpleCharts();
    }
    
    initSimpleCharts() {
        // Graphique simple de performance avec CSS
        this.createPerformanceIndicators();
    }
    
    createPerformanceIndicators() {
        // Indicateurs de performance visuels sans Chart.js
        const performanceContainer = document.getElementById('performance-indicators');
        if (!performanceContainer) return;
        
        // Les données seront mises à jour via updateCharts()
    }
    
    updateCharts() {
        // Mise à jour des graphiques
        this.updatePerformanceIndicators();
    }
    
    updatePerformanceIndicators() {
        const { stats, cacheStats, memoryStats } = this.state.metrics;
        
        // Calcul de scores de performance
        const performanceScore = this.calculatePerformanceScore();
        
        // Mise à jour des indicateurs visuels
        this.updatePerformanceScore(performanceScore);
    }
    
    calculatePerformanceScore() {
        const { stats, cacheStats, memoryStats } = this.state.metrics;
        
        let score = 100;
        
        // Facteurs de performance
        const successRate = stats.success_rate || 0;
        const hitRate = cacheStats.hit_rate || 0;
        const memoryUsage = memoryStats.current_usage?.process_memory_mb || 0;
        
        // Calcul du score (simplifié)
        score = (successRate * 0.4) + (hitRate * 0.3) + (Math.max(100 - memoryUsage/10, 0) * 0.3);
        
        return Math.min(Math.max(score, 0), 100);
    }
    
    updatePerformanceScore(score) {
        const scoreElement = document.getElementById('performance-score');
        const scoreBarElement = document.getElementById('performance-score-bar');
        
        if (scoreElement) {
            scoreElement.textContent = `${score.toFixed(1)}%`;
        }
        
        if (scoreBarElement) {
            scoreBarElement.style.width = `${score}%`;
            
            // Couleur basée sur le score
            scoreBarElement.className = 'h-2 rounded-full transition-all duration-300 ';
            if (score >= 80) {
                scoreBarElement.classList.add('bg-gradient-to-r', 'from-green-500', 'to-emerald-400');
            } else if (score >= 60) {
                scoreBarElement.classList.add('bg-gradient-to-r', 'from-yellow-500', 'to-orange-400');
            } else {
                scoreBarElement.classList.add('bg-gradient-to-r', 'from-red-500', 'to-pink-400');
            }
        }
    }
    
    initWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        this.config.websocketUrl = `${protocol}//${host}/stats/live`;
        console.log('WebSocket URL:', this.config.websocketUrl);
    }
    
    connectWebSocket() {
        if (this.state.websocket) {
            this.state.websocket.close();
        }
        
        try {
            console.log('🔗 Connexion WebSocket...');
            this.state.websocket = new WebSocket(this.config.websocketUrl);
            
            this.state.websocket.onopen = () => {
                console.log('✅ WebSocket connecté');
                this.state.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
            };
            
            this.state.websocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    if (message.type === 'stats_update') {
                        this.handleWebSocketUpdate(message.data);
                    }
                } catch (error) {
                    console.error('Erreur parsing message WebSocket:', error);
                }
            };
            
            this.state.websocket.onclose = () => {
                console.log('🔌 WebSocket fermé');
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            };
            
            this.state.websocket.onerror = (error) => {
                console.error('❌ Erreur WebSocket:', error);
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('Erreur création WebSocket:', error);
            this.fallbackToPolling();
        }
    }
    
    handleWebSocketUpdate(data) {
        if (data && Object.keys(data).length > 0) {
            this.state.metrics = data;
            this.state.lastUpdate = new Date();
            this.updateUI();
        }
    }
    
    attemptReconnect() {
        if (this.state.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, this.state.reconnectAttempts), 10000);
            this.state.reconnectAttempts++;
            
            console.log(`🔄 Tentative reconnexion ${this.state.reconnectAttempts}/${this.maxReconnectAttempts} dans ${delay}ms`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            console.log('🚫 Max tentatives de reconnexion atteint, basculement en polling');
            this.fallbackToPolling();
        }
    }
    
    fallbackToPolling() {
        this.config.useWebSocket = false;
        this.startAutoRefresh();
    }
    
    startAutoRefresh() {
        setInterval(async () => {
            if (!this.state.isLoading && !this.config.useWebSocket) {
                try {
                    await this.loadAllMetrics();
                    this.updateConnectionStatus('connected');
                } catch (error) {
                    console.error('Erreur rafraîchissement automatique:', error);
                    this.updateConnectionStatus('error');
                }
            }
        }, this.config.refreshInterval);
        
        console.log(`🔄 Rafraîchissement automatique démarré (${this.config.refreshInterval/1000}s)`);
    }
    
    setupEventListeners() {
        // Bouton de rafraîchissement manuel
        const refreshButton = document.getElementById('refresh-button');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.manualRefresh());
        }
        
        // Boutons de contrôle
        this.setupControlButtons();
    }
    
    setupControlButtons() {
        // Force refresh
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                e.preventDefault();
                this.manualRefresh();
            }
        });
    }
    
    async manualRefresh() {
        console.log('🔄 Rafraîchissement manuel');
        try {
            await this.loadAllMetrics();
            this.showSuccess('Données mises à jour');
        } catch (error) {
            this.showError('Erreur lors du rafraîchissement', error.message);
        }
    }
    
    updateConnectionStatus(status) {
        this.state.connectionStatus = status;
        
        const statusElement = document.getElementById('connection-status');
        const statusTextElement = document.getElementById('connection-status-text');
        
        if (!statusElement || !statusTextElement) return;
        
        // Reset classes
        statusElement.className = 'w-2 h-2 rounded-full';
        
        switch (status) {
            case 'connected':
                statusElement.classList.add('bg-green-400', 'animate-pulse');
                statusTextElement.textContent = 'API Online';
                statusTextElement.className = 'text-sm text-slate-300';
                break;
            case 'error':
                statusElement.classList.add('bg-red-400', 'animate-pulse');
                statusTextElement.textContent = 'API Erreur';
                statusTextElement.className = 'text-sm text-red-400';
                break;
            default:
                statusElement.classList.add('bg-yellow-400', 'animate-pulse');
                statusTextElement.textContent = 'API Connexion';
                statusTextElement.className = 'text-sm text-yellow-400';
        }
    }
    
    updateLoadingState(isLoading) {
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'block' : 'none';
        });
    }
    
    updateLastRefresh() {
        const lastRefreshElement = document.getElementById('last-refresh');
        if (lastRefreshElement && this.state.lastUpdate) {
            const timeString = this.state.lastUpdate.toLocaleTimeString();
            lastRefreshElement.textContent = `Dernière mise à jour: ${timeString}`;
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message, details = '') {
        this.showNotification(message, 'error', details);
        console.error('Dashboard Error:', message, details);
    }
    
    showNotification(message, type = 'info', details = '') {
        // Utilise le système de notification existant d'Alpine.js si disponible
        if (window.Alpine && window.scrapiniumApp) {
            const app = window.scrapiniumApp();
            app.showNotification(message, type, details);
        } else {
            // Fallback: notification console
            console.log(`${type.toUpperCase()}: ${message}`, details);
        }
    }
}

// Initialisation globale
let dashboard;

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new ScrapiniumDashboard();
});

// Export pour utilisation externe
window.ScrapiniumDashboard = ScrapiniumDashboard;

// Utilitaires globaux
window.dashboardUtils = {
    formatBytes: (bytes) => {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(1)}${sizes[i]}`;
    },
    
    formatDuration: (milliseconds) => {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    },
    
    getStatusColor: (status) => {
        const colors = {
            'completed': 'text-green-400',
            'running': 'text-yellow-400',
            'failed': 'text-red-400',
            'pending': 'text-blue-400'
        };
        return colors[status] || 'text-slate-400';
    }
};

console.log('📊 Dashboard Scrapinium v0.5.0 - Module chargé');