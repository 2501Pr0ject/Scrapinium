/**
 * Scrapinium Batch Processing - v0.7.0
 * Gestion du traitement par lots
 */

console.log('📦 Chargement du module Batch Processing');

class BatchProcessor {
    constructor() {
        this.batchJobs = new Map();
        this.isProcessing = false;
        this.currentUrls = [];
        
        this.initEventListeners();
        this.loadBatchJobs();
    }
    
    initEventListeners() {
        console.log('🔧 Initialisation des event listeners batch');
        
        // Input method toggle
        const inputMethods = document.querySelectorAll('input[name="input-method"]');
        inputMethods.forEach(method => {
            method.addEventListener('change', () => this.toggleInputMethod());
        });
        
        // URL textarea monitoring
        const urlTextarea = document.getElementById('batch-urls');
        if (urlTextarea) {
            urlTextarea.addEventListener('input', () => this.updateUrlCount());
        }
        
        // File upload
        const fileUpload = document.getElementById('file-upload');
        const fileDropArea = fileUpload?.parentElement;
        
        if (fileDropArea && fileUpload) {
            // Click to browse
            fileDropArea.addEventListener('click', () => fileUpload.click());
            
            // Drag and drop
            fileDropArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileDropArea.classList.add('border-indigo-500', 'bg-indigo-500/10');
            });
            
            fileDropArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                fileDropArea.classList.remove('border-indigo-500', 'bg-indigo-500/10');
            });
            
            fileDropArea.addEventListener('drop', (e) => {
                e.preventDefault();
                fileDropArea.classList.remove('border-indigo-500', 'bg-indigo-500/10');
                this.handleFileUpload(e.dataTransfer.files[0]);
            });
            
            fileUpload.addEventListener('change', (e) => {
                if (e.target.files[0]) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }
        
        // Start batch button
        const startButton = document.getElementById('start-batch');
        if (startButton) {
            startButton.addEventListener('click', () => this.startBatchProcessing());
        }
        
        // Refresh batches button
        const refreshButton = document.getElementById('refresh-batches');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadBatchJobs());
        }
    }
    
    toggleInputMethod() {
        const selectedMethod = document.querySelector('input[name="input-method"]:checked')?.value;
        const manualEntry = document.getElementById('manual-entry');
        const fileEntry = document.getElementById('file-entry');
        
        if (selectedMethod === 'manual') {
            manualEntry?.classList.remove('hidden');
            fileEntry?.classList.add('hidden');
        } else {
            manualEntry?.classList.add('hidden');
            fileEntry?.classList.remove('hidden');
        }
        
        console.log('🔄 Méthode d\'input changée:', selectedMethod);
    }
    
    updateUrlCount() {
        const textarea = document.getElementById('batch-urls');
        const counter = document.getElementById('url-count');
        
        if (textarea && counter) {
            const urls = this.parseUrls(textarea.value);
            counter.textContent = `${urls.length} URLs`;
            
            // Validation visuelle
            if (urls.length > 100) {
                counter.classList.add('text-red-400');
                counter.textContent = `${urls.length} URLs (Max: 100)`;
            } else {
                counter.classList.remove('text-red-400');
            }
        }
    }
    
    parseUrls(text) {
        if (!text.trim()) return [];
        
        const lines = text.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        
        // Valider les URLs
        const validUrls = [];
        for (const line of lines) {
            try {
                new URL(line);
                if (line.startsWith('http://') || line.startsWith('https://')) {
                    validUrls.push(line);
                }
            } catch (e) {
                // URL invalide, ignorer
            }
        }
        
        return validUrls;
    }
    
    async handleFileUpload(file) {
        console.log('📁 Upload de fichier:', file.name);
        
        if (!file) return;
        
        // Vérifier le type de fichier
        const allowedTypes = ['text/plain', 'text/csv', 'application/csv'];
        if (!allowedTypes.includes(file.type) && !file.name.endsWith('.txt') && !file.name.endsWith('.csv')) {
            this.showNotification('Type de fichier non supporté. Utilisez .txt ou .csv', 'error');
            return;
        }
        
        try {
            const text = await file.text();
            const urls = this.parseUrls(text);
            
            if (urls.length === 0) {
                this.showNotification('Aucune URL valide trouvée dans le fichier', 'error');
                return;
            }
            
            if (urls.length > 100) {
                this.showNotification(`Trop d'URLs (${urls.length}). Maximum: 100`, 'error');
                return;
            }
            
            // Basculer vers manual entry et remplir le textarea
            document.querySelector('input[name="input-method"][value="manual"]').checked = true;
            this.toggleInputMethod();
            
            const textarea = document.getElementById('batch-urls');
            if (textarea) {
                textarea.value = urls.join('\n');
                this.updateUrlCount();
            }
            
            this.showNotification(`${urls.length} URLs chargées depuis ${file.name}`, 'success');
            
        } catch (error) {
            console.error('❌ Erreur lecture fichier:', error);
            this.showNotification('Erreur lors de la lecture du fichier', 'error');
        }
    }
    
    async startBatchProcessing() {
        console.log('🚀 Démarrage batch processing');
        
        if (this.isProcessing) {
            this.showNotification('Un batch est déjà en cours', 'error');
            return;
        }
        
        // Récupérer les URLs
        const textarea = document.getElementById('batch-urls');
        const urls = this.parseUrls(textarea?.value || '');
        
        if (urls.length === 0) {
            this.showNotification('Aucune URL valide à traiter', 'error');
            return;
        }
        
        if (urls.length > 100) {
            this.showNotification('Trop d\'URLs. Maximum: 100', 'error');
            return;
        }
        
        // Récupérer la configuration
        const batchName = document.getElementById('batch-name')?.value || null;
        const outputFormat = document.getElementById('batch-format')?.value || 'markdown';
        const parallelLimit = parseInt(document.getElementById('batch-parallel')?.value || '3');
        const delay = parseFloat(document.getElementById('batch-delay')?.value || '1.0');
        
        const batchRequest = {
            urls: urls,
            batch_name: batchName,
            output_format: outputFormat,
            llm_provider: 'ollama',
            parallel_limit: parallelLimit,
            delay_between_requests: delay
        };
        
        try {
            this.isProcessing = true;
            this.updateStartButton(true);
            
            console.log('📤 Envoi batch request:', batchRequest);
            
            const response = await fetch('/scrape/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(batchRequest)
            });
            
            const result = await response.json();
            console.log('📥 Réponse batch:', result);
            
            if (result.success) {
                this.showNotification(
                    `Batch créé: ${result.data.batch_name}`,
                    'success',
                    `${result.data.total_urls} URLs en traitement`
                );
                
                // Reset le formulaire
                this.resetForm();
                
                // Recharger la liste des batches
                await this.loadBatchJobs();
                
                // Démarrer le monitoring de ce batch
                this.monitorBatch(result.data.batch_id);
                
            } else {
                throw new Error(result.message || 'Erreur inconnue');
            }
            
        } catch (error) {
            console.error('❌ Erreur batch processing:', error);
            this.showNotification('Erreur lors du démarrage du batch', 'error', error.message);
        } finally {
            this.isProcessing = false;
            this.updateStartButton(false);
        }
    }
    
    updateStartButton(processing) {
        const button = document.getElementById('start-batch');
        if (!button) return;
        
        if (processing) {
            button.disabled = true;
            button.innerHTML = `
                <span class="flex items-center justify-center space-x-2">
                    <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    <span>Creating Batch...</span>
                </span>
            `;
            button.classList.add('opacity-75', 'cursor-not-allowed');
        } else {
            button.disabled = false;
            button.innerHTML = `
                <span class="flex items-center justify-center space-x-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <span>Start Batch Processing</span>
                </span>
            `;
            button.classList.remove('opacity-75', 'cursor-not-allowed');
        }
    }
    
    resetForm() {
        // Reset textarea
        const textarea = document.getElementById('batch-urls');
        if (textarea) {
            textarea.value = '';
            this.updateUrlCount();
        }
        
        // Reset nom du batch
        const nameInput = document.getElementById('batch-name');
        if (nameInput) {
            nameInput.value = '';
        }
        
        // Reset à manual entry
        const manualRadio = document.querySelector('input[name="input-method"][value="manual"]');
        if (manualRadio) {
            manualRadio.checked = true;
            this.toggleInputMethod();
        }
        
        console.log('🧹 Formulaire batch reset');
    }
    
    async loadBatchJobs() {
        console.log('📋 Chargement des batch jobs');
        
        try {
            const response = await fetch('/scrape/batch?limit=10');
            const result = await response.json();
            
            if (result.success) {
                this.renderBatchJobs(result.data.batches || []);
                console.log(`✅ ${result.data.batches?.length || 0} batch jobs chargés`);
            } else {
                console.error('❌ Erreur chargement batches:', result.message);
            }
            
        } catch (error) {
            console.error('❌ Erreur API batches:', error);
        }
    }
    
    renderBatchJobs(batches) {
        const container = document.getElementById('batch-jobs-list');
        if (!container) return;
        
        if (batches.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6">
                    <svg class="w-8 h-8 text-slate-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                    </svg>
                    <p class="text-slate-400 text-sm">No batch jobs yet</p>
                    <p class="text-slate-500 text-xs">Create your first batch job to process multiple URLs</p>
                </div>
            `;
            return;
        }
        
        const batchHtml = batches.map(batch => this.renderBatchCard(batch)).join('');
        container.innerHTML = batchHtml;
    }
    
    renderBatchCard(batch) {
        const statusColors = {
            'pending': 'text-blue-400 bg-blue-400/10 border-blue-400/20',
            'running': 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
            'completed': 'text-green-400 bg-green-400/10 border-green-400/20',
            'completed_with_errors': 'text-orange-400 bg-orange-400/10 border-orange-400/20',
            'failed': 'text-red-400 bg-red-400/10 border-red-400/20',
            'cancelled': 'text-slate-400 bg-slate-400/10 border-slate-400/20'
        };
        
        const statusClass = statusColors[batch.status] || statusColors['pending'];
        const progressColor = batch.status === 'completed' ? 'bg-green-500' : 'bg-indigo-500';
        
        return `
            <div class="glass-enhanced border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="font-medium text-slate-100">${batch.batch_name || 'Unnamed Batch'}</h3>
                            <p class="text-sm text-slate-400">${batch.total_urls} URLs • ${new Date(batch.created_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-1 text-xs font-medium rounded border ${statusClass}">
                            ${batch.status.toUpperCase()}
                        </span>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="flex justify-between text-sm text-slate-400 mb-1">
                        <span>Progress</span>
                        <span>${batch.progress}%</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="${progressColor} h-2 rounded-full transition-all duration-300" style="width: ${batch.progress}%"></div>
                    </div>
                </div>
                
                <div class="flex justify-between text-sm text-slate-400">
                    <div class="flex space-x-4">
                        <span>✅ ${batch.completed_tasks}</span>
                        <span>⏳ ${batch.running_tasks}</span>
                        <span>❌ ${batch.failed_tasks}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="batchProcessor.viewBatchDetails('${batch.batch_id}')" class="text-indigo-400 hover:text-indigo-300 transition-colors">
                            View
                        </button>
                        ${batch.status === 'running' ? `
                            <button onclick="batchProcessor.cancelBatch('${batch.batch_id}')" class="text-red-400 hover:text-red-300 transition-colors">
                                Cancel
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    async monitorBatch(batchId) {
        console.log('👁️ Monitoring batch:', batchId);
        
        const monitor = async () => {
            try {
                const response = await fetch(`/scrape/batch/${batchId}`);
                const result = await response.json();
                
                if (result.success) {
                    const batch = result.data;
                    console.log(`📊 Batch ${batchId}: ${batch.progress}% (${batch.status})`);
                    
                    // Mettre à jour l'affichage
                    await this.loadBatchJobs();
                    
                    // Continuer le monitoring si encore en cours
                    if (batch.status === 'running' || batch.status === 'pending') {
                        setTimeout(monitor, 2000); // Check toutes les 2 secondes
                    } else {
                        console.log(`✅ Monitoring terminé pour batch ${batchId}: ${batch.status}`);
                        this.showNotification(
                            `Batch terminé: ${batch.batch_name}`,
                            batch.status === 'completed' ? 'success' : 'info',
                            `${batch.completed_tasks}/${batch.total_urls} completed`
                        );
                    }
                }
            } catch (error) {
                console.error('❌ Erreur monitoring batch:', error);
            }
        };
        
        // Démarrer le monitoring
        setTimeout(monitor, 1000);
    }
    
    async viewBatchDetails(batchId) {
        console.log('👁️ Affichage détails batch:', batchId);
        // TODO: Implémenter modal de détails
        this.showNotification('Détails du batch - À implémenter', 'info');
    }
    
    async cancelBatch(batchId) {
        console.log('🛑 Annulation batch:', batchId);
        
        try {
            const response = await fetch(`/scrape/batch/${batchId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Batch annulé avec succès', 'success');
                await this.loadBatchJobs();
            } else {
                throw new Error(result.message || 'Erreur annulation');
            }
            
        } catch (error) {
            console.error('❌ Erreur annulation batch:', error);
            this.showNotification('Erreur lors de l\'annulation', 'error');
        }
    }
    
    showNotification(message, type = 'info', details = '') {
        // Utiliser le système de notifications existant
        if (window.scrapiniumApp) {
            const app = window.scrapiniumApp();
            app.showNotification(message, type, details);
        } else {
            console.log(`${type.toUpperCase()}: ${message}${details ? ' - ' + details : ''}`);
        }
    }
}

// Initialiser le batch processor quand le DOM est prêt
let batchProcessor;

document.addEventListener('DOMContentLoaded', function() {
    console.log('📦 Initialisation Batch Processor');
    batchProcessor = new BatchProcessor();
});

// Export pour utilisation globale
window.batchProcessor = batchProcessor;

console.log('📦 Module Batch Processing chargé');