/**
 * UI Controller & Event Handlers (v4.5 - Enhanced Fonts & Robust 3MF Download)
 * Gestisce:
 * 1. Switch dinamico tra generatore "Portachiavi" e "Targhetta da Tavolo" (Desk Sign).
 * 2. Dropdown Font Personalizzato con Anteprima Tipografica Reale (Google Fonts + System + Upload).
 * 3. Palette rapida a 4 slot per Snapmaker U1 con aggiornamento Three.js a 0 ms.
 * 4. Chiamate API protette con cold-start feedback (Render free tier) e toast notifications.
 * 5. Generazione e download 3MF nativo multi-volume per Snapmaker Orca con gestione errori.
 */

// ==============================================================================
// 0. CATALOGO FONT PRECARICATO (Disponibilità immediata a latenza zero)
// ==============================================================================
const DEFAULT_CURATED_FONTS = [
  { id: "Anton", name: "Anton", desc: "Massiccio Display Bold", category: "display", family: "'Anton', sans-serif" },
  { id: "Bebas Neue", name: "Bebas Neue", desc: "Alto e Condensato", category: "display", family: "'Bebas Neue', sans-serif" },
  { id: "Pacifico", name: "Pacifico", desc: "Corsivo Connesso Elegante", category: "script", family: "'Pacifico', cursive" },
  { id: "Lobster", name: "Lobster", desc: "Vintage Bold Script", category: "script", family: "'Lobster', cursive" },
  { id: "Bungee", name: "Bungee", desc: "Spesso e Dimensional", category: "display", family: "'Bungee', cursive" },
  { id: "Righteous", name: "Righteous", desc: "Retro Futuristico Techno", category: "display", family: "'Righteous', cursive" },
  { id: "Bangers", name: "Bangers", desc: "Fumetto Comic Bold", category: "display", family: "'Bangers', cursive" },
  { id: "Permanent Marker", name: "Permanent Marker", desc: "Tratto Pennarello Autentico", category: "script", family: "'Permanent Marker', cursive" },
  { id: "Orbitron", name: "Orbitron", desc: "Futuristico Sci-Fi Mecha", category: "display", family: "'Orbitron', sans-serif" },
  { id: "Montserrat", name: "Montserrat", desc: "Geometrico Moderno Bold", category: "sans-serif", family: "'Montserrat', sans-serif" },
  { id: "Poppins", name: "Poppins", desc: "Geometrico Pulito e Morbido", category: "sans-serif", family: "'Poppins', sans-serif" },
  { id: "Roboto", name: "Roboto", desc: "Standard Tecnico Bilanciato", category: "sans-serif", family: "'Roboto', sans-serif" },
  { id: "Oswald", name: "Oswald", desc: "Display Dinamico", category: "display", family: "'Oswald', sans-serif" },
  { id: "Playfair Display", name: "Playfair Display", desc: "Serif Elegante Tradizionale", category: "serif", family: "'Playfair Display', serif" },
  { id: "Cinzel", name: "Cinzel", desc: "Classico Romano Scolpito", category: "serif", family: "'Cinzel', serif" },
  { id: "Ubuntu", name: "Ubuntu", desc: "Humanist Moderno", category: "sans-serif", family: "'Ubuntu', sans-serif" },
  { id: "Arial", name: "Arial", desc: "Sans-Serif Standard", category: "sans-serif", family: "Arial, sans-serif" },
  { id: "Arial Black", name: "Arial Black", desc: "Ultra-Spesso Massiccio", category: "sans-serif", family: "'Arial Black', sans-serif" },
  { id: "Impact", name: "Impact", desc: "Massiccio Classico", category: "display", family: "Impact, sans-serif" },
  { id: "Segoe UI", name: "Segoe UI", desc: "Geometrico Interfaccia", category: "sans-serif", family: "'Segoe UI', sans-serif" },
  { id: "Segoe Script", name: "Segoe Script", desc: "Corsivo Continuo Saldato", category: "script", family: "'Segoe Script', cursive" },
  { id: "Georgia", name: "Georgia", desc: "Serif Classico", category: "serif", family: "Georgia, serif" },
  { id: "Consolas", name: "Consolas", desc: "Monospazio Tecnico", category: "monospace", family: "Consolas, monospace" },
];

let globalFontsList = [...DEFAULT_CURATED_FONTS];

// ==============================================================================
// 0.1 TOAST NOTIFICATIONS MANAGER
// ==============================================================================
const ToastManager = {
  container: null,
  init() {
    this.container = document.getElementById("studioToastContainer");
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.id = "studioToastContainer";
      this.container.className = "studio-toast-container";
      document.body.appendChild(this.container);
    }
  },
  show({ type = "info", title, message, duration = 5000 }) {
    if (!this.container) this.init();

    const toast = document.createElement("div");
    toast.className = `studio-toast ${type}`;

    let icon = "ℹ️";
    if (type === "warning") icon = "⏳";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "❌";

    toast.innerHTML = `
      <span class="studio-toast-icon">${icon}</span>
      <div class="studio-toast-body">
        ${title ? `<div class="studio-toast-title">${title}</div>` : ""}
        <div class="studio-toast-message">${message}</div>
      </div>
      <button type="button" class="studio-toast-close" title="Chiudi">✕</button>
    `;

    const closeBtn = toast.querySelector(".studio-toast-close");
    closeBtn.addEventListener("click", () => this.dismiss(toast));

    this.container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => this.dismiss(toast), duration);
    }

    return toast;
  },
  dismiss(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add("fade-out");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 200);
  },
};

