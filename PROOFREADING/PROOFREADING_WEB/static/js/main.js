/**
 * L'ORÉAL - PRINTER PROOFREADING
 * Script principal de l'application
 */

// =================================
// VARIABLES GLOBALES
// =================================

let originalFiles = [];
let printerFiles = [];
let currentResults = [];

// =================================
// INITIALISATION
// =================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 L\'Oréal Proofreading App - Initialisée');
    
    // Setup des zones d'upload
    setupUploadZone('original-zone', 'original-input', originalFiles, 'original-files');
    setupUploadZone('printer-zone', 'printer-input', printerFiles, 'printer-files');
    
    // Setup des événements
    setupEventListeners();
    
    // Animation d'entrée
    animateEntrance();
});

// =================================
// SETUP UPLOAD ZONES
// =================================

function setupUploadZone(zoneId, inputId, filesArray, displayId) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const display = document.getElementById(displayId);

    if (!zone || !input) {
        console.error(`Elements not found: ${zoneId}, ${inputId}`);
        return;
    }

    // Clic sur la zone
    zone.addEventListener('click', () => {
        input.click();
    });

    // Drag over
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('dragover');
    });

    // Drag leave
    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
    });

    // Drop
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
        
        const items = e.dataTransfer.items;
        handleDroppedFiles(items, filesArray, display);
    });

    // Input change
    input.addEventListener('change', (e) => {
        handleFiles(e.target.files, filesArray, display);
    });
}

// =================================
// GESTION DES FICHIERS
// =================================

function handleDroppedFiles(items, filesArray, display) {
    filesArray.length = 0;
    
    for (let i = 0; i < items.length; i++) {
        const item = items[i].webkitGetAsEntry();
        if (item) {
            traverseFileTree(item, filesArray, display);
        }
    }
    
    // Petit délai pour laisser le temps de parcourir l'arbre
    setTimeout(() => {
        updateFileDisplay(filesArray, display);
        checkStartButton();
    }, 500);
}

function traverseFileTree(item, filesArray, display) {
    if (item.isFile) {
        item.file((file) => {
            if (file.name.toLowerCase().endsWith('.pdf')) {
                filesArray.push(file);
                updateFileDisplay(filesArray, display);
                checkStartButton();
            }
        });
    } else if (item.isDirectory) {
        const dirReader = item.createReader();
        dirReader.readEntries((entries) => {
            entries.forEach((entry) => {
                traverseFileTree(entry, filesArray, display);
            });
        });
    }
}

function handleFiles(files, filesArray, display) {
    filesArray.length = 0;
    
    Array.from(files).forEach(file => {
        if (file.name.toLowerCase().endsWith('.pdf')) {
            filesArray.push(file);
        }
    });

    updateFileDisplay(filesArray, display);
    checkStartButton();
}

function updateFileDisplay(filesArray, display) {
    if (!display) return;
    
    if (filesArray.length > 0) {
        display.innerHTML = `
            <small class="text-success">
                <i class="bi bi-check-circle-fill"></i> 
                ${filesArray.length} fichier(s) PDF sélectionné(s)
            </small>
        `;
    } else {
        display.innerHTML = '';
    }
}

// =================================
// VALIDATION & DÉMARRAGE
// =================================

function checkStartButton() {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) {
        const isValid = originalFiles.length > 0 && printerFiles.length > 0;
        startBtn.disabled = !isValid;
        
        if (isValid) {
            startBtn.classList.add('pulse');
        } else {
            startBtn.classList.remove('pulse');
        }
    }
}

// =================================
// EVENT LISTENERS
// =================================

function setupEventListeners() {
    // Bouton de démarrage
    const startBtn = document.getElementById('start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', startAnalysis);
    }

    // Bouton auto-approve
    const autoApproveBtn = document.getElementById('auto-approve-btn');
    if (autoApproveBtn) {
        autoApproveBtn.addEventListener('click', autoApproveAll);
    }

    // Bouton export CSV
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }

    // Bouton nouvelle analyse
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', () => {
            if (confirm('Êtes-vous sûr de vouloir recommencer une nouvelle analyse ?')) {
                location.reload();
            }
        });
    }
}

