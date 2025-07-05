/**
 * Scrapinium Templates Management - v0.7.0
 * Gestion des templates de scraping
 */

console.log('📄 Chargement du module Templates Management');

class TemplatesManager {
    constructor() {
        this.templates = [];
        this.categories = [];
        this.selectedTemplate = null;
        this.filteredTemplates = [];
        
        this.initEventListeners();
        this.loadTemplates();
        this.loadCategories();
    }
    
    initEventListeners() {
        console.log('🔧 Initialisation des event listeners templates');
        
        // Search input
        const searchInput = document.getElementById('template-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterTemplates());
        }
        
        // Category filter
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => this.filterTemplates());
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refresh-templates');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshTemplates());
        }
        
        // Template selection
        const templateSelect = document.getElementById('selected-template');
        if (templateSelect) {
            templateSelect.addEventListener('change', (e) => this.selectTemplate(e.target.value));
        }
        
        // Start scraping button
        const startBtn = document.getElementById('start-template-scraping');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startTemplateScraping());
        }
    }
    
    async loadTemplates() {
        console.log('📋 Chargement des templates');
        
        try {
            const response = await fetch('/templates');
            const result = await response.json();
            
            if (result.success) {
                this.templates = result.data.templates;
                this.filteredTemplates = [...this.templates];
                this.renderTemplates();
                this.populateTemplateSelect();
                this.updateTemplatesCount();
                console.log(`✅ ${this.templates.length} templates chargés`);
            } else {
                console.error('❌ Erreur chargement templates:', result.message);
                this.showNotification('Erreur lors du chargement des templates', 'error');
            }
            
        } catch (error) {
            console.error('❌ Erreur API templates:', error);
            this.showNotification('Erreur de connexion aux templates', 'error');
        }
    }
    
    async loadCategories() {
        console.log('📂 Chargement des catégories');
        
        try {
            const response = await fetch('/templates/categories');
            const result = await response.json();
            
            if (result.success) {
                this.categories = result.data.categories;
                this.populateCategoryFilter();
                console.log(`✅ ${this.categories.length} catégories chargées`);
            } else {
                console.error('❌ Erreur chargement catégories:', result.message);
            }
            
        } catch (error) {
            console.error('❌ Erreur API catégories:', error);
        }
    }
    
    populateCategoryFilter() {
        const categoryFilter = document.getElementById('category-filter');
        if (!categoryFilter) return;
        
        // Clear existing options (except "All Categories")
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        
        // Add category options
        this.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.category;
            option.textContent = `${this.capitalizeFirst(cat.category)} (${cat.count})`;
            categoryFilter.appendChild(option);
        });
    }
    
    populateTemplateSelect() {
        const templateSelect = document.getElementById('selected-template');
        if (!templateSelect) return;
        
        // Clear existing options
        templateSelect.innerHTML = '<option value="">Choose a template...</option>';
        
        // Add template options
        this.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = `${template.name} (${this.capitalizeFirst(template.category)})`;
            templateSelect.appendChild(option);
        });
    }
    
    filterTemplates() {
        const searchTerm = document.getElementById('template-search')?.value.toLowerCase() || '';
        const categoryFilter = document.getElementById('category-filter')?.value || '';
        
        this.filteredTemplates = this.templates.filter(template => {
            const matchesSearch = !searchTerm || 
                template.name.toLowerCase().includes(searchTerm) ||
                template.description.toLowerCase().includes(searchTerm) ||
                template.tags.some(tag => tag.toLowerCase().includes(searchTerm));
            
            const matchesCategory = !categoryFilter || template.category === categoryFilter;
            
            return matchesSearch && matchesCategory;
        });
        
        this.renderTemplates();
        this.updateTemplatesCount();
        
        console.log(`🔍 Filtrage: ${this.filteredTemplates.length}/${this.templates.length} templates`);
    }
    
    renderTemplates() {
        const container = document.getElementById('templates-grid');
        const emptyState = document.getElementById('templates-empty');
        
        if (!container) return;
        
        if (this.filteredTemplates.length === 0) {
            container.classList.add('hidden');
            emptyState?.classList.remove('hidden');
            return;
        }
        
        container.classList.remove('hidden');
        emptyState?.classList.add('hidden');
        
        container.innerHTML = this.filteredTemplates.map(template => this.renderTemplateCard(template)).join('');
    }
    
    renderTemplateCard(template) {
        const categoryColors = {
            'blog': 'bg-blue-500/10 border-blue-500/20 text-blue-400',
            'ecommerce': 'bg-green-500/10 border-green-500/20 text-green-400',
            'news': 'bg-red-500/10 border-red-500/20 text-red-400',
            'academic': 'bg-purple-500/10 border-purple-500/20 text-purple-400',
            'real-estate': 'bg-orange-500/10 border-orange-500/20 text-orange-400'
        };
        
        const categoryClass = categoryColors[template.category] || 'bg-slate-500/10 border-slate-500/20 text-slate-400';
        const tagsHtml = template.tags.slice(0, 3).map(tag => 
            `<span class="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded">${tag}</span>`
        ).join('');
        
        return `
            <div class="glass-enhanced border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-all duration-300 transform hover:scale-[1.02]">
                <!-- Header -->
                <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                        <h3 class="font-semibold text-slate-100 mb-1">${template.name}</h3>
                        <p class="text-sm text-slate-400 line-clamp-2">${template.description}</p>
                    </div>
                    <span class="px-2 py-1 text-xs font-medium rounded border ${categoryClass} ml-2 flex-shrink-0">
                        ${this.capitalizeFirst(template.category)}
                    </span>
                </div>
                
                <!-- Instructions Preview -->
                <div class="mb-3">
                    <div class="text-xs text-slate-500 mb-1">Instructions:</div>
                    <div class="text-sm text-slate-300 bg-slate-800/50 rounded p-2 max-h-16 overflow-hidden">
                        ${template.instructions.substring(0, 100)}${template.instructions.length > 100 ? '...' : ''}
                    </div>
                </div>
                
                <!-- Tags -->
                <div class="flex flex-wrap gap-1 mb-3">
                    ${tagsHtml}
                    ${template.tags.length > 3 ? `<span class="px-2 py-1 text-xs text-slate-500">+${template.tags.length - 3}</span>` : ''}
                </div>
                
                <!-- Footer -->
                <div class="flex items-center justify-between text-xs text-slate-500">
                    <div class="flex items-center space-x-3">
                        <span>🎯 ${template.usage_count} uses</span>
                        <span>📊 ${template.output_format}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="templatesManager.useTemplate(${template.id})" 
                                class="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs transition-colors">
                            Use
                        </button>
                        <button onclick="templatesManager.viewTemplate(${template.id})" 
                                class="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-white rounded text-xs transition-colors">
                            View
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    useTemplate(templateId) {
        console.log('🎯 Utilisation template:', templateId);
        
        // Sélectionner le template dans le dropdown
        const templateSelect = document.getElementById('selected-template');
        if (templateSelect) {
            templateSelect.value = templateId;
            this.selectTemplate(templateId);
        }
        
        // Faire défiler vers la section quick use
        const quickUseSection = document.querySelector('#templates-section .glass-enhanced:nth-child(3)');
        if (quickUseSection) {
            quickUseSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        this.showNotification(`Template "${this.getTemplateName(templateId)}" sélectionné`, 'success');
    }
    
    viewTemplate(templateId) {
        console.log('👁️ Affichage template:', templateId);
        
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;
        
        // Create and show modal (you can enhance this)
        const modalContent = `
            <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-75">
                <div class="glass-enhanced rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <div class="p-6">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-xl font-bold text-slate-100">${template.name}</h2>
                            <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" 
                                    class="text-slate-400 hover:text-white">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="text-sm font-medium text-slate-300">Description:</label>
                                <p class="text-slate-400 mt-1">${template.description}</p>
                            </div>
                            
                            <div>
                                <label class="text-sm font-medium text-slate-300">Category:</label>
                                <p class="text-slate-400 mt-1">${this.capitalizeFirst(template.category)}</p>
                            </div>
                            
                            <div>
                                <label class="text-sm font-medium text-slate-300">Instructions:</label>
                                <pre class="text-slate-300 text-sm bg-slate-800/50 rounded p-3 mt-1 whitespace-pre-wrap">${template.instructions}</pre>
                            </div>
                            
                            <div>
                                <label class="text-sm font-medium text-slate-300">Tags:</label>
                                <div class="flex flex-wrap gap-1 mt-1">
                                    ${template.tags.map(tag => `<span class="px-2 py-1 text-xs bg-slate-700 text-slate-300 rounded">${tag}</span>`).join('')}
                                </div>
                            </div>
                            
                            <div class="flex space-x-3 pt-4">
                                <button onclick="templatesManager.useTemplate(${template.id}); this.parentElement.parentElement.parentElement.parentElement.parentElement.remove()" 
                                        class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
                                    Use This Template
                                </button>
                                <button onclick="this.parentElement.parentElement.parentElement.parentElement.parentElement.remove()" 
                                        class="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors">
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
    }
    
    selectTemplate(templateId) {
        if (!templateId) {
            this.selectedTemplate = null;
            return;
        }
        
        this.selectedTemplate = this.templates.find(t => t.id == templateId);
        console.log('✅ Template sélectionné:', this.selectedTemplate?.name);
    }
    
    async startTemplateScraping() {
        console.log('🚀 Démarrage scraping avec template');
        
        const url = document.getElementById('template-url')?.value;
        const templateId = document.getElementById('selected-template')?.value;
        const customInstructions = document.getElementById('template-custom-instructions')?.value;
        
        if (!url) {
            this.showNotification('Veuillez entrer une URL', 'error');
            return;
        }
        
        if (!templateId) {
            this.showNotification('Veuillez sélectionner un template', 'error');
            return;
        }
        
        const startBtn = document.getElementById('start-template-scraping');
        
        try {
            // Disable button
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.innerHTML = `
                    <span class="flex items-center space-x-2">
                        <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                        </svg>
                        <span>Starting...</span>
                    </span>
                `;
            }
            
            const requestData = {
                url: url,
                template_id: parseInt(templateId)
            };
            
            if (customInstructions) {
                requestData.custom_instructions = customInstructions;
            }
            
            const response = await fetch('/templates/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(
                    `Scraping démarré avec template "${this.getTemplateName(templateId)}"`,
                    'success',
                    `Task ID: ${result.data.task_id}`
                );
                
                // Reset form
                this.resetQuickUseForm();
                
                // Switch to tasks view to see progress
                if (window.scrapiniumNavigation) {
                    window.scrapiniumNavigation.showSection('tasks');
                }
                
            } else {
                throw new Error(result.message || 'Erreur inconnue');
            }
            
        } catch (error) {
            console.error('❌ Erreur scraping avec template:', error);
            this.showNotification('Erreur lors du démarrage du scraping', 'error', error.message);
        } finally {
            // Re-enable button
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.innerHTML = `
                    <span class="flex items-center space-x-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                        <span>Start Scraping</span>
                    </span>
                `;
            }
        }
    }
    
    resetQuickUseForm() {
        const urlInput = document.getElementById('template-url');
        const templateSelect = document.getElementById('selected-template');
        const instructionsTextarea = document.getElementById('template-custom-instructions');
        
        if (urlInput) urlInput.value = '';
        if (templateSelect) templateSelect.value = '';
        if (instructionsTextarea) instructionsTextarea.value = '';
        
        this.selectedTemplate = null;
        
        console.log('🧹 Formulaire template reset');
    }
    
    async refreshTemplates() {
        console.log('🔄 Rafraîchissement des templates');
        await this.loadTemplates();
        await this.loadCategories();
        this.showNotification('Templates rafraîchis', 'success');
    }
    
    updateTemplatesCount() {
        const countElement = document.getElementById('templates-count');
        if (countElement) {
            const total = this.templates.length;
            const filtered = this.filteredTemplates.length;
            countElement.textContent = filtered === total ? 
                `${total} templates` : 
                `${filtered}/${total} templates`;
        }
    }
    
    getTemplateName(templateId) {
        const template = this.templates.find(t => t.id == templateId);
        return template ? template.name : 'Unknown';
    }
    
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
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

// Initialiser le gestionnaire de templates quand le DOM est prêt
let templatesManager;

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 Initialisation Templates Manager');
    templatesManager = new TemplatesManager();
});

// Export pour utilisation globale
window.templatesManager = templatesManager;

console.log('📄 Module Templates Management chargé');