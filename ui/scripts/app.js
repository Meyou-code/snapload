let currentLanguage = "EN";
let translations = {};

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

    const languageSelect = document.getElementById("language-select");
    if (languageSelect) languageSelect.value = currentLanguage;

    applyTranslations();
  } catch (e) {
    console.error("Error loading translations:", e);
    currentLanguage = "EN";
  }
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    if (!el.hasAttribute("data-i18n-original"))
      el.setAttribute("data-i18n-original", el.textContent);
  });

  const appTitle = document.getElementById("app-title");
  const appDescription = document.getElementById("app-description");

  if (currentLanguage === "EN") {
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const original = el.getAttribute("data-i18n-original");
      if (original) el.textContent = original;
    });
    if (appTitle) appTitle.textContent = "SnapLoad";
    if (appDescription) appDescription.textContent = "Download Snapchat Memories";
    return;
  }

  const t = translations[currentLanguage] || {};
  if (appTitle && t.appName) appTitle.textContent = t.appName;
  if (appDescription && t.appDescription) appDescription.textContent = t.appDescription;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key]) el.textContent = t[key];
  });
}

function applyTranslationsToNewContent() {
  const t = translations[currentLanguage] || {};
  document.querySelectorAll("[data-i18n]").forEach(el => {
    if (currentLanguage === "EN") {
      if (!el.hasAttribute("data-i18n-original"))
        el.setAttribute("data-i18n-original", el.textContent);
      const original = el.getAttribute("data-i18n-original");
      if (original) el.textContent = original;
    } else {
      const key = el.getAttribute("data-i18n");
      if (t[key]) el.textContent = t[key];
    }
  });
}

function getTranslation(key, defaultValue = "") {
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

async function loadStoragePath() {
  try {
    const data = await apiRequest("/api/storage-path");
    const el = document.getElementById("storage-folder-info");
    if (el && data.path) el.textContent = data.path;
  } catch (err) {
    console.error("Error retrieving storage path:", err);
  }
}

async function apiRequest(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) throw new Error(`API Error: ${resp.status}`);
  return resp.json();
}

function formatTime(seconds) {
  if (seconds == null || !isFinite(seconds)) return "";
  const s = Math.round(seconds);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  if (h > 0) return `${h}h ${m % 60}m ${s % 60}s`;
  if (m > 0) return `${m}m ${s % 60}s`;
  return `${s}s`;
}

function isDeadLinksModalDismissed() {
  return localStorage.getItem("deadLinksModalDismissed") === "true";
}

function setDeadLinksModalDismissed(value) {
  if (value) localStorage.setItem("deadLinksModalDismissed", "true");
  else localStorage.removeItem("deadLinksModalDismissed");
}

const statusText = document.getElementById("status-text");
const progressText = document.getElementById("progress-text");
const progressFill = document.getElementById("progress-fill");
const progressPercent = document.getElementById("progress-percent");
const currentFile = document.getElementById("current-file");
const downloadSpeed = document.getElementById("download-speed");
const networkSpeed = document.getElementById("network-speed");
const timeRemaining = document.getElementById("time-remaining");
const statSuccess = document.getElementById("stat-success");
const statFailed = document.getElementById("stat-failed");
const statTotal = document.getElementById("stat-total");
const startBtn = document.getElementById("start-btn");
const stopBtn = document.getElementById("stop-btn");
const openFolderBtn = document.getElementById("open-folder-btn");
const stoppingSpinner = document.getElementById("stopping-spinner");

