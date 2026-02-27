const backBtn = document.getElementById("back-btn");
const memoriesFileInput = document.getElementById("memories-file-input");
const importMemoriesBtn = document.getElementById("import-memories-btn");
const settingsNavItems = document.querySelectorAll(".settings-nav-item");
const settingsSections = document.querySelectorAll(".settings-section");

backBtn.addEventListener("click", () => {
    window.history.back();
});

settingsNavItems.forEach(item => {
    item.addEventListener("click", (e) => {
        e.preventDefault();
        const section = item.getAttribute("data-section");
        
        settingsNavItems.forEach(nav => nav.classList.remove("active"));
        item.classList.add("active");
        
        settingsSections.forEach(sec => sec.classList.remove("active"));
        const targetSection = document.getElementById(`${section}-section`);
        if (targetSection) {
            targetSection.classList.add("active");
        }
    });
});

function navigateToSection() {
    const hash = window.location.hash.substring(1);
    if (hash) {
        const targetNavItem = Array.from(settingsNavItems).find(item => 
            item.getAttribute("data-section") === hash
        );
        
        if (targetNavItem) {
            targetNavItem.click();
        }
    }
}

importMemoriesBtn.addEventListener("click", () => {
    memoriesFileInput.click();
});

memoriesFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const statusContainer = document.getElementById("import-status-container");
    
    try {
        showImportStatus("loading", "File validation in progress...", statusContainer);
        
        await validateFile(file);
        
        const confirmed = confirm(
            "WARNING!\n\n" +
            "Importing a new Memories file will:\n" +
            "- Reset the state of all downloads\n" +
            "- Reset file status (success/error)\n" +
            "- Reset progress\n\n" +
            "Do you want to continue?"
        );
        
        if (!confirmed) {
            statusContainer.style.display = "none";
            return;
        }
        
        showImportStatus("loading", "Import in progress...", statusContainer);
        await importFile(file);
        
        showImportStatus("success", "File imported successfully!", statusContainer);
        
        setTimeout(() => {
            window.location.href = "index.html";
        }, 2000);
        
    } catch (error) {
        showImportStatus("error", `Error: ${error.message}`, statusContainer);
    } finally {
        memoriesFileInput.value = "";
    }
});

async function validateFile(file) {
    if (file.name.endsWith(".zip")) {
        return true;
    } else if (file.name === "memories_history.json") {
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            
            if (!data["Saved Media"] && !data["SavedMedia"]) {
                throw new Error("Invalid JSON structure - 'Saved Media' not found");
            }
            return true;
        } catch (err) {
            throw new Error(`Invalid JSON file: ${err.message}`);
        }
    } else {
        throw new Error(`File must be named "memories_history.json" or be a ZIP (found: "${file.name}")`);
    }
}

async function importFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await fetch("/api/import-new-memories", {
        method: "POST",
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        console.error("Error during import:", error);
        throw new Error(error.error || "Error during import");
    }
    
    return response.json();
}

