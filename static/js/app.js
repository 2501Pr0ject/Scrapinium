/**
 * Scrapinium Alpine.js App - v0.6.0
 * Gestion de l'application principale avec intégration API
 */

function scrapiniumApp() {
    return {
        // État du formulaire
        form: {
            url: '',
            output_format: 'markdown',
            use_llm: true,
            use_cache: true,
            custom_instructions: ''
        },
        
        // État de validation URL
        urlValidation: {
            isValid: false,
            error: null
        },
        
        // État de chargement
        isLoading: false,
        progress: 0,
        progressMessage: 'Initializing...',
        
        // État des tâches
        tasks: [],
        currentTask: null,
        
        // État des notifications
        notification: {
            show: false,
            type: 'info', // 'success', 'error', 'info'
            message: '',
            details: ''
        },
        
        // WebSocket
        websocket: null,
        wsConnected: false,
        wsReconnectAttempts: 0,
        wsMaxReconnectAttempts: 5,
        
        // État du modal
        modal: {
            show: false,
            title: '',
            content: '',
            taskId: null
        },
        
        // Initialisation
        init() {
            console.log('🚀 Scrapinium App initialisée');
            this.loadTasks();
            this.setupEventListeners();
            this.initWebSocket();
        },
        
        // Validation d'URL
        validateUrl() {
            const url = this.form.url.trim();
            
            if (!url) {
                this.urlValidation.isValid = false;
                this.urlValidation.error = null;
                return;
            }
            
            try {
                const urlObj = new URL(url);
                if (!['http:', 'https:'].includes(urlObj.protocol)) {
                    throw new Error('Only HTTP and HTTPS URLs are allowed');
                }
                
                this.urlValidation.isValid = true;
                this.urlValidation.error = null;
            } catch (error) {
                this.urlValidation.isValid = false;
                this.urlValidation.error = 'Please enter a valid URL (http:// or https://)';
            }
        },
        
        // Soumission du scraping
        async submitScraping() {
            if (!this.urlValidation.isValid || this.isLoading) {
                return;
            }
            
            console.log('📝 Soumission scraping pour:', this.form.url);
            
            this.isLoading = true;
            this.progress = 0;
            this.progressMessage = 'Initializing scraping task...';
            
            try {
                // Préparer les données pour l'API
                const scrapingData = {
                    url: this.form.url,
                    output_format: this.form.output_format,
                    llm_provider: 'ollama',
                    llm_model: this.form.use_llm ? 'llama2' : null
                };
                
                console.log('📤 Envoi des données:', scrapingData);
                
                // Simulation de progression
                this.updateProgress(10, 'Validating URL...');
                
                // Appel API
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(scrapingData)
                });
                
                this.updateProgress(30, 'Processing request...');
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `HTTP ${response.status}`);
                }
                
                const result = await response.json();
                console.log('📥 Réponse API:', result);
                
                if (result.success) {
                    const taskId = result.data.task_id;
                    this.currentTask = { id: taskId, status: 'pending' };
                    
                    this.updateProgress(30, 'Task created successfully...');
                    
                    // S'abonner aux mises à jour WebSocket pour cette tâche
                    this.subscribeToTask(taskId);
                    
                    this.showNotification(
                        'Scraping task started!',
                        'info',
                        `Task ID: ${taskId}`
                    );
                    
                    // Recharger la liste des tâches
                    await this.loadTasks();
                    
                } else {
                    throw new Error(result.message || 'Unknown error occurred');
                }
                
            } catch (error) {
                console.error('❌ Erreur scraping:', error);
                this.showNotification(
                    'Scraping failed',
                    'error',
                    error.message
                );
            } finally {
                this.isLoading = false;
                this.progress = 0;
                this.progressMessage = 'Initializing...';
            }
        },
        
        // Simulation de progression (sera remplacé par WebSocket)
        async simulateProgress() {
            const steps = [
                { progress: 60, message: 'Loading webpage...' },
                { progress: 70, message: 'Extracting content...' },
                { progress: 85, message: 'Processing with AI...' },
                { progress: 95, message: 'Finalizing results...' },
                { progress: 100, message: 'Completed!' }
            ];
            
            for (const step of steps) {
                this.updateProgress(step.progress, step.message);
                await new Promise(resolve => setTimeout(resolve, 800));
            }
        },
        
        // Mise à jour de la progression
        updateProgress(progress, message) {
            this.progress = progress;
            this.progressMessage = message;
        },
        
        // Chargement des tâches
        async loadTasks() {
            try {
                console.log('📋 Chargement des tâches...');
                
                const response = await fetch('/scrape?limit=10');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const result = await response.json();
                if (result.success && result.data) {
                    this.tasks = result.data.tasks || [];
                    console.log(`✅ ${this.tasks.length} tâches chargées`);
                } else {
                    this.tasks = [];
                }
                
            } catch (error) {
                console.error('❌ Erreur chargement tâches:', error);
                this.tasks = [];
            }
        },
        
        // Visualisation d'un résultat
        async viewResult(taskId) {
            try {
                console.log('👁️ Visualisation résultat pour:', taskId);
                
                const response = await fetch(`/scrape/${taskId}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const result = await response.json();
                if (result.success && result.data) {
                    this.modal = {
                        show: true,
                        title: `Scraping Result - ${result.data.url || 'Unknown URL'}`,
                        content: result.data.result || result.data.structured_content || result.data.raw_content || 'No content available',
                        taskId: taskId,
                        metadata: {
                            output_format: result.data.output_format,
                            execution_time_ms: result.data.execution_time_ms,
                            tokens_used: result.data.tokens_used,
                            url: result.data.url,
                            created_at: result.data.created_at
                        }
                    };
                } else {
                    throw new Error('Failed to load task result');
                }
                
            } catch (error) {
                console.error('❌ Erreur visualisation:', error);
                this.showNotification(
                    'Failed to load result',
                    'error',
                    error.message
                );
            }
        },
        
        // Reset du formulaire
        resetForm() {
            this.form = {
                url: '',
                output_format: 'markdown',
                use_llm: true,
                use_cache: true,
                custom_instructions: ''
            };
            this.urlValidation = {
                isValid: false,
                error: null
            };
        },
        
        // Affichage des notifications
        showNotification(message, type = 'info', details = '') {
            this.notification = {
                show: true,
                type: type,
                message: message,
                details: details
            };
            
            // Auto-hide après 5 secondes sauf pour les erreurs
            if (type !== 'error') {
                setTimeout(() => {
                    this.notification.show = false;
                }, 5000);
            }
        },
        
        // Fermeture des notifications
        hideNotification() {
            this.notification.show = false;
        },
        
        // Setup des event listeners
        setupEventListeners() {
            // Validation URL en temps réel
            this.$watch('form.url', () => {
                this.validateUrl();
            });
            
            // Auto-fermeture du modal avec Escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.modal.show) {
                    this.modal.show = false;
                }
            });
        },
        
        // === WEBSOCKET MANAGEMENT ===
        
        // Initialisation WebSocket
        initWebSocket() {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                console.log('🔌 Connexion WebSocket:', wsUrl);
                this.websocket = new WebSocket(wsUrl);
                
                this.websocket.onopen = (event) => {
                    console.log('✅ WebSocket connecté');
                    this.wsConnected = true;
                    this.wsReconnectAttempts = 0;
                    
                    // Ping périodique pour maintenir la connexion
                    this.startPingInterval();
                };
                
                this.websocket.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleWebSocketMessage(message);
                    } catch (error) {
                        console.error('❌ Erreur parsing message WebSocket:', error);
                    }
                };
                
                this.websocket.onclose = (event) => {
                    console.log('📴 WebSocket fermé:', event.code, event.reason);
                    this.wsConnected = false;
                    
                    // Tentative de reconnexion automatique
                    if (this.wsReconnectAttempts < this.wsMaxReconnectAttempts) {
                        this.wsReconnectAttempts++;
                        console.log(`🔄 Reconnexion WebSocket (${this.wsReconnectAttempts}/${this.wsMaxReconnectAttempts})...`);
                        setTimeout(() => this.initWebSocket(), 2000 * this.wsReconnectAttempts);
                    } else {
                        console.warn('⚠️ Nombre max de reconnexions atteint');
                        this.showNotification(
                            'Connection lost',
                            'error',
                            'Real-time updates are disabled. Please refresh the page.'
                        );
                    }
                };
                
                this.websocket.onerror = (error) => {
                    console.error('❌ Erreur WebSocket:', error);
                };
                
            } catch (error) {
                console.error('❌ Erreur initialisation WebSocket:', error);
            }
        },
        
        // Gestion des messages WebSocket
        handleWebSocketMessage(message) {
            const { type, data, task_id } = message;
            
            switch (type) {
                case 'task_update':
                    this.handleTaskUpdate(task_id, data);
                    break;
                    
                case 'stats_update':
                    this.handleStatsUpdate(data);
                    break;
                    
                case 'notification':
                    this.showNotification(data.message, data.type, data.details);
                    break;
                    
                case 'pong':
                    // Réponse au ping - connection active
                    break;
                    
                default:
                    console.log('📨 Message WebSocket non géré:', type, data);
            }
        },
        
        // Gestion des mises à jour de tâches temps réel
        handleTaskUpdate(taskId, update) {
            console.log('📈 Mise à jour tâche:', taskId, update);
            
            // Mettre à jour la tâche dans la liste
            const taskIndex = this.tasks.findIndex(task => task.id === taskId);
            if (taskIndex !== -1) {
                // Merger les données de mise à jour
                this.tasks[taskIndex] = { ...this.tasks[taskIndex], ...update };
            }
            
            // Si c'est la tâche courante, mettre à jour la progression
            if (this.currentTask && this.currentTask.id === taskId) {
                this.currentTask = { ...this.currentTask, ...update };
                
                if (update.progress !== undefined) {
                    this.progress = update.progress;
                }
                if (update.message) {
                    this.progressMessage = update.message;
                }
                
                // Si terminé, notifier l'utilisateur
                if (update.status === 'completed') {
                    this.isLoading = false;
                    this.progress = 100;
                    this.progressMessage = 'Completed!';
                    this.showNotification(
                        'Scraping completed!',
                        'success',
                        `Task ${taskId} finished successfully`
                    );
                    
                    // Reset du formulaire et état après 3 secondes
                    setTimeout(() => {
                        this.resetForm();
                        this.currentTask = null;
                        this.unsubscribeFromTask(taskId);
                    }, 3000);
                    
                } else if (update.status === 'failed') {
                    this.isLoading = false;
                    this.progress = 0;
                    this.progressMessage = 'Failed';
                    this.showNotification(
                        'Scraping failed',
                        'error',
                        update.error || 'Unknown error occurred'
                    );
                    
                    // Reset après 5 secondes
                    setTimeout(() => {
                        this.currentTask = null;
                        this.unsubscribeFromTask(taskId);
                    }, 5000);
                }
            }
        },
        
        // Gestion des mises à jour de statistiques
        handleStatsUpdate(stats) {
            // Mettre à jour les statistiques dans l'interface
            // TODO: Implémenter la mise à jour des métriques sidebar
            console.log('📊 Statistiques mises à jour:', stats);
        },
        
        // Abonnement aux mises à jour d'une tâche
        subscribeToTask(taskId) {
            if (this.websocket && this.wsConnected) {
                const message = {
                    type: 'subscribe_task',
                    task_id: taskId
                };
                this.websocket.send(JSON.stringify(message));
                console.log('🔔 Abonné aux mises à jour de la tâche:', taskId);
            }
        },
        
        // Désabonnement d'une tâche
        unsubscribeFromTask(taskId) {
            if (this.websocket && this.wsConnected) {
                const message = {
                    type: 'unsubscribe_task',
                    task_id: taskId
                };
                this.websocket.send(JSON.stringify(message));
                console.log('🔕 Désabonné de la tâche:', taskId);
            }
        },
        
        // Ping périodique pour maintenir la connexion
        startPingInterval() {
            setInterval(() => {
                if (this.websocket && this.wsConnected) {
                    const pingMessage = { type: 'ping' };
                    this.websocket.send(JSON.stringify(pingMessage));
                }
            }, 30000); // Ping toutes les 30 secondes
        },
        
        // === FIN WEBSOCKET ===
        
        // === EXPORT FUNCTIONS ===
        
        // Copier dans le presse-papiers
        copyToClipboard(content) {
            if (!content) {
                this.showNotification('Nothing to copy', 'error');
                return;
            }
            
            navigator.clipboard.writeText(content).then(() => {
                this.showNotification(
                    'Copied to clipboard!',
                    'success',
                    `${content.length} characters copied`
                );
            }).catch(err => {
                console.error('❌ Erreur copie presse-papiers:', err);
                this.showNotification('Failed to copy', 'error', 'Clipboard access denied');
            });
        },
        
        // Télécharger le résultat
        downloadResult() {
            if (!this.modal.content) {
                this.showNotification('No content to download', 'error');
                return;
            }
            
            try {
                const metadata = this.modal.metadata || {};
                const format = metadata.output_format || 'markdown';
                const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
                const url = metadata.url ? new URL(metadata.url).hostname : 'unknown';
                
                // Préparer le contenu avec métadonnées
                const header = [
                    `# Scrapinium Export`,
                    `**URL:** ${metadata.url || 'N/A'}`,
                    `**Format:** ${format}`,
                    `**Date:** ${new Date().toLocaleString()}`,
                    `**Task ID:** ${this.modal.taskId || 'N/A'}`,
                    `**Execution Time:** ${metadata.execution_time_ms || 0}ms`,
                    `**Tokens Used:** ${metadata.tokens_used || 0}`,
                    ``,
                    `---`,
                    ``,
                    this.modal.content
                ].join('\n');
                
                // Déterminer l'extension de fichier
                const extensions = {
                    'markdown': 'md',
                    'html': 'html',
                    'json': 'json',
                    'text': 'txt'
                };
                const ext = extensions[format] || 'txt';
                
                const filename = `scrapinium-${url}-${timestamp}.${ext}`;
                
                // Créer et télécharger le fichier
                const blob = new Blob([header], { type: 'text/plain;charset=utf-8' });
                const downloadUrl = URL.createObjectURL(blob);
                
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(downloadUrl);
                
                this.showNotification(
                    'File downloaded!',
                    'success',
                    `Saved as ${filename}`
                );
                
            } catch (error) {
                console.error('❌ Erreur téléchargement:', error);
                this.showNotification(
                    'Download failed',
                    'error',
                    error.message
                );
            }
        },
        
        // === FIN EXPORT ===
        
        // Utilitaires
        formatDate(dateString) {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString();
        },
        
        getStatusColor(status) {
            const colors = {
                'pending': 'text-blue-400',
                'running': 'text-yellow-400',
                'completed': 'text-green-400',
                'failed': 'text-red-400'
            };
            return colors[status] || 'text-slate-400';
        },
        
        getStatusText(status) {
            const texts = {
                'pending': 'Pending',
                'running': 'Running',
                'completed': 'Completed',
                'failed': 'Failed'
            };
            return texts[status] || status;
        }
    };
}

// Export pour utilisation globale
window.scrapiniumApp = scrapiniumApp;

console.log('📱 Scrapinium App module loaded');