// ==============================================================================
// 0.2 CUSTOM FONT DROPDOWN COMPONENT (Anteprima reale e ricerca)
// ==============================================================================
class CustomFontDropdown {
  constructor(selectElem, onFontChange) {
    this.selectElem = selectElem;
    this.onFontChange = onFontChange;
    this.currentCategory = "all";
    this.searchTerm = "";

    this.init();
  }

  init() {
    this.selectElem.style.display = "none";

    this.wrapper = document.createElement("div");
    this.wrapper.className = "custom-font-dropdown";

    this.wrapper.innerHTML = `
      <div class="custom-font-trigger" tabindex="0">
        <div class="custom-font-trigger-info">
          <span class="custom-font-current-name">Arial</span>
          <span class="custom-font-current-badge">Sans</span>
        </div>
        <span class="custom-font-arrow">▼</span>
      </div>
      <div class="custom-font-menu">
        <div class="custom-font-search-box">
          <input type="text" class="custom-font-search-input" placeholder="🔍 Cerca font per nome o stile...">
        </div>
        <div class="custom-font-filter-chips">
          <button type="button" class="custom-font-chip active" data-cat="all">Tutti</button>
          <button type="button" class="custom-font-chip" data-cat="display">Display</button>
          <button type="button" class="custom-font-chip" data-cat="script">Corsivo</button>
          <button type="button" class="custom-font-chip" data-cat="sans-serif">Sans</button>
          <button type="button" class="custom-font-chip" data-cat="serif">Serif</button>
          <button type="button" class="custom-font-chip" data-cat="custom">Caricati</button>
        </div>
        <div class="custom-font-options-list"></div>
      </div>
    `;

    this.selectElem.parentNode.insertBefore(this.wrapper, this.selectElem.nextSibling);

    this.trigger = this.wrapper.querySelector(".custom-font-trigger");
    this.menu = this.wrapper.querySelector(".custom-font-menu");
    this.currentName = this.wrapper.querySelector(".custom-font-current-name");
    this.currentBadge = this.wrapper.querySelector(".custom-font-current-badge");
    this.searchInput = this.wrapper.querySelector(".custom-font-search-input");
    this.optionsList = this.wrapper.querySelector(".custom-font-options-list");
    this.chips = this.wrapper.querySelectorAll(".custom-font-chip");

    // Eventi
    this.trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleMenu();
    });

    this.trigger.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        this.toggleMenu();
      }
    });

    this.searchInput.addEventListener("input", (e) => {
      this.searchTerm = e.target.value.toLowerCase().trim();
      this.renderOptions();
    });

    this.searchInput.addEventListener("click", (e) => e.stopPropagation());

    this.chips.forEach((chip) => {
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        this.chips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        this.currentCategory = chip.dataset.cat;
        this.renderOptions();
      });
    });

    document.addEventListener("click", (e) => {
      if (!this.wrapper.contains(e.target)) {
        this.closeMenu();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.closeMenu();
    });

    this.updateFromSelect();
  }

  toggleMenu() {
    const isOpen = this.wrapper.classList.contains("open");
    // Chiudi tutti gli altri dropdown aperti
    document.querySelectorAll(".custom-font-dropdown.open").forEach((d) => {
      if (d !== this.wrapper) d.classList.remove("open");
    });

    if (isOpen) {
      this.closeMenu();
    } else {
      this.wrapper.classList.add("open");
      this.renderOptions();
      setTimeout(() => this.searchInput.focus(), 50);
    }
  }

  closeMenu() {
    this.wrapper.classList.remove("open");
  }

  updateFromSelect() {
    const selectedVal = this.selectElem.value || "Arial";
    const font = globalFontsList.find((f) => f.id === selectedVal) || {
      id: selectedVal,
      name: selectedVal,
      category: "sans-serif",
      family: selectedVal,
    };

    this.currentName.textContent = font.name || font.id;
    this.currentName.style.fontFamily = font.family || font.id;
    this.currentBadge.textContent = font.category || "Font";
  }

  renderOptions() {
    this.optionsList.innerHTML = "";
    const selectedVal = this.selectElem.value;

    const filtered = globalFontsList.filter((f) => {
      const matchCat = this.currentCategory === "all" || f.category === this.currentCategory;
      const matchSearch = !this.searchTerm ||
        f.id.toLowerCase().includes(this.searchTerm) ||
        (f.name && f.name.toLowerCase().includes(this.searchTerm)) ||
        (f.desc && f.desc.toLowerCase().includes(this.searchTerm));
      return matchCat && matchSearch;
    });

    if (filtered.length === 0) {
      this.optionsList.innerHTML = `<div style="padding: 12px; color: var(--text-dim); text-align: center; font-size: 12px;">Nessun carattere trovato.</div>`;
      return;
    }

    filtered.forEach((font) => {
      const isSelected = font.id === selectedVal;
      const item = document.createElement("div");
      item.className = `custom-font-option-item ${isSelected ? "selected" : ""}`;
      item.dataset.value = font.id;

      item.innerHTML = `
        <div class="custom-font-item-main">
          <div class="custom-font-item-name" style="font-family: ${font.family || font.id};">
            ${font.name || font.id}
          </div>
          <div class="custom-font-item-sample" style="font-family: ${font.family || font.id};">
            ${font.desc || "Anteprima Testo 3D • Snapmaker U1"}
          </div>
        </div>
        <div class="custom-font-item-meta">
          <span class="custom-font-item-badge">${font.category || "Font"}</span>
          ${isSelected ? `<span class="custom-font-check">✓</span>` : ""}
        </div>
      `;

      item.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectFont(font.id);
      });

      this.optionsList.appendChild(item);
    });
  }

  selectFont(fontId) {
    this.selectElem.value = fontId;
    this.updateFromSelect();
    this.closeMenu();

    // Trigger evento change sul select originario per retrocompatibilità
    const event = new Event("change", { bubbles: true });
    this.selectElem.dispatchEvent(event);

    if (this.onFontChange) this.onFontChange(fontId);
  }
}