const fusionStatusText = document.getElementById("fusion-status-text");
const fusionZipsCount = document.getElementById("fusion-zips-count");
const fusionProgressFill = document.getElementById("fusion-progress-fill");
const fusionProgressPercent = document.getElementById("fusion-progress-percent");
const fusionCurrentFile = document.getElementById("fusion-current-file");
const fusionStartBtn = document.getElementById("fusion-start-btn");
const fusionStopBtn = document.getElementById("fusion-stop-btn");
const fusionRefreshBtn = document.getElementById("fusion-refresh-btn");
const fusionMoveFusedBtn = document.getElementById("fusion-move-fused-btn");
const fusionRefreshFusedBtn = document.getElementById("fusion-refresh-fused-btn");
const fusionFusedList = document.getElementById("fusion-fused-list");
const fusionStatTotal = document.getElementById("fusion-stat-total");
const fusionStatSuccess = document.getElementById("fusion-stat-success");
const fusionStatFailed = document.getElementById("fusion-stat-failed");
const fusionZipsList = document.getElementById("fusion-zips-list");
const infoBtn = document.getElementById("info-btn");
const storageInfoBtn = document.getElementById("storage-info-btn");

let deadLinksModal, deadLinksCloseBtn, deadLinksChangeFileBtn;
let infoModal, modalClose, closeWarningModal, closeWarningBtn, closeWarningOkBtn, storageInfoModal;

let statusTimer = null;
let fusionStatusTimer = null;
let closeAttemptTimer = null;
let lastFusionMessage = "";
let lastStopping = false;
let windowHasFocus = true;

function updateUI(data) {
  const { status } = data;
  const { running, stopping, total, completed, success, failed, current_filename,
    files_per_second, mb_per_second, eta_seconds, dead_links_detected } = status;

  if (!running && lastStopping && !stopping)
    statusText.textContent = getTranslation("stoppingCompleted", "Stopping completed");
  else if (running)
    statusText.textContent = getTranslation("downloading", "Downloading");
  else if (stopping)
    statusText.textContent = getTranslation("stopping", "Stopping...");
  else
    statusText.textContent = getTranslation("ready", "Ready");

  statTotal.textContent = total;
  statSuccess.textContent = success;
  statFailed.textContent = failed;

  const filesWord = getTranslation("files", "files");
  progressText.textContent = `${completed} / ${total} ${filesWord}`;
  const pct = total > 0 ? ((completed / total) * 100).toFixed(1) : 0;
  progressFill.style.width = `${pct}%`;
  progressPercent.textContent = `${pct}%`;

  currentFile.textContent = current_filename ? `${getTranslation("file", "File")}: ${current_filename}` : "";
  downloadSpeed.textContent = `${files_per_second.toFixed(2)} ${getTranslation("downloadSpeed", "files/s")}`;
  networkSpeed.textContent = mb_per_second != null ? `${mb_per_second.toFixed(2)} ${getTranslation("networkSpeed", "MB/s")}` : "0.00 MB/s";
  timeRemaining.textContent = eta_seconds != null
    ? `${getTranslation("estimatedTimeRemaining", "Estimated time remaining")} : ${formatTime(eta_seconds)}`
    : "";

  startBtn.disabled = running;
  stopBtn.disabled = !running;
  stoppingSpinner.style.display = stopping ? "flex" : "none";

  const stopIcon = stopBtn.querySelector("i");
  const stopSpan = stopBtn.querySelector("span");
  if (stopping) {
    stopBtn.classList.add("stopping");
    if (stopIcon) stopIcon.setAttribute("data-lucide", "loader");
    if (stopSpan) stopSpan.textContent = getTranslation("stopping", "Stopping...");
  } else {
    stopBtn.classList.remove("stopping");
    if (stopIcon) stopIcon.setAttribute("data-lucide", "square");
    if (stopSpan) stopSpan.textContent = getTranslation("stop", "Stop");
  }
  lucide.createIcons();

  let startLabel = getTranslation("startDownload", "Start Download");
  if (!running) {
    if (total > 0 && completed > 0 && completed < total)
      startLabel = getTranslation("resumeDownload", "Resume Download");
    else if (total > 0 && completed === total)
      startLabel = getTranslation("reDownload", "Re-download");
  }
  startBtn.textContent = startLabel;

  if (dead_links_detected && !isDeadLinksModalDismissed())
    deadLinksModal.style.display = "block";

  lastStopping = stopping;
}