// =================================
// ANALYSE
// =================================

async function startAnalysis() {
    const threshold = document.getElementById('threshold').value;
    const formData = new FormData();

    // Ajouter les fichiers
    originalFiles.forEach(file => formData.append('original_folder', file));
    printerFiles.forEach(file => formData.append('printer_folder', file));
    formData.append('threshold', threshold);

    // Afficher le loader
    showLoader();
    disableStartButton();

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            console.log('✓ Analyse terminée:', data);
            await loadResults();
            showResults(data);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('✗ Erreur:', error);
        showError('Erreur lors de l\'analyse: ' + error.message);
        hideLoader();
        enableStartButton();
    }
}

// =================================
// AFFICHAGE DES RÉSULTATS
// =================================

async function loadResults() {
    try {
        const response = await fetch('/results');
        currentResults = await response.json();
        
        const resultsList = document.getElementById('results-list');
        if (!resultsList) return;
        
        resultsList.innerHTML = '';

        currentResults.forEach((result, index) => {
            const card = createResultCard(result, index);
            resultsList.appendChild(card);
        });
    } catch (error) {
        console.error('Erreur chargement résultats:', error);
    }
}

function createResultCard(result, index) {
    const card = document.createElement('div');
    card.className = 'result-card fade-in';
    card.style.animationDelay = `${index * 0.1}s`;

    const scoreClass = result.score >= 95 ? 'score-excellent' : 
                      result.score >= 80 ? 'score-good' : 'score-poor';

    const validationBadge = result.validation === 'Approved' ? 'bg-success' :
                           result.validation === 'Auto-Approved' ? 'bg-info' :
                           result.validation === 'Rejected' ? 'bg-danger' : 'bg-secondary';

    card.innerHTML = `
        <div class="row">
            <div class="col-md-8">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h5>
                            <i class="bi bi-file-earmark-text"></i>
                            ${escapeHtml(result.litho_code)}
                        </h5>
                        <p class="text-muted mb-0">${escapeHtml(result.filename)}</p>
                    </div>
                    <div class="text-end">
                        ${result.score ? 
                            `<div class="score-badge ${scoreClass}">${result.score}%</div>` : 
                            '<span class="badge bg-secondary">N/A</span>'
                        }
                        <div class="mt-2">
                            <span class="badge ${validationBadge}">${result.validation}</span>
                        </div>
                    </div>
                </div>

                <div class="row g-3">
                    <div class="col-6">
                        <h6 class="text-muted">Original</h6>
                        ${result.original_image ? 
                            `<img src="${result.original_image}" class="image-preview" alt="Original" onclick="showImageModal('${result.original_image}', 'Original')">` : 
                            '<p class="text-muted">Aucune image</p>'
                        }
                    </div>
                    <div class="col-6">
                        <h6 class="text-muted">Imprimeur</h6>
                        ${result.printer_image ? 
                            `<img src="${result.printer_image}" class="image-preview" alt="Imprimeur" onclick="showImageModal('${result.printer_image}', 'Imprimeur')">` : 
                            '<p class="text-muted">Aucune image</p>'
                        }
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <h6>Actions</h6>
                ${result.validation === 'Pending' ? `
                    <button class="btn btn-success w-100 mb-2" onclick="validateItem(${index}, true)">
                        <i class="bi bi-check-lg"></i> Approuver
                    </button>
                    <button class="btn btn-danger w-100" onclick="validateItem(${index}, false)">
                        <i class="bi bi-x-lg"></i> Rejeter
                    </button>
                ` : `
                    <p class="text-muted">${escapeHtml(result.comment)}</p>
                `}
                ${result.date ? `
                    <p class="text-muted mt-3 mb-0">
                        <small><i class="bi bi-clock"></i> ${result.date}</small>
                    </p>
                ` : ''}
            </div>
        </div>
    `;

    return card;
}

