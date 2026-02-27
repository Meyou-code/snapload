let currentLanguage = "EN";
let translations = {};
let currentStep = 0;
const totalSteps = 5;
let selectedFile = null;
let currentCarouselIndex = 0;

const getElement = (id) => document.getElementById(id);
const getElements = (selector) => document.querySelectorAll(selector);

// Translation & Language Logic
function detectSystemLanguage() {
    const browserLang = navigator.language || navigator.userLanguage || "en";
    return browserLang.toLowerCase().startsWith("fr") ? "FR" : "EN";
}

async function loadTranslations() {
    try {
        const response = await fetch("/api/translations");
        if (!response.ok) throw new Error("Error loading translations");
        translations = await response.json();

        const savedLanguage = localStorage.getItem("currentLanguage");
        currentLanguage = savedLanguage ?? detectSystemLanguage();
        if (!savedLanguage) localStorage.setItem("currentLanguage", currentLanguage);

        const languageSelect = getElement("language-select");
        if (languageSelect) languageSelect.value = currentLanguage;

        applyTranslations();
    } catch (e) {
        console.error("Error loading translations:", e);
        currentLanguage = "EN";
    }
}

function applyTranslations() {
    // Store original text on first run
    getElements("[data-i18n]").forEach(el => {
        if (!el.hasAttribute("data-i18n-original")) {
            el.setAttribute("data-i18n-original", el.textContent);
        }
    });

    if (currentLanguage === "EN") {
        getElements("[data-i18n]").forEach(el => {
            const original = el.getAttribute("data-i18n-original");
            if (original) el.textContent = original;
        });
    } else {
        const t = translations[currentLanguage] || {};
        getElements("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            if (t[key]) el.textContent = t[key];
        });
    }
    updateNavigationButtons();
}

function getTranslation(key, defaultValue = "") {
    if (currentLanguage === "EN") return defaultValue;
    const t = translations[currentLanguage] || {};
    return t[key] || defaultValue;
}

async function saveLanguagePreference() {
    try {
        localStorage.setItem("currentLanguage", currentLanguage);
    } catch (err) {
        console.error("Error saving language preference:", err);
    }
}