async function refreshStatus() {
  if (!windowHasFocus && !statusTimer) return;
  try {
    const data = await apiRequest("/api/status");
    updateUI(data);
  } catch (e) {
    console.error(e);
  }
}

async function checkCloseAttempt() {
  try {
    const data = await apiRequest("/api/close-attempt");
    if (data.close_attempt) closeWarningModal.style.display = "block";
  } catch (e) {
    console.error(e);
  }
}

async function onStart() {
  try {
    startBtn.disabled = true;
    setDeadLinksModalDismissed(false);
    deadLinksModal.style.display = "none";

    const res = await apiRequest("/api/start", { method: "POST", body: JSON.stringify({}) });
    if (!res.ok) {
      alert(res.error || getTranslation("errorStartingDownload", "Unable to start download"));
      return;
    }
    if (!statusTimer) statusTimer = setInterval(refreshStatus, 1000);
    await refreshStatus();
  } catch (e) {
    console.error("Error starting download:", e);
    alert(getTranslation("errorStartingDownload", "Unable to start download"));
  }
}

async function onStop() {
  try {
    stopBtn.disabled = true;
    stoppingSpinner.style.display = "flex";
    await apiRequest("/api/stop", { method: "POST", body: JSON.stringify({}) });
    await refreshStatus();
  } catch (e) {
    console.error(e);
  }
}

document.querySelectorAll(".tab-button").forEach(button => {
  button.addEventListener("click", () => {
    const targetTab = button.getAttribute("data-tab");
    document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(`${targetTab}-tab`).classList.add("active");
  });
});

async function refreshFusionStatus() {
  if (!windowHasFocus) return;
  try {
    const { status } = await apiRequest("/api/fusion/status");
    fusionStatusText.textContent = status.running
      ? getTranslation("fusionRunning", "Fusion running...")
      : getTranslation("ready", "Ready");
    fusionStartBtn.disabled = status.running;
    fusionStartBtn.style.display = status.running ? "none" : "block";
    fusionStopBtn.style.display = status.running ? "block" : "none";
    fusionRefreshBtn.disabled = status.running;
    fusionMoveFusedBtn.disabled = status.running;

    if (!status.running && fusionStatusTimer) {
      clearInterval(fusionStatusTimer);
      fusionStatusTimer = null;
    }

    const progress = status.progress || { current: 0, total: 0, current_file: "" };
    const stats = status.stats || { total: 0, success: 0, failed: 0 };

    if (progress.current_file && progress.current_file !== lastFusionMessage)
      lastFusionMessage = progress.current_file;

    fusionCurrentFile.textContent = progress.current_file || "";
    fusionStatTotal.textContent = stats.total;
    fusionStatSuccess.textContent = stats.success;
    fusionStatFailed.textContent = stats.failed;

    const pct = progress.total > 0 ? (progress.current / progress.total) * 100 : 0;
    fusionProgressFill.style.width = `${Math.min(pct, 100)}%`;
    fusionProgressPercent.textContent = `${pct.toFixed(1)}%`;
  } catch (e) {
    console.error(e);
  }
}

async function refreshFusionZips() {
  try {
    const { zips } = await apiRequest("/api/fusion/zips");
    fusionZipsCount.textContent = zips.length;

    if (!fusionZipsList) return console.warn("Element fusion-zips-list not found");

    if (zips.length === 0) {
      fusionZipsList.innerHTML = `<p class="empty-message">${getTranslation("emptyZIPsMessage", "No ZIPs available")}</p>`;
      return;
    }

    fusionZipsList.innerHTML = "";
    zips.forEach(zip => {
      let badge;
      if (!zip.has_pairs) badge = `<span class="zip-status-badge no-pairs">${getTranslation("noPairs", "No pairs")}</span>`;
      else if (zip.is_fused) badge = `<span class="zip-status-badge fused">${getTranslation("fused", "Fused")}</span>`;
      else badge = `<span class="zip-status-badge pending">${getTranslation("pending", "Pending")}</span>`;

      const zipItem = document.createElement("div");
      zipItem.className = "zip-item";
      zipItem.innerHTML = `
        <div class="zip-info">
          <div class="zip-name">${zip.name}</div>
          <div class="zip-details">${zip.has_pairs ? getTranslation("pairFound", "Pair found") : getTranslation("noPairsMainOverlay", "No main/overlay pairs")}</div>
        </div>
        <div class="zip-status">${badge}</div>
      `;
      fusionZipsList.appendChild(zipItem);
    });
  } catch (e) {
    console.error(e);
    if (fusionZipsList)
      fusionZipsList.innerHTML = `<p class="empty-message">${getTranslation("errorLoadingZIPs", "Error loading ZIPs")}</p>`;
  }
}