function showImportStatus(type, message, container) {
    container.style.display = "block";
    
    let html = "";
    if (type === "loading") {
        html = `
            <div class="import-status-message import-status-loading">
                <div class="spinner"></div>
                <span>${message}</span>
            </div>
        `;
    } else if (type === "error") {
        html = `
            <div class="import-status-message import-status-error">
                <i data-lucide="alert-circle"></i>
                <span>${message}</span>
            </div>
        `;
    } else if (type === "success") {
        html = `
            <div class="import-status-message import-status-success">
                <i data-lucide="check-circle"></i>
                <span>${message}</span>
            </div>
        `;
    }
    
    container.innerHTML = html;
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

const changeStorageBtn = document.getElementById("change-storage-btn");
const currentStoragePath = document.getElementById("current-storage-path");

async function loadStoragePath() {
    try {
        const response = await fetch("/api/storage-path");
        const data = await response.json();
        if (data.path) {
            currentStoragePath.textContent = data.path;
        }
    } catch (error) {
        console.error("Error loading storage path:", error);
    }
}

changeStorageBtn.addEventListener("click", async () => {
    try {
        const response = await fetch("/api/storage-path/pick", {
            method: "POST"
        });
        const data = await response.json();
        if (data.success || data.path) {
            if (data.path) {
                currentStoragePath.textContent = data.path;
            }
            alert(data.message || "Storage path is fixed to the default location and cannot be changed.");
        } else {
            alert(data.message || "Unable to change storage folder.");
        }
    } catch (error) {
        console.error("Error selecting folder:", error);
        alert("Error accessing storage settings.");
    }
});

loadStoragePath();

let currentLanguage = "EN";
let translations = {};
const langFrRadio = document.getElementById("lang-fr");
const langEnRadio = document.getElementById("lang-en");

function detectSystemLanguage() {
    const browserLang = navigator.language || navigator.userLanguage || "en";
    
    if (browserLang.toLowerCase().startsWith("fr")) {
        return "FR";
    }
    return "EN";
}

async function loadTranslations() {
    try {
        const response = await fetch("/api/translations");
        if (!response.ok) throw new Error("Error loading translations");
        translations = await response.json();
        
        let savedLanguage = localStorage.getItem("currentLanguage");
        
        if (!savedLanguage) {
            currentLanguage = detectSystemLanguage();
            localStorage.setItem("currentLanguage", currentLanguage);
        } else {
            currentLanguage = savedLanguage;
        }
        
        if (currentLanguage === "FR") {
            langFrRadio.checked = true;
        } else {
            langEnRadio.checked = true;
        }
        
        applyTranslations();
    } catch (error) {
        console.error("Error loading translations:", error);
        currentLanguage = "EN";
    }
}

function applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(element => {
        if (!element.hasAttribute("data-i18n-original")) {
            element.setAttribute("data-i18n-original", element.textContent);
        }
    });
    
    if (currentLanguage === "EN") {
        document.querySelectorAll("[data-i18n]").forEach(element => {
            const original = element.getAttribute("data-i18n-original");
            if (original) {
                element.textContent = original;
            }
        });
        return;
    }
    
    const t = translations[currentLanguage] || {};
    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.getAttribute("data-i18n");
        if (key && t[key]) {
            element.textContent = t[key];
        }
    });
}

langFrRadio.addEventListener("change", () => {
    currentLanguage = "FR";
    localStorage.setItem("currentLanguage", "FR");
    applyTranslations();
});

langEnRadio.addEventListener("change", () => {
    currentLanguage = "EN";
    localStorage.setItem("currentLanguage", "EN");
    applyTranslations();
});

loadTranslations();

function applyTranslationsToNewContent() {
    document.querySelectorAll("[data-i18n]").forEach(element => {
        if (!element.hasAttribute("data-i18n-original")) {
            element.setAttribute("data-i18n-original", element.textContent);
        }
    });
    
    if (currentLanguage === "EN") {
        document.querySelectorAll("[data-i18n]").forEach(element => {
            const original = element.getAttribute("data-i18n-original");
            if (original) {
                element.textContent = original;
            }
        });
        return;
    }
    
    const t = translations[currentLanguage] || {};
    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.getAttribute("data-i18n");
        if (key && t[key]) {
            element.textContent = t[key];
        }
    });
}

fetch('modals.html')
    .then(response => response.text())
    .then(html => {
        const container = document.getElementById('modals-container');
        if (container) {
            container.innerHTML = html;
            applyTranslationsToNewContent();
            if (window.lucide) lucide.createIcons();
        }
    })
    .catch(error => console.error('Failed to load modals:', error));

navigateToSection();

const resetAllBtn = document.getElementById("reset-all-btn");

resetAllBtn.addEventListener("click", async () => {
    const confirmed = confirm(
        "Are you sure you want to reset all downloads and memories?\n\n" +
        "This action cannot be undone."
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch("/api/reset-all", {
            method: "POST"
        });
        
        if (response.ok) {
            alert("All downloads and memories have been reset!");
            setTimeout(() => {
                window.location.href = "index.html";
            }, 500);
        }
    } catch (error) {
        console.error("Error resetting all:", error);
        alert("Error resetting all.");
    }
});