function showResults(data) {
    // Masquer l'upload section
    const uploadSection = document.getElementById('upload-section');
    if (uploadSection) uploadSection.style.display = 'none';

    // Afficher les résultats
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) resultsSection.style.display = 'block';

    // Mettre à jour les stats
    updateStats(data);
}

function updateStats(data) {
    const statTotal = document.getElementById('stat-total');
    const statMatched = document.getElementById('stat-matched');
    const statApproved = document.getElementById('stat-approved');

    if (statTotal) animateNumber(statTotal, 0, data.total, 1000);
    if (statMatched) animateNumber(statMatched, 0, data.matched, 1200);
    if (statApproved) animateNumber(statApproved, 0, data.auto_approved, 1400);
}

// =================================
// VALIDATION
// =================================

async function validateItem(index, approved) {
    let comment = '';
    
    if (!approved) {
        comment = prompt('Veuillez entrer un commentaire pour le rejet:');
        if (comment === null) return; // Annulé
    }

    try {
        const response = await fetch(`/validate/${index}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ approved, comment })
        });

        const data = await response.json();

        if (data.success) {
            await loadResults();
            showNotification(approved ? 'Fichier approuvé ✓' : 'Fichier rejeté', approved ? 'success' : 'warning');
        }
    } catch (error) {
        console.error('Erreur validation:', error);
        showError('Erreur lors de la validation');
    }
}

async function autoApproveAll() {
    const threshold = document.getElementById('threshold').value;
    
    if (!confirm(`Approuver automatiquement tous les fichiers avec un score ≥ ${threshold}% ?`)) {
        return;
    }

    try {
        const response = await fetch('/auto-approve', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ threshold: parseFloat(threshold) })
        });

        const data = await response.json();

        if (data.success) {
            await loadResults();
            showNotification(`${data.approved_count} fichier(s) approuvé(s) automatiquement ✓`, 'success');
        }
    } catch (error) {
        console.error('Erreur auto-approve:', error);
        showError('Erreur lors de l\'approbation automatique');
    }
}

// =================================
// EXPORT
// =================================

function exportToCSV() {
    window.location.href = '/export/csv';
    showNotification('Export CSV en cours...', 'info');
}

// =================================
// UTILITAIRES UI
// =================================

function showLoader() {
    const loader = document.getElementById('progress-container');
    if (loader) loader.style.display = 'block';
}

function hideLoader() {
    const loader = document.getElementById('progress-container');
    if (loader) loader.style.display = 'none';
}

function disableStartButton() {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) startBtn.disabled = true;
}

function enableStartButton() {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) {
        startBtn.disabled = false;
        checkStartButton();
    }
}

function showNotification(message, type = 'info') {
    // Créer une notification toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} notification-toast`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.5s ease;
    `;
    toast.innerHTML = `
        <strong>${message}</strong>
        <button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove après 3 secondes
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function showError(message) {
    alert('❌ ' + message);
}

function animateNumber(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            element.textContent = end;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

function animateEntrance() {
    const elements = document.querySelectorAll('.upload-zone, .threshold-control');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            el.style.transition = 'all 0.6s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showImageModal(src, title) {
    // Modal simple pour voir l'image en grand
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        cursor: pointer;
    `;
    
    modal.innerHTML = `
        <div style="max-width: 90%; max-height: 90%; position: relative;">
            <h3 style="color: white; text-align: center; margin-bottom: 20px;">${title}</h3>
            <img src="${src}" style="max-width: 100%; max-height: 80vh; border-radius: 10px;">
        </div>
    `;
    
    modal.onclick = () => modal.remove();
    document.body.appendChild(modal);
}

// =================================
// ANIMATIONS CSS
// =================================

const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .pulse {
        animation: pulse 1.5s ease-in-out infinite;
    }
`;
document.head.appendChild(style);

// =================================
// EXPORT GLOBAL
// =================================

window.validateItem = validateItem;
window.showImageModal = showImageModal;

console.log('✓ main.js chargé');