async function onFusionStart() {
  try {
    fusionStartBtn.disabled = true;
    await apiRequest("/api/fusion/fuse", { method: "POST", body: JSON.stringify({}) });

    if (!fusionStatusTimer) {
      fusionStatusTimer = setInterval(() => {
        refreshFusionStatus();
        refreshFusionZips();
        refreshFusedFiles();
      }, 800);
    }

    await refreshFusionStatus();
    await refreshFusionZips();
  } catch (e) {
    console.error(e);
    alert(getTranslation("errorStartingFusion", "Unable to start fusion"));
    fusionStartBtn.disabled = false;
  }
}

async function onFusionStop() {
  try {
    fusionStopBtn.disabled = true;
    await apiRequest("/api/fusion/stop", { method: "POST", body: JSON.stringify({}) });
    await refreshFusionStatus();
  } catch (e) {
    console.error(e);
    alert(getTranslation("errorStoppingFusion", "Error stopping fusion"));
  }
}

async function refreshFusedFiles() {
  try {
    const res = await fetch("/api/fusion/fused-files");
    if (!res.ok) {
      if (fusionFusedList)
        fusionFusedList.innerHTML = `<p class="empty-state">${getTranslation("errorLoadingFused", "Error loading fused files")}</p>`;
      return;
    }

    const { files = [] } = await res.json();
    if (!fusionFusedList) return console.warn("Element fusion-fused-list not found");

    if (files.length === 0) {
      fusionFusedList.innerHTML = `<div class="empty-state" data-i18n="noFusedFiles">No fused files</div>`;
      fusionMoveFusedBtn.disabled = true;
      return;
    }

    fusionMoveFusedBtn.disabled = false;
    fusionFusedList.innerHTML = "";
    files.forEach(file => {
      const fileItem = document.createElement("div");
      fileItem.className = "zip-item";
      fileItem.innerHTML = `
        <div class="zip-info">
          <div class="zip-name">${file.name}</div>
          <div class="zip-details">${(file.size / (1024 * 1024)).toFixed(2)} MB</div>
        </div>
        <div class="zip-status"><span class="zip-status-badge fused">${getTranslation("fusedBadge", "Fused")}</span></div>
      `;
      fusionFusedList.appendChild(fileItem);
    });
  } catch (e) {
    console.error(e);
    if (fusionFusedList)
      fusionFusedList.innerHTML = `<p class="empty-state">${getTranslation("errorLoadingFused", "Error loading fused files")}</p>`;
  }
}

async function onFusionMove() {
  if (!confirm(getTranslation("confirmMoveFused", "Move all fused media to memories_storage?"))) return;
  try {
    fusionMoveFusedBtn.disabled = true;
    const res = await apiRequest("/api/fusion/move", { method: "POST", body: JSON.stringify({}) });
    if (!res.ok) {
      alert(res.error || getTranslation("errorMovingFused", "Error moving fused files"));
      return;
    }
    await refreshFusedFiles();
  } catch (e) {
    console.error(e);
    alert(getTranslation("errorMovingFused", "Error moving fused files"));
  } finally {
    fusionMoveFusedBtn.disabled = false;
  }
}