// ==============================================================================
// 1. INIZIALIZZAZIONE APPLICAZIONE
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
  ToastManager.init();

  const viewer = new ModelViewer("canvas-container");
  let debounceTimer = null;
  let isRequestPending = false;
  let currentProduct = "keychain"; // "keychain" | "desk_sign"

  function safeAddListener(el, evt, handler) {
    if (el) el.addEventListener(evt, handler);
  }

  // Preset Palettes U1
  const PALETTE_PRESETS = {
    snapmaker: ["#161616", "#ffffff", "#e31b23", "#ffd400"],
    sunset: ["#1c120c", "#ff7b00", "#ffd700", "#e63946"],
    cyberpunk: ["#0e111a", "#00f5d4", "#f72585", "#7b2cbf"],
    forest: ["#18231c", "#84a98c", "#52796f", "#cad2c5"],
  };

  // --- Elementi Switcher Prodotto ---
  const tabKeychain = document.getElementById("tabKeychain");
  const tabDeskSign = document.getElementById("tabDeskSign");

  // --- Elementi Portachiavi (Keychain) ---
  const textInput = document.getElementById("textInput");
  const fontSelect = document.getElementById("fontSelect");
  const btnUploadFont = document.getElementById("btnUploadFont");
  const fontFileInput = document.getElementById("fontFileInput");
  const fontUploadStatus = document.getElementById("fontUploadStatus");

  const fontSizeInput = document.getElementById("fontSizeInput");
  const fontSizeVal = document.getElementById("fontSizeVal");
  const letterSpacingInput = document.getElementById("letterSpacingInput");
  const letterSpacingVal = document.getElementById("letterSpacingVal");

  const iconOptionsWrap = document.getElementById("iconOptionsWrap");
  const extruderIconSelect = document.getElementById("extruderIconSelect");

  const baseThicknessInput = document.getElementById("baseThicknessInput");
  const baseThicknessVal = document.getElementById("baseThicknessVal");
  const cornerRadiusInput = document.getElementById("cornerRadiusInput");
  const cornerRadiusVal = document.getElementById("cornerRadiusVal");
  const paddingXInput = document.getElementById("paddingXInput");
  const paddingXVal = document.getElementById("paddingXVal");
  const paddingYInput = document.getElementById("paddingYInput");
  const paddingYVal = document.getElementById("paddingYVal");

  const textThicknessInput = document.getElementById("textThicknessInput");
  const textThicknessVal = document.getElementById("textThicknessVal");

  const holeToggle = document.getElementById("holeToggle");
  const holeDiameterInput = document.getElementById("holeDiameterInput");
  const holeDiameterVal = document.getElementById("holeDiameterVal");
  const holeOptionsWrap = document.getElementById("holeOptionsWrap");
  const extruderTextSelect = document.getElementById("extruderTextSelect");

  // --- Elementi Targhetta da Tavolo (Desk Sign) ---
  const dsWedgeAngleGroup = document.getElementById("dsWedgeAngleGroup");
  const dsWedgeAngleInput = document.getElementById("dsWedgeAngleInput");
  const dsWedgeAngleVal = document.getElementById("dsWedgeAngleVal");
  const dsBaseThicknessInput = document.getElementById("dsBaseThicknessInput");
  const dsBaseThicknessVal = document.getElementById("dsBaseThicknessVal");
  const dsPaddingXInput = document.getElementById("dsPaddingXInput");
  const dsPaddingXVal = document.getElementById("dsPaddingXVal");
  const dsPaddingYInput = document.getElementById("dsPaddingYInput");
  const dsPaddingYVal = document.getElementById("dsPaddingYVal");

  const dsText1Input = document.getElementById("dsText1Input");
  const dsFont1Select = document.getElementById("dsFont1Select");
  const dsFontSize1Input = document.getElementById("dsFontSize1Input");
  const dsFontSize1Val = document.getElementById("dsFontSize1Val");
  const dsThickness1Input = document.getElementById("dsThickness1Input");
  const dsThickness1Val = document.getElementById("dsThickness1Val");
  const dsExtruderLine1Select = document.getElementById("dsExtruderLine1Select");

  const dsLine2Toggle = document.getElementById("dsLine2Toggle");
  const dsLine2Wrap = document.getElementById("dsLine2Wrap");
  const dsText2Input = document.getElementById("dsText2Input");
  const dsFont2Select = document.getElementById("dsFont2Select");
  const dsFontSize2Input = document.getElementById("dsFontSize2Input");
  const dsFontSize2Val = document.getElementById("dsFontSize2Val");
  const dsLineSpacingInput = document.getElementById("dsLineSpacingInput");
  const dsLineSpacingVal = document.getElementById("dsLineSpacingVal");
  const dsThickness2Input = document.getElementById("dsThickness2Input");
  const dsThickness2Val = document.getElementById("dsThickness2Val");
  const dsExtruderLine2Select = document.getElementById("dsExtruderLine2Select");

  const dsBorderToggle = document.getElementById("dsBorderToggle");
  const dsBorderWrap = document.getElementById("dsBorderWrap");
  const dsBorderWidthInput = document.getElementById("dsBorderWidthInput");
  const dsBorderWidthVal = document.getElementById("dsBorderWidthVal");
  const dsBorderThicknessInput = document.getElementById("dsBorderThicknessInput");
  const dsBorderThicknessVal = document.getElementById("dsBorderThicknessVal");
  const dsCornerRadiusInput = document.getElementById("dsCornerRadiusInput");
  const dsCornerRadiusVal = document.getElementById("dsCornerRadiusVal");
  const dsExtruderBorderSelect = document.getElementById("dsExtruderBorderSelect");

  // --- Elementi Comuni: Palette & Toolbar ---
  const extruderBaseSelect = document.getElementById("extruderBaseSelect");
  const colorT0 = document.getElementById("colorT0");
  const colorT1 = document.getElementById("colorT1");
  const colorT2 = document.getElementById("colorT2");
  const colorT3 = document.getElementById("colorT3");

  const btnGenerate = document.getElementById("btnGenerate");
  const dimWidth = document.getElementById("dimWidth");
  const dimHeight = document.getElementById("dimHeight");
  const dimDepth = document.getElementById("dimDepth");
  const statusPill = document.getElementById("statusPill");
  const statusDot = statusPill ? statusPill.querySelector(".status-dot") : null;
  const statusText = document.getElementById("statusText");

  // ==========================================
  // 1.1 GESTIONE SELETTORE PRODOTTO (TABS)
  // ==========================================
  function setProduct(product) {
    currentProduct = product;
    if (product === "desk_sign") {
      if (tabDeskSign) tabDeskSign.classList.add("active");
      if (tabKeychain) tabKeychain.classList.remove("active");
      document.body.classList.add("mode-desksign");
    } else {
      if (tabKeychain) tabKeychain.classList.add("active");
      if (tabDeskSign) tabDeskSign.classList.remove("active");
      document.body.classList.remove("mode-desksign");
    }
    triggerPreview(true);
  }

  safeAddListener(tabKeychain, "click", () => setProduct("keychain"));
  safeAddListener(tabDeskSign, "click", () => setProduct("desk_sign"));

  // ==============================================================================
  // 1.2 CONFIGURAZIONE DINAMICA API_BASE_URL (Supporto Localhost, Vercel & Render)
  // ==============================================================================
  const btnApiSettings = document.getElementById("btnApiSettings");
  const apiStatusDot = document.getElementById("apiStatusDot");
  const apiStatusLabel = document.getElementById("apiStatusLabel");
  const DEFAULT_PRODUCTION_API = "https://snapmaker-u1-backend.onrender.com";

  function determineApiBaseUrl() {
    const metaTag = document.querySelector('meta[name="api-base-url"]');
    if (metaTag && metaTag.content && metaTag.content.trim() !== "") {
      return metaTag.content.trim().replace(/\/$/, "");
    }
    if (window.API_BASE_URL) {
      return window.API_BASE_URL.replace(/\/$/, "");
    }
    const saved = localStorage.getItem("snapmaker_u1_api_url");
    if (saved && saved.trim() !== "") {
      return saved.trim().replace(/\/$/, "");
    }
    const isLocal = window.location.hostname === "localhost" ||
                    window.location.hostname === "127.0.0.1";
    if (isLocal) {
      if (window.location.port !== "8000" && window.location.port !== "") {
        return "http://localhost:8000";
      }
      return "";
    }
    return DEFAULT_PRODUCTION_API;
  }

  let API_BASE_URL = determineApiBaseUrl();

  async function checkApiHealth() {
    if (apiStatusLabel) apiStatusLabel.textContent = "API: Verifica...";
    if (apiStatusDot) apiStatusDot.className = "api-status-dot";

    try {
      const url = `${API_BASE_URL}/api/health`;
      const res = await fetch(url, { method: "GET" });
      if (res.ok) {
        if (apiStatusDot) apiStatusDot.className = "api-status-dot online";
        let displayHost = "Localhost:8000";
        if (API_BASE_URL) {
          try {
            displayHost = new URL(API_BASE_URL).hostname;
          } catch {
            displayHost = API_BASE_URL;
          }
        }
        if (apiStatusLabel) apiStatusLabel.textContent = `API: Online (${displayHost})`;
      } else {
        throw new Error("HTTP " + res.status);
      }
    } catch (err) {
      if (apiStatusDot) apiStatusDot.className = "api-status-dot offline";
      if (apiStatusLabel) apiStatusLabel.textContent = "API: Offline / Standby";
    }
  }

  safeAddListener(btnApiSettings, "click", () => {
    const current = API_BASE_URL || "(Relativo / Localhost:8000)";
    const input = prompt(
      "Configura l'endpoint Backend API per Snapmaker U1:\n" +
      "- In locale: http://localhost:8000\n" +
      "- Su Render/Railway: https://tuo-servizio.onrender.com\n\n" +
      "URL attuale: " + current,
      API_BASE_URL
    );
    if (input !== null) {
      const cleaned = input.trim().replace(/\/$/, "");
      if (cleaned) {
        localStorage.setItem("snapmaker_u1_api_url", cleaned);
        API_BASE_URL = cleaned;
      } else {
        localStorage.removeItem("snapmaker_u1_api_url");
        API_BASE_URL = determineApiBaseUrl();
      }
      checkApiHealth();
      loadFonts();
    }
  });

  checkApiHealth();

  // ==========================================
  // 2. INIZIALIZZAZIONE CUSTOM FONT DROPDOWNS
  // ==========================================
  function populateSelectOptions(selectElem, fonts, selectedId) {
    if (!selectElem) return;
    const prevVal = selectElem.value || selectedId || "Arial";
    selectElem.innerHTML = "";
    fonts.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = f.name;
      if (f.path) opt.dataset.path = f.path;
      if (f.id === prevVal) opt.selected = true;
      selectElem.appendChild(opt);
    });
  }

  // Popola immediatamente con i font di default
  populateSelectOptions(fontSelect, globalFontsList, "Anton");
  populateSelectOptions(dsFont1Select, globalFontsList, "Anton");
  populateSelectOptions(dsFont2Select, globalFontsList, "Montserrat");

  // Inizializza i 3 custom dropdown
  const dropdownKeychain = fontSelect ? new CustomFontDropdown(fontSelect, () => triggerPreview(true)) : null;
  const dropdownDs1 = dsFont1Select ? new CustomFontDropdown(dsFont1Select, () => triggerPreview(true)) : null;
  const dropdownDs2 = dsFont2Select ? new CustomFontDropdown(dsFont2Select, () => triggerPreview(true)) : null;

  function refreshAllDropdowns() {
    if (dropdownKeychain) {
      dropdownKeychain.updateFromSelect();
      dropdownKeychain.renderOptions();
    }
    if (dropdownDs1) {
      dropdownDs1.updateFromSelect();
      dropdownDs1.renderOptions();
    }
    if (dropdownDs2) {
      dropdownDs2.updateFromSelect();
      dropdownDs2.renderOptions();
    }
  }

  function loadFonts(selectedId = null) {
    fetch(`${API_BASE_URL}/api/fonts`)
      .then((res) => {
        if (!res.ok) throw new Error("Status " + res.status);
        return res.json();
      })
      .then((fonts) => {
        if (Array.isArray(fonts) && fonts.length > 0) {
          globalFontsList = fonts;
          populateSelectOptions(fontSelect, globalFontsList, selectedId || fontSelect?.value || "Anton");
          populateSelectOptions(dsFont1Select, globalFontsList, dsFont1Select?.value || "Anton");
          populateSelectOptions(dsFont2Select, globalFontsList, dsFont2Select?.value || "Montserrat");
          refreshAllDropdowns();
          triggerPreview(true);
        }
      })
      .catch(() => {
        // Fallback tranquillo sui font integrati
        refreshAllDropdowns();
        triggerPreview(true);
      });
  }

  // Caricamento asincrono font dal backend
  loadFonts();

  // Upload Font .ttf / .otf
  safeAddListener(btnUploadFont, "click", () => {
    if (fontFileInput) fontFileInput.click();
  });

  safeAddListener(fontFileInput, "change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    if (fontUploadStatus) {
      fontUploadStatus.style.display = "block";
      fontUploadStatus.style.color = "#ffa502";
      fontUploadStatus.textContent = "Caricamento font in corso...";
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/fonts/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Errore upload font");
      }

      const data = await res.json();
      if (fontUploadStatus) {
        fontUploadStatus.style.color = "#2ed573";
        fontUploadStatus.textContent = `✓ Font ${file.name} caricato e pronto!`;
      }

      ToastManager.show({
        type: "success",
        title: "Font Caricato",
        message: `Il font "${file.name}" è stato aggiunto con successo.`,
      });

      loadFonts(data.font.id);
    } catch (err) {
      if (fontUploadStatus) {
        fontUploadStatus.style.color = "#ff4757";
        fontUploadStatus.textContent = `Errore: ${err.message}`;
      }
      ToastManager.show({
        type: "error",
        title: "Errore Caricamento Font",
        message: err.message,
      });
    }
  });

  // ==========================================
  // 3. PRESET PALETTE & COLORI
  // ==========================================
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const presetKey = btn.dataset.preset;
      const colors = PALETTE_PRESETS[presetKey];
      if (colors) {
        if (colorT0) colorT0.value = colors[0];
        if (colorT1) colorT1.value = colors[1];
        if (colorT2) colorT2.value = colors[2];
        if (colorT3) colorT3.value = colors[3];
        onPaletteChange();
      }
    });
  });

  function onPaletteChange() {
    const c0 = colorT0 ? colorT0.value : "#161616";
    const c1 = colorT1 ? colorT1.value : "#ffffff";
    const c2 = colorT2 ? colorT2.value : "#e31b23";
    const c3 = colorT3 ? colorT3.value : "#ffd400";
    viewer.updateColors([c0, c1, c2, c3]);
  }

  safeAddListener(colorT0, "input", onPaletteChange);
  safeAddListener(colorT1, "input", onPaletteChange);
  safeAddListener(colorT2, "input", onPaletteChange);
  safeAddListener(colorT3, "input", onPaletteChange);

  // ==========================================
  // 4. EVENT LISTENERS DINAMICI
  // ==========================================
  // Portachiavi Icone
  document.querySelectorAll('input[name="iconName"]').forEach((r) => {
    r.addEventListener("change", (e) => {
      if (iconOptionsWrap) iconOptionsWrap.style.display = e.target.value !== "none" ? "flex" : "none";
      triggerPreview(true);
    });
  });

  document.querySelectorAll('input[name="iconPos"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });

  safeAddListener(extruderIconSelect, "change", () => triggerPreview(true));

  // Portachiavi Slider
  safeAddListener(textInput, "input", () => triggerPreview(false));
  safeAddListener(fontSelect, "change", () => triggerPreview(true));

  safeAddListener(fontSizeInput, "input", (e) => {
    if (fontSizeVal) fontSizeVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(letterSpacingInput, "input", (e) => {
    if (letterSpacingVal) letterSpacingVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(baseThicknessInput, "input", (e) => {
    if (baseThicknessVal) baseThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(cornerRadiusInput, "input", (e) => {
    if (cornerRadiusVal) cornerRadiusVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(paddingXInput, "input", (e) => {
    if (paddingXVal) paddingXVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(paddingYInput, "input", (e) => {
    if (paddingYVal) paddingYVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(textThicknessInput, "input", (e) => {
    if (textThicknessVal) textThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(holeDiameterInput, "input", (e) => {
    if (holeDiameterVal) holeDiameterVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(holeToggle, "change", (e) => {
    if (holeOptionsWrap) holeOptionsWrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });

  document.querySelectorAll('input[name="baseStyle"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  document.querySelectorAll('input[name="textMode"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  document.querySelectorAll('input[name="holePos"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  safeAddListener(extruderBaseSelect, "change", () => triggerPreview(true));
  safeAddListener(extruderTextSelect, "change", () => triggerPreview(true));

  // --- Targhetta da Tavolo (Desk Sign) Event Listeners ---
  document.querySelectorAll('input[name="dsBaseMode"]').forEach((r) => {
    r.addEventListener("change", (e) => {
      if (dsWedgeAngleGroup) dsWedgeAngleGroup.style.display = e.target.value === "wedge" ? "flex" : "none";
      triggerPreview(true);
    });
  });

  safeAddListener(dsWedgeAngleInput, "input", (e) => {
    if (dsWedgeAngleVal) dsWedgeAngleVal.textContent = `${e.target.value}°`;
    triggerPreview(false);
  });
  safeAddListener(dsBaseThicknessInput, "input", (e) => {
    if (dsBaseThicknessVal) dsBaseThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsPaddingXInput, "input", (e) => {
    if (dsPaddingXVal) dsPaddingXVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsPaddingYInput, "input", (e) => {
    if (dsPaddingYVal) dsPaddingYVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });

  safeAddListener(dsText1Input, "input", () => triggerPreview(false));
  safeAddListener(dsFont1Select, "change", () => triggerPreview(true));
  safeAddListener(dsFontSize1Input, "input", (e) => {
    if (dsFontSize1Val) dsFontSize1Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsThickness1Input, "input", (e) => {
    if (dsThickness1Val) dsThickness1Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsExtruderLine1Select, "change", () => triggerPreview(true));

  safeAddListener(dsLine2Toggle, "change", (e) => {
    if (dsLine2Wrap) dsLine2Wrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });
  safeAddListener(dsText2Input, "input", () => triggerPreview(false));
  safeAddListener(dsFont2Select, "change", () => triggerPreview(true));
  safeAddListener(dsFontSize2Input, "input", (e) => {
    if (dsFontSize2Val) dsFontSize2Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsLineSpacingInput, "input", (e) => {
    if (dsLineSpacingVal) dsLineSpacingVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsThickness2Input, "input", (e) => {
    if (dsThickness2Val) dsThickness2Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsExtruderLine2Select, "change", () => triggerPreview(true));

  safeAddListener(dsBorderToggle, "change", (e) => {
    if (dsBorderWrap) dsBorderWrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });
  document.querySelectorAll('input[name="dsTextAlign"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  safeAddListener(dsBorderWidthInput, "input", (e) => {
    if (dsBorderWidthVal) dsBorderWidthVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsBorderThicknessInput, "input", (e) => {
    if (dsBorderThicknessVal) dsBorderThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsCornerRadiusInput, "input", (e) => {
    if (dsCornerRadiusVal) dsCornerRadiusVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsExtruderBorderSelect, "change", () => triggerPreview(true));

  // ==========================================
  // 5. RACCOLTA PARAMETRI PER L'API
  // ==========================================
  function getParams() {
    const palette = [
      colorT0 ? colorT0.value : "#161616",
      colorT1 ? colorT1.value : "#ffffff",
      colorT2 ? colorT2.value : "#e31b23",
      colorT3 ? colorT3.value : "#ffd400",
    ];
    const baseExtruder = extruderBaseSelect ? parseInt(extruderBaseSelect.value) : 0;

    if (currentProduct === "desk_sign") {
      const baseMode = document.querySelector('input[name="dsBaseMode"]:checked')?.value || "wedge";
      const textAlign = document.querySelector('input[name="dsTextAlign"]:checked')?.value || "center";
      const font1Opt = dsFont1Select ? dsFont1Select.options[dsFont1Select.selectedIndex] : null;
      const font2Opt = dsFont2Select ? dsFont2Select.options[dsFont2Select.selectedIndex] : null;

      return {
        generator: "desk_sign",
        base_mode: baseMode,
        wedge_angle: dsWedgeAngleInput ? parseFloat(dsWedgeAngleInput.value) : 45.0,
        base_thickness: dsBaseThicknessInput ? parseFloat(dsBaseThicknessInput.value) : 3.0,
        corner_radius: dsCornerRadiusInput ? parseFloat(dsCornerRadiusInput.value) : 3.0,
        padding_x: dsPaddingXInput ? parseFloat(dsPaddingXInput.value) : 8.0,
        padding_y: dsPaddingYInput ? parseFloat(dsPaddingYInput.value) : 6.0,
        line_spacing: dsLineSpacingInput ? parseFloat(dsLineSpacingInput.value) : 3.5,
        text_align: textAlign,
        text_line1: dsText1Input ? dsText1Input.value.trim() || "STUDIO U1" : "STUDIO U1",
        font_family_line1: dsFont1Select ? dsFont1Select.value || "Anton" : "Anton",
        font_path_line1: font1Opt?.dataset?.path || null,
        font_size_line1: dsFontSize1Input ? parseFloat(dsFontSize1Input.value) : 14.0,
        thickness_line1: dsThickness1Input ? parseFloat(dsThickness1Input.value) : 1.2,
        extruder_line1: dsExtruderLine1Select ? parseInt(dsExtruderLine1Select.value) : 1,
        line2_enabled: dsLine2Toggle ? dsLine2Toggle.checked : false,
        text_line2: dsText2Input ? dsText2Input.value.trim() : "",
        font_family_line2: dsFont2Select ? dsFont2Select.value || "Montserrat" : "Montserrat",
        font_path_line2: font2Opt?.dataset?.path || null,
        font_size_line2: dsFontSize2Input ? parseFloat(dsFontSize2Input.value) : 7.5,
        thickness_line2: dsThickness2Input ? parseFloat(dsThickness2Input.value) : 1.0,
        extruder_line2: dsExtruderLine2Select ? parseInt(dsExtruderLine2Select.value) : 2,
        border_enabled: dsBorderToggle ? dsBorderToggle.checked : true,
        border_width: dsBorderWidthInput ? parseFloat(dsBorderWidthInput.value) : 2.0,
        border_thickness: dsBorderThicknessInput ? parseFloat(dsBorderThicknessInput.value) : 1.0,
        extruder_border: dsExtruderBorderSelect ? parseInt(dsExtruderBorderSelect.value) : 3,
        extruder_base: baseExtruder,
        filament_colors: palette,
      };
    } else {
      // Template Keychain
      const baseStyle = document.querySelector('input[name="baseStyle"]:checked')?.value || "rectangle";
      const textMode = document.querySelector('input[name="textMode"]:checked')?.value || "embossed";
      const holePos = document.querySelector('input[name="holePos"]:checked')?.value || "left";
      const iconName = document.querySelector('input[name="iconName"]:checked')?.value || "none";
      const iconPos = document.querySelector('input[name="iconPos"]:checked')?.value || "left";
      const selectedFontOpt = fontSelect ? fontSelect.options[fontSelect.selectedIndex] : null;
      const textExtruder = extruderTextSelect ? parseInt(extruderTextSelect.value) : 1;
      let iconExtruder = extruderIconSelect ? parseInt(extruderIconSelect.value) : -1;
      if (iconExtruder === -1) iconExtruder = textExtruder;

      return {
        generator: "keychain",
        text: textInput ? textInput.value.trim() || "NOME" : "NOME",
        font_family: fontSelect ? fontSelect.value || "Anton" : "Anton",
        font_path: selectedFontOpt?.dataset?.path || null,
        font_size: fontSizeInput ? parseFloat(fontSizeInput.value) : 14.0,
        letter_spacing: letterSpacingInput ? parseFloat(letterSpacingInput.value) : 0.0,
        base_style: baseStyle,
        base_thickness: baseThicknessInput ? parseFloat(baseThicknessInput.value) : 2.4,
        text_thickness: textThicknessInput ? parseFloat(textThicknessInput.value) : 1.2,
        text_mode: textMode,
        corner_radius: cornerRadiusInput ? parseFloat(cornerRadiusInput.value) : 4.0,
        padding_x: paddingXInput ? parseFloat(paddingXInput.value) : 5.0,
        padding_y: paddingYInput ? parseFloat(paddingYInput.value) : 4.5,
        hole_enabled: holeToggle ? holeToggle.checked : true,
        hole_position: holePos,
        hole_diameter: holeDiameterInput ? parseFloat(holeDiameterInput.value) : 5.0,
        icon_name: iconName,
        icon_position: iconPos,
        extruder_base: baseExtruder,
        extruder_text: textExtruder,
        extruder_icon: iconExtruder,
        filament_colors: palette,
      };
    }
  }

  // ==========================================
  // 6. CHIAMATA ANTEPRIMA CON DEBOUNCE
  // ==========================================
  function triggerPreview(immediate = false) {
    if (debounceTimer) clearTimeout(debounceTimer);

    if (immediate) {
      executePreview();
    } else {
      if (statusDot) statusDot.classList.add("busy");
      if (statusText) statusText.textContent = "Modifica in corso...";
      debounceTimer = setTimeout(executePreview, 260);
    }
  }

  async function executePreview() {
    const params = getParams();
    if (statusDot) statusDot.classList.add("busy");
    if (statusText) statusText.textContent = "Calcolo geometria 3D...";
    isRequestPending = true;

    try {
      const response = await fetch(`${API_BASE_URL}/api/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Errore di anteprima geometria.");
      }

      const data = await response.json();
      viewer.updateGeometry(
        data,
        params.filament_colors,
        params.extruder_base,
        params.extruder_text !== undefined ? params.extruder_text : params.extruder_line1
      );

      if (data.dimensions) {
        if (dimWidth) dimWidth.textContent = `${data.dimensions.width} mm`;
        if (dimHeight) dimHeight.textContent = `${data.dimensions.height} mm`;
        if (dimDepth) dimDepth.textContent = `${data.dimensions.depth} mm`;
      }

      if (statusDot) statusDot.classList.remove("busy");
      if (statusText) statusText.textContent = "Pronto per la stampa";
    } catch (error) {
      console.error("Preview error:", error);
      if (statusDot) statusDot.classList.remove("busy");
      if (statusText) statusText.textContent = "Errore di calcolo";
    } finally {
      isRequestPending = false;
    }
  }

  // ==========================================
  // 7. TOOLBAR CAMERA & WIREFRAME
  // ==========================================
  const btnResetView = document.getElementById("btnResetView");
  const btnTopView = document.getElementById("btnTopView");
  const btnFrontView = document.getElementById("btnFrontView");
  const btnWireframe = document.getElementById("btnWireframe");

  safeAddListener(btnResetView, "click", () => viewer.resetView());
  safeAddListener(btnTopView, "click", () => viewer.topView());
  safeAddListener(btnFrontView, "click", () => viewer.frontView());
  safeAddListener(btnWireframe, "click", function () {
    const isWire = viewer.toggleWireframe();
    this.classList.toggle("active", isWire);
  });

  // ==========================================
  // 8. DOWNLOAD 3MF NATIVO PER SNAPMAKER U1
  // ==========================================
  if (btnGenerate) {
    btnGenerate.addEventListener("click", async () => {
      const params = getParams();

      // Disabilita pulsante e attiva spinner
      btnGenerate.disabled = true;
      btnGenerate.classList.add("loading");
      btnGenerate.innerHTML = `<span class="spinner"></span> Preparazione 3MF...`;

      if (statusText) statusText.textContent = "Compilazione pacchetto 3MF in corso...";

      // Timer di Cold Start (se Render free tier è in standby e richiede ~30s per risvegliarsi)
      let coldStartNotice = null;
      const coldStartTimer = setTimeout(() => {
        coldStartNotice = ToastManager.show({
          type: "warning",
          title: "Risveglio Server Cloud (Render Free Tier)",
          message: "Il backend cloud si sta avviando dallo standby. Può richiedere ~30-40 secondi per il primo caricamento. Attendere...",
          duration: 0, // Rimane finché non risponde
        });
      }, 3500);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minuti timeout massimo

      try {
        const response = await fetch(`${API_BASE_URL}/api/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
          signal: controller.signal,
        });

        clearTimeout(coldStartTimer);
        clearTimeout(timeoutId);
        if (coldStartNotice) ToastManager.dismiss(coldStartNotice);

        if (!response.ok) {
          let errDetail = `Errore HTTP ${response.status}`;
          try {
            const errJson = await response.json();
            if (errJson && errJson.detail) errDetail = errJson.detail;
          } catch {
            const errText = await response.text();
            if (errText) errDetail = errText;
          }
          throw new Error(errDetail);
        }

        // Nome file coerente
        const disposition = response.headers.get("Content-Disposition");
        let rawName = currentProduct === "desk_sign" ? params.text_line1 : params.text;
        let cleanName = (rawName || "Model").replace(/[^a-zA-Z0-9_\-]/g, "_").trim() || "Model";

        let filename = currentProduct === "desk_sign"
          ? `targhetta_snapmaker_u1_${cleanName}.3mf`
          : `portachiavi_snapmaker_u1_${cleanName}.3mf`;

        if (disposition && disposition.indexOf("filename=") !== -1) {
          const matches = /filename="?([^"]+)"?/.exec(disposition);
          if (matches != null && matches[1]) {
            filename = matches[1];
          }
        }

        // Download automatico Blob
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        if (statusText) statusText.textContent = "✓ 3MF scaricato!";

        ToastManager.show({
          type: "success",
          title: "Download Completato",
          message: `Il file "${filename}" è pronto per lo slicing su Snapmaker Orca.`,
          duration: 6000,
        });
      } catch (err) {
        clearTimeout(coldStartTimer);
        clearTimeout(timeoutId);
        if (coldStartNotice) ToastManager.dismiss(coldStartNotice);

        console.error("Errore generazione 3MF:", err);

        let userMsg = err.message;
        if (err.name === "AbortError") {
          userMsg = "La richiesta al server è scaduta (timeout). Riprova tra pochi istanti.";
        } else if (err.message && err.message.includes("Failed to fetch")) {
          userMsg = "Impossibile contattare il server cloud. Verifica la connessione o prova a riconnettere l'API dal pulsante in alto.";
        }

        ToastManager.show({
          type: "error",
          title: "Errore Generazione 3MF",
          message: userMsg,
          duration: 8000,
        });

        if (statusText) statusText.textContent = "Errore durante il download";
      } finally {
        btnGenerate.disabled = false;
        btnGenerate.classList.remove("loading");
        btnGenerate.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          SCARICA 3MF PER SNAPMAKER U1
        `;
      }
    });
  }
});
