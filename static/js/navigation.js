/**
 * Navigation principale pour Scrapinium Dashboard
 */

console.log('🚀 Chargement du fichier navigation.js');

// Variables globales
let currentSection = 'scraping';

// Fonction pour changer de section
function showSection(sectionId) {
    console.log('🔄 Changement de section vers:', sectionId);
    
    // Cacher toutes les sections
    const sections = document.querySelectorAll('.section-content');
    console.log('📋 Sections trouvées:', sections.length);
    
    sections.forEach(section => {
        section.classList.add('hidden');
    });
    
    // Afficher la section sélectionnée
    const targetSection = document.getElementById(sectionId + '-section');
    if (targetSection) {
        targetSection.classList.remove('hidden');
        console.log('✅ Section affichée:', sectionId);
    } else {
        console.error('❌ Section non trouvée:', sectionId + '-section');
    }
    
    // Mettre à jour les boutons de navigation
    const navButtons = document.querySelectorAll('.nav-item');
    console.log('🔘 Boutons de navigation trouvés:', navButtons.length);
    
    navButtons.forEach(btn => {
        btn.classList.remove('bg-gradient-to-r', 'from-indigo-600', 'to-purple-600', 'hover:from-indigo-700', 'hover:to-purple-700', 'text-slate-100', 'shadow-lg');
        btn.classList.add('text-slate-400', 'hover:text-white', 'hover:bg-gradient-to-r', 'hover:from-slate-700', 'hover:to-slate-600');
    });
    
    // Mettre en évidence le bouton actif
    const activeBtn = document.getElementById(sectionId + '-tab');
    if (activeBtn) {
        activeBtn.classList.remove('text-slate-400', 'hover:text-white', 'hover:bg-gradient-to-r', 'hover:from-slate-700', 'hover:to-slate-600');
        activeBtn.classList.add('bg-gradient-to-r', 'from-indigo-600', 'to-purple-600', 'hover:from-indigo-700', 'hover:to-purple-700', 'text-slate-100', 'shadow-lg');
        console.log('✅ Bouton activé:', sectionId + '-tab');
    } else {
        console.error('❌ Bouton non trouvé:', sectionId + '-tab');
    }
    
    currentSection = sectionId;
}

// Fonction pour toggle la sidebar
function toggleSidebar() {
    console.log('🖱️ Toggle sidebar');
    const sidebar = document.getElementById('metrics-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('sidebar-collapsed');
        console.log('✅ Sidebar toggleé');
    } else {
        console.error('❌ Sidebar non trouvée');
    }
}

// Fonction pour fermer la sidebar
function closeSidebar() {
    console.log('🖱️ Fermeture sidebar');
    const sidebar = document.getElementById('metrics-sidebar');
    if (sidebar) {
        sidebar.classList.add('sidebar-collapsed');
        console.log('✅ Sidebar fermée');
    }
}

// Initialisation quand le DOM est prêt
function initNavigation() {
    console.log('📄 Initialisation de la navigation');
    
    // Vérifier les éléments
    const scrapingBtn = document.getElementById('scraping-tab');
    const tasksBtn = document.getElementById('tasks-tab');
    const batchBtn = document.getElementById('batch-tab');
    const templatesBtn = document.getElementById('templates-tab');
    const metricsBtn = document.getElementById('metrics-toggle');
    const closeSidebarBtn = document.getElementById('close-sidebar');
    
    console.log('🔍 Éléments trouvés:', {
        scrapingBtn: !!scrapingBtn,
        tasksBtn: !!tasksBtn,
        batchBtn: !!batchBtn,
        templatesBtn: !!templatesBtn,
        metricsBtn: !!metricsBtn,
        closeSidebarBtn: !!closeSidebarBtn
    });
    
    // Ajouter les event listeners
    if (scrapingBtn) {
        scrapingBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Clic sur Scraping');
            showSection('scraping');
        });
        console.log('✅ Listener Scraping ajouté');
    }
    
    if (tasksBtn) {
        tasksBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Clic sur Tasks');
            showSection('tasks');
        });
        console.log('✅ Listener Tasks ajouté');
    }
    
    if (batchBtn) {
        batchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Clic sur Batch');
            showSection('batch');
        });
        console.log('✅ Listener Batch ajouté');
    }
    
    if (templatesBtn) {
        templatesBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Clic sur Templates');
            showSection('templates');
        });
        console.log('✅ Listener Templates ajouté');
    }
    
    if (metricsBtn) {
        metricsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Clic sur Metrics');
            toggleSidebar();
        });
        console.log('✅ Listener Metrics ajouté');
    }
    
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Clic sur fermer sidebar');
            closeSidebar();
        });
        console.log('✅ Listener fermeture sidebar ajouté');
    }
    
    console.log('🎯 Navigation initialisée avec succès');
}

// Attendre que le DOM soit prêt
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavigation);
} else {
    initNavigation();
}

// Export pour debug
window.scrapiniumNavigation = {
    showSection,
    toggleSidebar,
    closeSidebar,
    currentSection: () => currentSection
};

console.log('✅ Navigation.js chargé complètement');