function initializeModals() {
  deadLinksModal = document.getElementById("dead-links-modal");
  deadLinksCloseBtn = document.getElementById("dead-links-close");
  deadLinksChangeFileBtn = document.getElementById("dead-links-change-file");
  infoModal = document.getElementById("info-modal");
  closeWarningModal = document.getElementById("close-warning-modal");
  closeWarningBtn = document.getElementById("close-warning-btn");
  closeWarningOkBtn = document.getElementById("close-warning-ok");
  storageInfoModal = document.getElementById("storage-info-modal");

  if (!deadLinksModal || !infoModal) return console.warn("Modals not loaded yet");

  if (infoBtn) infoBtn.addEventListener("click", () => infoModal.style.display = "block");

  infoModal.querySelector(".modal-close")?.addEventListener("click", () => infoModal.style.display = "none");

  storageInfoBtn?.addEventListener("click", () => storageInfoModal.style.display = "block");
  storageInfoModal.querySelector(".modal-close")?.addEventListener("click", () => storageInfoModal.style.display = "none");

  const closeDeadLinks = () => {
    deadLinksModal.style.display = "none";
    setDeadLinksModalDismissed(true);
  };
  deadLinksCloseBtn?.addEventListener("click", closeDeadLinks);
  deadLinksModal.querySelector(".modal-close")?.addEventListener("click", closeDeadLinks);
  deadLinksChangeFileBtn?.addEventListener("click", () => {
    deadLinksModal.style.display = "none";
    window.location.href = "settings.html#import-memories";
  });

  closeWarningBtn?.addEventListener("click", () => closeWarningModal.style.display = "none");
  closeWarningOkBtn?.addEventListener("click", () => closeWarningModal.style.display = "none");

  window.addEventListener("click", e => {
    [infoModal, deadLinksModal, closeWarningModal, storageInfoModal].forEach(modal => {
      if (e.target === modal) modal.style.display = "none";
    });
  });

  applyTranslationsToNewContent();
}

document.addEventListener("modalsLoaded", initializeModals);

startBtn.addEventListener("click", onStart);
stopBtn.addEventListener("click", onStop);
openFolderBtn.addEventListener("click", async () => {
  try {
    const res = await apiRequest("/api/open-output-folder");
    if (!res.ok) alert(res.error || getTranslation("errorOpeningFolder", "Error opening folder"));
  } catch (e) {
    console.error(e);
    alert(getTranslation("errorOpeningFolder", "Error opening folder"));
  }
});
fusionStartBtn.addEventListener("click", onFusionStart);
fusionStopBtn.addEventListener("click", onFusionStop);
fusionRefreshBtn.addEventListener("click", async () => { await refreshFusionZips(); await refreshFusionStatus(); });
fusionMoveFusedBtn.addEventListener("click", onFusionMove);
fusionRefreshFusedBtn.addEventListener("click", refreshFusedFiles);

window.showCloseWarning = () => closeWarningModal.style.display = "block";

document.addEventListener("DOMContentLoaded", async () => {
  await loadTranslations();
  await loadStoragePath();

  document.getElementById("feedback-button")?.addEventListener("click", e => {
    e.preventDefault();
    window.open("https://github.com", "_blank");
  });

  document.getElementById("settings-button")?.addEventListener("click", () => {
    window.location.href = "settings.html";
  });

  document.getElementById("language-select")?.addEventListener("change", async e => {
    currentLanguage = e.target.value;
    await saveLanguagePreference();
    applyTranslations();
    applyTranslationsToNewContent();
    await loadStoragePath();
    await refreshFusionZips();
    await refreshFusedFiles();
    await refreshStatus();
  });

  refreshStatus();
  statusTimer = setInterval(refreshStatus, 2000);

  await refreshFusionZips();
  await refreshFusedFiles();

  checkCloseAttempt();
  closeAttemptTimer = setInterval(checkCloseAttempt, 2000);

  window.addEventListener("focus", () => windowHasFocus = true);
  window.addEventListener("blur", () => windowHasFocus = false);
});