// Carousel Logic
function showCarouselSlide(index) {
    const items = getElements('.carousel-item');
    const dots = getElements('.dot');

    if (index < 0) index = items.length - 1;
    if (index >= items.length) index = 0;

    currentCarouselIndex = index;

    items.forEach((item, i) => item.classList.toggle('active', i === index));
    dots.forEach((dot, i) => dot.classList.toggle('active', i === index));

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Modal Logic
function openInfoModal(type) {
    const modal = getElement('info-modal');
    const autoContent = getElement('info-auto-import-content');
    const manualContent = getElement('info-manual-import-content');
    const title = getElement('info-modal-title');

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    autoContent.style.display = 'none';
    manualContent.style.display = 'none';

    if (type === 'auto') {
        title.textContent = getTranslation("guideAutomaticImport", "Automatic Import");
        autoContent.style.display = 'block';
    } else if (type === 'manual') {
        title.textContent = getTranslation("guideManualImport", "Manual Import");
        manualContent.style.display = 'block';
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function closeInfoModal() {
    getElement('info-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function openFileUploadModal() {
    getElement('file-upload-modal').style.display = 'flex';
    hideMessages();
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function closeFileUploadModal() {
    getElement('file-upload-modal').style.display = 'none';
    selectedFile = null;
    getElement('file-input').value = '';
    getElement('file-info').style.display = 'none';
    getElement('validate-btn').disabled = true;
    hideMessages();
}

// Navigation Logic
function goToStep(stepNumber) {
    if (stepNumber < 0 || stepNumber > totalSteps) return;

    getElements('.step-content').forEach(c => c.classList.remove('active'));
    getElements('.step-indicator').forEach(i => i.classList.remove('active'));

    const content = getElement(`step-${stepNumber}`);
    const indicator = document.querySelector(`[data-step="${stepNumber}"]`);

    if (content) content.classList.add('active');
    if (indicator) indicator.classList.add('active');

    currentStep = stepNumber;
    getElement('current-step').textContent = currentStep + 1;

    updateNavigationButtons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateNavigationButtons() {
    const prevBtn = getElement('prev-btn');
    const nextBtn = getElement('next-btn');
    if (!prevBtn || !nextBtn) return;

    prevBtn.style.display = currentStep === 0 ? 'none' : 'flex';
    
    const isLastStep = currentStep === totalSteps;
    const nextKey = isLastStep ? "start" : "guideNext";
    const defaultText = isLastStep ? "Start" : "Next";
    
    // Update text content specifically for the span inside the button
    const nextSpan = nextBtn.querySelector('span');
    if (nextSpan) nextSpan.textContent = getTranslation(nextKey, defaultText);

    const iconName = isLastStep ? "arrow-right" : "chevron-right";
    const icon = nextBtn.querySelector('i');
    if (icon) icon.setAttribute('data-lucide', iconName);

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// File Handling
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    hideMessages();

    const name = file.name.toLowerCase();
    const isJson = name.endsWith('.json');
    const isZip = name.endsWith('.zip');

    if (isJson && file.name !== "memories_history.json") {
        showError(getTranslation("errorJsonName", "JSON file must be exactly 'memories_history.json'"));
        return;
    }

    if (isZip && !/^mydata~\d+\.zip$/i.test(file.name)) {
        showError(getTranslation("errorZipPattern", "ZIP file must follow pattern 'mydata~XXXX.zip'"));
        return;
    }

    if (!isJson && !isZip) {
        showError(getTranslation("errorFileType", "File must be JSON or ZIP"));
        return;
    }

    selectedFile = file;
    getElement('file-name').textContent = file.name;
    getElement('file-path').textContent = file.name;
    getElement('file-info').style.display = 'flex';
    getElement('validate-btn').disabled = false;
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function validateAndSaveFile() {
    if (!selectedFile) return;

    const overlay = getElement('loading-overlay');
    const btn = getElement('validate-btn');

    overlay.style.display = 'flex';
    btn.disabled = true;
    hideMessages();

    try {
        const isZip = selectedFile.name.toLowerCase().endsWith('.zip');
        const formData = new FormData();
        formData.append("file", selectedFile);
        if (isZip) formData.append("is_zip", "true");

        if (!isZip) {
            const content = await readFileAsText(selectedFile);
            const data = JSON.parse(content);
            if (!data["Saved Media"] && !data["SavedMedia"]) {
                throw new Error(getTranslation("errorFileStructure", "File missing 'Saved Media' structure"));
            }
        }

        const response = await fetch("/api/memories/upload", { method: "POST", body: formData });
        const result = await response.json();

        if (!response.ok) throw new Error(result.error || "Error saving file.");

        showSuccess();
        setTimeout(() => window.location.href = "/", 1000);
    } catch (error) {
        showError(error.message || "Error validating file.");
        btn.disabled = false;
    } finally {
        overlay.style.display = 'none';
    }
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error("Error reading file."));
        reader.readAsText(file);
    });
}

// UI Helpers
function showError(msg) {
    getElement('error-text').textContent = msg;
    getElement('error-message').style.display = 'flex';
    getElement('success-message').style.display = 'none';
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function showSuccess() {
    getElement('success-message').style.display = 'flex';
    getElement('error-message').style.display = 'none';
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function hideMessages() {
    getElement('error-message').style.display = 'none';
    getElement('success-message').style.display = 'none';
}

// Auto Import
async function handleAutoImport() {
    const btn = getElement('auto-import-memories-btn');
    const status = getElement('auto-import-status');
    const loading = getElement('auto-import-loading');
    const error = getElement('auto-import-error');
    const success = getElement('auto-import-success');

    btn.disabled = true;
    status.style.display = 'block';
    loading.style.display = 'flex';
    error.style.display = 'none';
    success.style.display = 'none';

    try {
        const res = await fetch("/api/memories/auto-import", { method: "POST" });
        const result = await res.json();

        if (result.ok) {
            loading.style.display = 'none';
            success.style.display = 'flex';
            setTimeout(() => window.location.href = "/", 1500);
        } else {
            throw new Error();
        }
    } catch {
        loading.style.display = 'none';
        error.style.display = 'flex';
        btn.disabled = false;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

// Image Zoom
function toggleZoom(src) {
    const modal = getElement('image-zoom-modal');
    const img = getElement('zoomed-image');
    if (src) {
        img.src = src;
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    } else {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        img.src = '';
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
    goToStep(0);
    loadTranslations();

    // Event Delegation for cleaner code
    document.body.addEventListener('click', (e) => {
        const target = e.target;
        
        // Navigation
        if (target.closest('#prev-btn')) goToStep(currentStep - 1);
        if (target.closest('#next-btn')) {
            currentStep < totalSteps ? goToStep(currentStep + 1) : openFileUploadModal();
        }
        if (target.classList.contains('step-indicator') || target.closest('.step-indicator')) {
             const step = target.closest('.step-indicator').dataset.step;
             goToStep(parseInt(step));
        }

        // Carousel
        if (target.closest('#carousel-prev')) showCarouselSlide(currentCarouselIndex - 1);
        if (target.closest('#carousel-next')) showCarouselSlide(currentCarouselIndex + 1);
        if (target.classList.contains('dot')) showCarouselSlide(parseInt(target.dataset.index));

        // Modals & Zoom
        if (target.closest('.zoomable-image')) toggleZoom(target.closest('.zoomable-image').src);
        if (target.closest('#close-zoom') || target.id === 'image-zoom-modal') toggleZoom(null);
        
        if (target.closest('#info-auto-import')) openInfoModal('auto');
        if (target.closest('#info-manual-import')) openInfoModal('manual');
        if (target.closest('#close-info-modal') || target.id === 'info-modal') closeInfoModal();

        if (target.closest('#fallback-upload-memories-btn')) openFileUploadModal();
        if (target.closest('#close-modal') || target.id === 'file-upload-modal') closeFileUploadModal();
        
        // Actions
        if (target.closest('#select-file-btn')) getElement('file-input').click();
        if (target.closest('#validate-btn')) validateAndSaveFile();
        if (target.closest('#auto-import-memories-btn')) handleAutoImport();
    });

    getElement('file-input')?.addEventListener('change', handleFileSelect);
    getElement('language-select')?.addEventListener('change', async (e) => {
        currentLanguage = e.target.value;
        await saveLanguagePreference();
        applyTranslations();
    });
});