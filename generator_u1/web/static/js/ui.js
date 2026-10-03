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

const DEFAULT_CURATED_ICONS = [
  {
    "id": "none",
    "name": "Nessuna Icona",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Solo testo senza simboli aggiuntivi",
    "d": "",
    "viewBox": "0 0 512 512"
  },
  {
    "id": "cuore",
    "name": "Cuore",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Cuore romantico solido e continuo",
    "d": "M47.6 300.4L228.3 469.1c7.5 7 17.4 10.9 27.7 10.9s20.2-3.9 27.7-10.9L464.4 300.4c30.4-28.3 47.6-68 47.6-109.5v-5.8c0-69.9-50.5-129.5-119.4-141C347 36.5 300.6 51.4 268 84L256 96 244 84c-32.6-32.6-79-47.5-124.6-39.9C50.5 55.6 0 115.2 0 185.1v5.8c0 41.5 17.2 81.2 47.6 109.5z",
    "viewBox": "0 0 512 512"
  },
  {
    "id": "stella",
    "name": "Stella",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Stella a 5 punte bilanciata",
    "d": "M316.9 18C311.6 7 300.4 0 288.1 0s-23.4 7-28.8 18L195 150.3 51.4 171.5c-12 1.8-22 10.2-25.7 21.7s-.7 24.2 7.9 32.7L137.8 329 113.2 474.7c-2 12 3 24.2 12.9 31.3s23 8 33.8 2.3l128.3-68.5 128.3 68.5c10.8 5.7 23.9 4.9 33.8-2.3s14.9-19.3 12.9-31.3L438.5 329 542.7 225.9c8.6-8.5 11.7-21.2 7.9-32.7s-13.7-19.9-25.7-21.7L381.2 150.3 316.9 18z",
    "viewBox": "0 0 576 512"
  },
  {
    "id": "zampa",
    "name": "Zampa",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Impronta zampa di cane o gatto con 4 dita e cuscinetto",
    "d": "M226.5 92.9c14.3 42.9-.3 86.2-32.6 96.8s-70.1-15.6-84.4-58.5s.3-86.2 32.6-96.8s70.1 15.6 84.4 58.5zM100.4 198.6c18.9 32.4 14.3 70.1-10.2 84.1s-59.7-.9-78.5-33.3S-2.7 179.3 21.8 165.3s59.7 .9 78.5 33.3zM69.2 401.2C121.6 259.9 214.7 224 256 224s134.4 35.9 186.8 177.2c3.6 9.7 5.2 20.1 5.2 30.5l0 1.6c0 25.8-20.9 46.7-46.7 46.7c-11.5 0-22.9-1.4-34-4.2l-88-22c-15.3-3.8-31.3-3.8-46.6 0l-88 22c-11.1 2.8-22.5 4.2-34 4.2C84.9 480 64 459.1 64 433.3l0-1.6c0-10.4 1.6-20.8 5.2-30.5zM421.8 282.7c-24.5-14-29.1-51.7-10.2-84.1s54-47.3 78.5-33.3s29.1 51.7 10.2 84.1s-54 47.3-78.5 33.3zM310.1 189.7c-32.3-10.6-46.9-53.9-32.6-96.8s52.1-69.1 84.4-58.5s46.9 53.9 32.6 96.8s-52.1 69.1-84.4 58.5z",
    "viewBox": "0 0 512 512"
  },
  {
    "id": "quadrifoglio",
    "name": "Quadrifoglio",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Quadrifoglio 4 lobi a cuore con gambo arcuato",
    "d": "M216.6 49.9C205.1 38.5 189.5 32 173.3 32C139.4 32 112 59.4 112 93.3l0 4.9c0 12 3.3 23.7 9.4 34l18.8 31.3c1.1 1.8 1.2 3.1 1 4.2c-.2 1.2-.8 2.5-2 3.6s-2.4 1.8-3.6 2c-1 .2-2.4 .1-4.2-1l-31.3-18.8c-10.3-6.2-22-9.4-34-9.4l-4.9 0C27.4 144 0 171.4 0 205.3c0 16.2 6.5 31.8 17.9 43.3l1.2 1.2c3.4 3.4 3.4 9 0 12.4l-1.2 1.2C6.5 274.9 0 290.5 0 306.7C0 340.6 27.4 368 61.3 368l4.9 0c12 0 23.7-3.3 34-9.4l31.3-18.8c1.8-1.1 3.1-1.2 4.2-1c1.2 .2 2.5 .8 3.6 2s1.8 2.4 2 3.6c.2 1 .1 2.4-1 4.2l-18.8 31.3c-6.2 10.3-9.4 22-9.4 34l0 4.9c0 33.8 27.4 61.3 61.3 61.3c16.2 0 31.8-6.5 43.3-17.9l1.2-1.2c3.4-3.4 9-3.4 12.4 0l1.2 1.2c11.5 11.5 27.1 17.9 43.3 17.9c33.8 0 61.3-27.4 61.3-61.3l0-4.9c0-12-3.3-23.7-9.4-34l-18.8-31.3c-1.1-1.8-1.2-3.1-1-4.2c.2-1.2 .8-2.5 2-3.6s2.4-1.8 3.6-2c1-.2 2.4-.1 4.2 1l31.3 18.8c10.3 6.2 22 9.4 34 9.4l4.9 0c33.8 0 61.3-27.4 61.3-61.3c0-16.2-6.5-31.8-17.9-43.3l-1.2-1.2c-3.4-3.4-3.4-9 0-12.4l1.2-1.2c11.5-11.5 17.9-27.1 17.9-43.3c0-33.8-27.4-61.3-61.3-61.3l-4.9 0c-12 0-23.7 3.3-34 9.4l-31.3 18.8c-1.8 1.1-3.1 1.2-4.2 1c-1.2-.2-2.5-.8-3.6-2s-1.8-2.4-2-3.6c-.2-1-.1-2.4 1-4.2l18.8-31.3c6.2-10.3 9.4-22 9.4-34l0-4.9C336 59.4 308.6 32 274.7 32c-16.2 0-31.8 6.5-43.3 17.9l-1.2 1.2c-3.4 3.4-9 3.4-12.4 0l-1.2-1.2z M 215 330 C 210 440 250 510 320 540 C 310 545 230 520 190 440 C 180 390 195 330 215 330 Z",
    "viewBox": "0 0 512 550"
  },
  {
    "id": "gatto",
    "name": "Gatto",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Silhouette gattino seduto con orecchie e coda",
    "d": "M320 192l17.1 0c22.1 38.3 63.5 64 110.9 64c11 0 21.8-1.4 32-4l0 4 0 32 0 192c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-140.8L280 448l56 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-144 0c-53 0-96-43-96-96l0-223.5c0-16.1-12-29.8-28-31.8l-7.9-1c-17.5-2.2-30-18.2-27.8-35.7s18.2-30 35.7-27.8l7.9 1c48 6 84.1 46.8 84.1 95.3l0 85.3c34.4-51.7 93.2-85.8 160-85.8zm160 26.5s0 0 0 0c-10 3.5-20.8 5.5-32 5.5c-28.4 0-54-12.4-71.6-32c0 0 0 0 0 0c-3.7-4.1-7-8.5-9.9-13.2C357.3 164 352 146.6 352 128c0 0 0 0 0 0l0-96 0-20 0-1.3C352 4.8 356.7 .1 362.6 0l.2 0c3.3 0 6.4 1.6 8.4 4.2c0 0 0 0 0 .1L384 21.3l27.2 36.3L416 64l64 0 4.8-6.4L512 21.3 524.8 4.3c0 0 0 0 0-.1c2-2.6 5.1-4.2 8.4-4.2l.2 0C539.3 .1 544 4.8 544 10.7l0 1.3 0 20 0 96c0 17.3-4.6 33.6-12.6 47.6c-11.3 19.8-29.6 35.2-51.4 42.9zM432 128a16 16 0 1 0 -32 0 16 16 0 1 0 32 0zm48 16a16 16 0 1 0 0-32 16 16 0 1 0 0 32z",
    "viewBox": "0 0 576 512"
  },
  {
    "id": "cane",
    "name": "Cane",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Profilo sagomato di cane con collare ed orecchie",
    "d": "M309.6 158.5L332.7 19.8C334.6 8.4 344.5 0 356.1 0c7.5 0 14.5 3.5 19 9.5L392 32l52.1 0c12.7 0 24.9 5.1 33.9 14.1L496 64l56 0c13.3 0 24 10.7 24 24l0 24c0 44.2-35.8 80-80 80l-32 0-16 0-21.3 0-5.1 30.5-112-64zM416 256.1L416 480c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-115.2c-24 12.3-51.2 19.2-80 19.2s-56-6.9-80-19.2L160 480c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-230.2c-28.8-10.9-51.4-35.3-59.2-66.5L1 167.8c-4.3-17.1 6.1-34.5 23.3-38.8s34.5 6.1 38.8 23.3l3.9 15.5C70.5 182 83.3 192 98 192l30 0 16 0 159.8 0L416 256.1zM464 80a16 16 0 1 0 -32 0 16 16 0 1 0 32 0z",
    "viewBox": "0 0 576 512"
  },
  {
    "id": "corona",
    "name": "Corona",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Corona regale con base solida e punte",
    "d": "M309 106c11.4-7 19-19.7 19-34c0-22.1-17.9-40-40-40s-40 17.9-40 40c0 14.4 7.6 27 19 34L209.7 220.6c-9.1 18.2-32.7 23.4-48.6 10.7L72 160c5-6.7 8-15 8-24c0-22.1-17.9-40-40-40S0 113.9 0 136s17.9 40 40 40c.2 0 .5 0 .7 0L86.4 427.4c5.5 30.4 32 52.6 63 52.6l277.2 0c30.9 0 57.4-22.1 63-52.6L535.3 176c.2 0 .5 0 .7 0c22.1 0 40-17.9 40-40s-17.9-40-40-40s-40 17.9-40 40c0 9 3 17.3 8 24l-89.1 71.3c-15.9 12.7-39.5 7.5-48.6-10.7L309 106z",
    "viewBox": "0 0 576 512"
  },
  {
    "id": "fulmine",
    "name": "Fulmine",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Fulmine classico geometrico e affilato",
    "d": "M349.4 44.6c5.9-13.7 1.5-29.7-10.6-38.5s-28.6-8-39.9 1.8l-256 224c-10 8.8-13.6 22.9-8.9 35.3S50.7 288 64 288l111.5 0L98.6 467.4c-5.9 13.7-1.5 29.7 10.6 38.5s28.6 8 39.9-1.8l256-224c10-8.8 13.6-22.9 8.9-35.3s-16.6-20.7-30-20.7l-111.5 0L349.4 44.6z",
    "viewBox": "0 0 448 512"
  }
];

let globalIconsList = [...DEFAULT_CURATED_ICONS];


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
// 0.3 CUSTOM ICON DROPDOWN COMPONENT (Libreria 40+ Simboli Vettoriali e Ricerca)
// ==============================================================================
class CustomIconDropdown {
  constructor(selectElem, onIconChange) {
    this.selectElem = selectElem;
    this.onIconChange = onIconChange;
    this.currentCategory = "all";
    this.searchTerm = "";

    this.init();
  }

  init() {
    this.selectElem.style.display = "none";

    this.wrapper = document.createElement("div");
    this.wrapper.className = "custom-icon-dropdown";

    this.wrapper.innerHTML = `
      <div class="custom-icon-trigger" tabindex="0">
        <div class="custom-icon-trigger-info">
          <div class="custom-icon-trigger-preview">
            <span class="custom-icon-none-badge">✕</span>
          </div>
          <span class="custom-icon-current-name">Nessuna Icona</span>
          <span class="custom-icon-current-badge">Solo Testo</span>
        </div>
        <span class="custom-icon-arrow">▼</span>
      </div>
      <div class="custom-icon-menu">
        <div class="custom-icon-search-box">
          <input type="text" class="custom-icon-search-input" placeholder="🔍 Cerca simbolo (es. cuore, zampa, auto, gamer, sport)...">
        </div>
        <div class="custom-icon-filter-chips">
          <button type="button" class="custom-icon-chip active" data-cat="all">Tutti</button>
          <button type="button" class="custom-icon-chip" data-cat="forme">Forme</button>
          <button type="button" class="custom-icon-chip" data-cat="animali">Animali</button>
          <button type="button" class="custom-icon-chip" data-cat="gaming">Gaming</button>
          <button type="button" class="custom-icon-chip" data-cat="musica">Musica</button>
          <button type="button" class="custom-icon-chip" data-cat="sport">Sport</button>
          <button type="button" class="custom-icon-chip" data-cat="motori">Motori</button>
          <button type="button" class="custom-icon-chip" data-cat="natura">Natura</button>
          <button type="button" class="custom-icon-chip" data-cat="simboli">Simboli</button>
        </div>
        <div class="custom-icon-options-list"></div>
      </div>
    `;

    this.selectElem.parentNode.insertBefore(this.wrapper, this.selectElem.nextSibling);

    this.trigger = this.wrapper.querySelector(".custom-icon-trigger");
    this.menu = this.wrapper.querySelector(".custom-icon-menu");
    this.previewWrap = this.wrapper.querySelector(".custom-icon-trigger-preview");
    this.currentName = this.wrapper.querySelector(".custom-icon-current-name");
    this.currentBadge = this.wrapper.querySelector(".custom-icon-current-badge");
    this.searchInput = this.wrapper.querySelector(".custom-icon-search-input");
    this.optionsList = this.wrapper.querySelector(".custom-icon-options-list");
    this.chips = this.wrapper.querySelectorAll(".custom-icon-chip");

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
    document.querySelectorAll(".custom-icon-dropdown.open, .custom-font-dropdown.open").forEach((d) => {
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
    const selectedVal = this.selectElem.value || "none";
    const icon = globalIconsList.find((i) => i.id === selectedVal) || {
      id: "none",
      name: "Nessuna Icona",
      category: "forme",
      category_name: "Solo Testo",
      d: ""
    };

    if (icon.d) {
      const vb = icon.viewBox || "0 0 512 512";
    this.previewWrap.innerHTML = `<svg viewBox="${vb}"><path d="${icon.d}" fill="currentColor" /></svg>`;
    } else {
      this.previewWrap.innerHTML = `<span class="custom-icon-none-badge">✕</span>`;
    }

    this.currentName.textContent = icon.name;
    this.currentBadge.textContent = icon.category_name || icon.category;
  }

  renderOptions() {
    this.optionsList.innerHTML = "";
    const selectedVal = this.selectElem.value || "none";

    const filtered = globalIconsList.filter((icon) => {
      const matchCat = this.currentCategory === "all" || icon.category === this.currentCategory;
      const matchSearch = !this.searchTerm ||
        icon.id.toLowerCase().includes(this.searchTerm) ||
        (icon.name && icon.name.toLowerCase().includes(this.searchTerm)) ||
        (icon.desc && icon.desc.toLowerCase().includes(this.searchTerm));
      return matchCat && matchSearch;
    });

    if (filtered.length === 0) {
      this.optionsList.innerHTML = `<div style="padding: 12px; color: var(--text-dim); text-align: center; font-size: 12px;">Nessun simbolo trovato.</div>`;
      return;
    }

    filtered.forEach((icon) => {
      const isSelected = icon.id === selectedVal;
      const item = document.createElement("div");
      item.className = `custom-icon-option-item ${isSelected ? "selected" : ""}`;
      item.dataset.value = icon.id;

      const vb = icon.viewBox || "0 0 512 512";
      const svgHtml = icon.d
        ? `<svg viewBox="${vb}"><path d="${icon.d}" fill="currentColor" /></svg>`
        : `<span style="font-size: 14px; opacity: 0.7;">❌</span>`;

      item.innerHTML = `
        <div class="custom-icon-item-left">
          <div class="custom-icon-svg-wrap">
            ${svgHtml}
          </div>
          <div class="custom-icon-item-texts">
            <div class="custom-icon-item-name">${icon.name}</div>
            <div class="custom-icon-item-desc">${icon.desc}</div>
          </div>
        </div>
        <div class="custom-icon-item-meta">
          <span class="custom-icon-item-badge">${icon.category_name || icon.category}</span>
          ${isSelected ? `<span class="custom-icon-check">✓</span>` : ""}
        </div>
      `;

      item.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectIcon(icon.id);
      });

      this.optionsList.appendChild(item);
    });
  }

  selectIcon(iconId) {
    this.selectElem.value = iconId;
    this.updateFromSelect();
    this.closeMenu();

    const event = new Event("change", { bubbles: true });
    this.selectElem.dispatchEvent(event);

    if (this.onIconChange) this.onIconChange(iconId);
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
  const headerTabKeychain = document.getElementById("headerTabKeychain");
  const headerTabDeskSign = document.getElementById("headerTabDeskSign");

  // --- Elementi Portachiavi (Keychain) ---
  const textInput = document.getElementById("textInput");
  const fontSelect = document.getElementById("fontSelect");
  const iconSelect = document.getElementById("iconSelect");
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
  const btnResetDefaults = document.getElementById("btnResetDefaults");
  const dimWidth = document.getElementById("dimWidth");
  const dimHeight = document.getElementById("dimHeight");
  const dimDepth = document.getElementById("dimDepth");
  const statusPill = document.getElementById("statusPill");
  const statusDot = statusPill ? statusPill.querySelector(".status-dot") : null;
  const statusText = document.getElementById("statusText");

  // ==========================================
  // 1.1 GESTIONE SELETTORE PRODOTTO (TABS)
  // ==========================================
  function setProduct(product, skipPreview = false) {
    currentProduct = product;
    if (product === "desk_sign") {
      if (tabDeskSign) tabDeskSign.classList.add("active");
      if (tabKeychain) tabKeychain.classList.remove("active");
      if (headerTabDeskSign) headerTabDeskSign.classList.add("active");
      if (headerTabKeychain) headerTabKeychain.classList.remove("active");
      document.body.classList.add("mode-desksign");
    } else {
      if (tabKeychain) tabKeychain.classList.add("active");
      if (tabDeskSign) tabDeskSign.classList.remove("active");
      if (headerTabKeychain) headerTabKeychain.classList.add("active");
      if (headerTabDeskSign) headerTabDeskSign.classList.remove("active");
      document.body.classList.remove("mode-desksign");
    }
    if (!skipPreview) {
      triggerPreview(true);
    }
  }

  safeAddListener(tabKeychain, "click", () => setProduct("keychain"));
  safeAddListener(tabDeskSign, "click", () => setProduct("desk_sign"));
  safeAddListener(headerTabKeychain, "click", () => setProduct("keychain"));
  safeAddListener(headerTabDeskSign, "click", () => setProduct("desk_sign"));

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

  // Inizializza i 3 custom dropdown font
  const dropdownKeychain = fontSelect ? new CustomFontDropdown(fontSelect, () => triggerPreview(true)) : null;
  const dropdownDs1 = dsFont1Select ? new CustomFontDropdown(dsFont1Select, () => triggerPreview(true)) : null;
  const dropdownDs2 = dsFont2Select ? new CustomFontDropdown(dsFont2Select, () => triggerPreview(true)) : null;

  // Inizializza custom dropdown icona vettoriale
  function populateIconOptions(selectElem, icons, selectedId) {
    if (!selectElem) return;
    const prevVal = selectElem.value || selectedId || "none";
    selectElem.innerHTML = "";
    icons.forEach((icon) => {
      const opt = document.createElement("option");
      opt.value = icon.id;
      opt.textContent = `${icon.id === "none" ? "❌ " : ""}${icon.name}`;
      if (icon.id === prevVal) opt.selected = true;
      selectElem.appendChild(opt);
    });
  }

  populateIconOptions(iconSelect, globalIconsList, "none");
  const dropdownIcon = iconSelect ? new CustomIconDropdown(iconSelect, (iconId) => {
    if (iconOptionsWrap) {
      iconOptionsWrap.style.display = (iconId && iconId !== "none") ? "flex" : "none";
    }
    triggerPreview(true);
  }) : null;

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

  // ==============================================================================
  // 2.1 PERSISTENZA STATO UTENTE (AUTO-SAVE / AUTO-RESTORE IN LOCALSTORAGE)
  // ==============================================================================
  const STORAGE_STATE_KEY = "snapmaker_u1_last_state";

  function collectFullState() {
    const palette = [
      colorT0 ? colorT0.value : "#161616",
      colorT1 ? colorT1.value : "#ffffff",
      colorT2 ? colorT2.value : "#e31b23",
      colorT3 ? colorT3.value : "#ffd400",
    ];

    const baseExtruder = extruderBaseSelect ? parseInt(extruderBaseSelect.value) : 0;
    const textExtruder = extruderTextSelect ? parseInt(extruderTextSelect.value) : 1;
    let iconExtruder = extruderIconSelect ? parseInt(extruderIconSelect.value) : -1;
    if (iconExtruder === -1) iconExtruder = textExtruder;

    return {
      version: "1.0",
      currentProduct: currentProduct || "keychain",
      palette: palette,

      // Parametri Portachiavi
      keychain: {
        text: textInput ? textInput.value : "ANTONELLO",
        font_family: fontSelect ? fontSelect.value : "Anton",
        font_size: fontSizeInput ? parseFloat(fontSizeInput.value) : 14.0,
        letter_spacing: letterSpacingInput ? parseFloat(letterSpacingInput.value) : 0.0,
        base_style: document.querySelector('input[name="baseStyle"]:checked')?.value || "rectangle",
        base_thickness: baseThicknessInput ? parseFloat(baseThicknessInput.value) : 2.4,
        text_thickness: textThicknessInput ? parseFloat(textThicknessInput.value) : 1.2,
        text_mode: document.querySelector('input[name="textMode"]:checked')?.value || "embossed",
        corner_radius: cornerRadiusInput ? parseFloat(cornerRadiusInput.value) : 4.0,
        padding_x: paddingXInput ? parseFloat(paddingXInput.value) : 5.0,
        padding_y: paddingYInput ? parseFloat(paddingYInput.value) : 4.5,
        hole_enabled: holeToggle ? holeToggle.checked : true,
        hole_position: document.querySelector('input[name="holePos"]:checked')?.value || "left",
        hole_diameter: holeDiameterInput ? parseFloat(holeDiameterInput.value) : 5.0,
        icon_name: iconSelect ? iconSelect.value : "none",
        icon_position: document.querySelector('input[name="iconPos"]:checked')?.value || "left",
        extruder_base: baseExtruder,
        extruder_text: textExtruder,
        extruder_icon: extruderIconSelect ? parseInt(extruderIconSelect.value) : -1,
      },

      // Parametri Targhetta da Tavolo
      desk_sign: {
        base_mode: document.querySelector('input[name="dsBaseMode"]:checked')?.value || "wedge",
        wedge_angle: dsWedgeAngleInput ? parseFloat(dsWedgeAngleInput.value) : 45.0,
        base_thickness: dsBaseThicknessInput ? parseFloat(dsBaseThicknessInput.value) : 3.0,
        corner_radius: dsCornerRadiusInput ? parseFloat(dsCornerRadiusInput.value) : 3.0,
        padding_x: dsPaddingXInput ? parseFloat(dsPaddingXInput.value) : 8.0,
        padding_y: dsPaddingYInput ? parseFloat(dsPaddingYInput.value) : 6.0,
        line_spacing: dsLineSpacingInput ? parseFloat(dsLineSpacingInput.value) : 3.5,
        text_align: document.querySelector('input[name="dsTextAlign"]:checked')?.value || "center",
        text_line1: dsText1Input ? dsText1Input.value : "STUDIO U1",
        font_family_line1: dsFont1Select ? dsFont1Select.value : "Anton",
        font_size_line1: dsFontSize1Input ? parseFloat(dsFontSize1Input.value) : 14.0,
        thickness_line1: dsThickness1Input ? parseFloat(dsThickness1Input.value) : 1.2,
        extruder_line1: dsExtruderLine1Select ? parseInt(dsExtruderLine1Select.value) : 1,
        line2_enabled: dsLine2Toggle ? dsLine2Toggle.checked : false,
        text_line2: dsText2Input ? dsText2Input.value : "BASE SET 1999",
        font_family_line2: dsFont2Select ? dsFont2Select.value : "Montserrat",
        font_size_line2: dsFontSize2Input ? parseFloat(dsFontSize2Input.value) : 7.5,
        thickness_line2: dsThickness2Input ? parseFloat(dsThickness2Input.value) : 1.0,
        extruder_line2: dsExtruderLine2Select ? parseInt(dsExtruderLine2Select.value) : 2,
        border_enabled: dsBorderToggle ? dsBorderToggle.checked : true,
        border_width: dsBorderWidthInput ? parseFloat(dsBorderWidthInput.value) : 2.0,
        border_thickness: dsBorderThicknessInput ? parseFloat(dsBorderThicknessInput.value) : 1.0,
        cornerRadius: dsCornerRadiusInput ? parseFloat(dsCornerRadiusInput.value) : 3.0,
        extruder_border: dsExtruderBorderSelect ? parseInt(dsExtruderBorderSelect.value) : 3,
        extruder_base: baseExtruder,
      }
    };
  }

  function saveCurrentStateToLocalStorage() {
    try {
      const state = collectFullState();
      localStorage.setItem(STORAGE_STATE_KEY, JSON.stringify(state));
    } catch (err) {
      console.warn("Impossibile salvare lo stato in localStorage:", err);
    }
  }

  function restoreStateFromLocalStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_STATE_KEY);
      if (!raw) return false;
      const state = JSON.parse(raw);
      if (!state || typeof state !== "object") return false;

      // 1. Ripristino Palette Colori
      if (Array.isArray(state.palette) && state.palette.length >= 4) {
        if (colorT0) colorT0.value = state.palette[0];
        if (colorT1) colorT1.value = state.palette[1];
        if (colorT2) colorT2.value = state.palette[2];
        if (colorT3) colorT3.value = state.palette[3];
        const c0 = colorT0 ? colorT0.value : "#161616";
        const c1 = colorT1 ? colorT1.value : "#ffffff";
        const c2 = colorT2 ? colorT2.value : "#e31b23";
        const c3 = colorT3 ? colorT3.value : "#ffd400";
        viewer.updateColors([c0, c1, c2, c3]);
      }

      // 2. Ripristino Parametri Portachiavi
      const kc = state.keychain || (state.generator === "keychain" ? state : null);
      if (kc) {
        if (textInput && kc.text !== undefined) textInput.value = kc.text;
        if (fontSelect && kc.font_family) fontSelect.value = kc.font_family;
        if (fontSizeInput && kc.font_size !== undefined) {
          fontSizeInput.value = kc.font_size;
          if (fontSizeVal) fontSizeVal.textContent = `${kc.font_size} mm`;
        }
        if (letterSpacingInput && kc.letter_spacing !== undefined) {
          letterSpacingInput.value = kc.letter_spacing;
          if (letterSpacingVal) letterSpacingVal.textContent = `${kc.letter_spacing} mm`;
        }
        if (kc.base_style) {
          const r = document.querySelector(`input[name="baseStyle"][value="${kc.base_style}"]`);
          if (r) r.checked = true;
        }
        if (baseThicknessInput && kc.base_thickness !== undefined) {
          baseThicknessInput.value = kc.base_thickness;
          if (baseThicknessVal) baseThicknessVal.textContent = `${kc.base_thickness} mm`;
        }
        if (textThicknessInput && kc.text_thickness !== undefined) {
          textThicknessInput.value = kc.text_thickness;
          if (textThicknessVal) textThicknessVal.textContent = `${kc.text_thickness} mm`;
        }
        if (kc.text_mode) {
          const r = document.querySelector(`input[name="textMode"][value="${kc.text_mode}"]`);
          if (r) r.checked = true;
        }
        if (cornerRadiusInput && kc.corner_radius !== undefined) {
          cornerRadiusInput.value = kc.corner_radius;
          if (cornerRadiusVal) cornerRadiusVal.textContent = `${kc.corner_radius} mm`;
        }
        if (paddingXInput && kc.padding_x !== undefined) {
          paddingXInput.value = kc.padding_x;
          if (paddingXVal) paddingXVal.textContent = `${kc.padding_x} mm`;
        }
        if (paddingYInput && kc.padding_y !== undefined) {
          paddingYInput.value = kc.padding_y;
          if (paddingYVal) paddingYVal.textContent = `${kc.padding_y} mm`;
        }
        if (holeToggle && kc.hole_enabled !== undefined) {
          holeToggle.checked = Boolean(kc.hole_enabled);
          if (holeOptionsWrap) holeOptionsWrap.style.display = holeToggle.checked ? "flex" : "none";
        }
        if (kc.hole_position) {
          const r = document.querySelector(`input[name="holePos"][value="${kc.hole_position}"]`);
          if (r) r.checked = true;
        }
        if (holeDiameterInput && kc.hole_diameter !== undefined) {
          holeDiameterInput.value = kc.hole_diameter;
          if (holeDiameterVal) holeDiameterVal.textContent = `${kc.hole_diameter} mm`;
        }
        if (iconSelect && kc.icon_name !== undefined) {
          const aliasMap = { heart: "cuore", star: "stella", paw: "zampa", clover: "quadrifoglio", cat: "gatto", dog: "cane", crown: "corona", lightning: "fulmine", bolt: "fulmine" };
          const resolvedIcon = aliasMap[kc.icon_name.toLowerCase()] || kc.icon_name;
          iconSelect.value = resolvedIcon;
          if (iconOptionsWrap) {
            iconOptionsWrap.style.display = (kc.icon_name && kc.icon_name !== "none") ? "flex" : "none";
          }
        }
        if (kc.icon_position) {
          const r = document.querySelector(`input[name="iconPos"][value="${kc.icon_position}"]`);
          if (r) r.checked = true;
        }
        if (extruderBaseSelect && kc.extruder_base !== undefined) {
          extruderBaseSelect.value = kc.extruder_base.toString();
        }
        if (extruderTextSelect && kc.extruder_text !== undefined) {
          extruderTextSelect.value = kc.extruder_text.toString();
        }
        if (extruderIconSelect && kc.extruder_icon !== undefined) {
          extruderIconSelect.value = kc.extruder_icon.toString();
        }
      }

      // 3. Ripristino Parametri Targhetta da Tavolo
      const ds = state.desk_sign || (state.generator === "desk_sign" ? state : null);
      if (ds) {
        if (ds.base_mode) {
          const r = document.querySelector(`input[name="dsBaseMode"][value="${ds.base_mode}"]`);
          if (r) r.checked = true;
          if (dsWedgeAngleGroup) dsWedgeAngleGroup.style.display = ds.base_mode === "wedge" ? "flex" : "none";
        }
        if (dsWedgeAngleInput && ds.wedge_angle !== undefined) {
          dsWedgeAngleInput.value = ds.wedge_angle;
          if (dsWedgeAngleVal) dsWedgeAngleVal.textContent = `${ds.wedge_angle}°`;
        }
        if (dsBaseThicknessInput && ds.base_thickness !== undefined) {
          dsBaseThicknessInput.value = ds.base_thickness;
          if (dsBaseThicknessVal) dsBaseThicknessVal.textContent = `${ds.base_thickness} mm`;
        }
        if (dsCornerRadiusInput && ds.corner_radius !== undefined) {
          dsCornerRadiusInput.value = ds.corner_radius;
          if (dsCornerRadiusVal) dsCornerRadiusVal.textContent = `${ds.corner_radius} mm`;
        }
        if (dsPaddingXInput && ds.padding_x !== undefined) {
          dsPaddingXInput.value = ds.padding_x;
          if (dsPaddingXVal) dsPaddingXVal.textContent = `${ds.padding_x} mm`;
        }
        if (dsPaddingYInput && ds.padding_y !== undefined) {
          dsPaddingYInput.value = ds.padding_y;
          if (dsPaddingYVal) dsPaddingYVal.textContent = `${ds.padding_y} mm`;
        }
        if (dsLineSpacingInput && ds.line_spacing !== undefined) {
          dsLineSpacingInput.value = ds.line_spacing;
          if (dsLineSpacingVal) dsLineSpacingVal.textContent = `${ds.line_spacing} mm`;
        }
        if (ds.text_align) {
          const r = document.querySelector(`input[name="dsTextAlign"][value="${ds.text_align}"]`);
          if (r) r.checked = true;
        }
        if (dsText1Input && ds.text_line1 !== undefined) dsText1Input.value = ds.text_line1;
        if (dsFont1Select && ds.font_family_line1) dsFont1Select.value = ds.font_family_line1;
        if (dsFontSize1Input && ds.font_size_line1 !== undefined) {
          dsFontSize1Input.value = ds.font_size_line1;
          if (dsFontSize1Val) dsFontSize1Val.textContent = `${ds.font_size_line1} mm`;
        }
        if (dsThickness1Input && ds.thickness_line1 !== undefined) {
          dsThickness1Input.value = ds.thickness_line1;
          if (dsThickness1Val) dsThickness1Val.textContent = `${ds.thickness_line1} mm`;
        }
        if (dsExtruderLine1Select && ds.extruder_line1 !== undefined) {
          dsExtruderLine1Select.value = ds.extruder_line1.toString();
        }
        if (dsLine2Toggle && ds.line2_enabled !== undefined) {
          dsLine2Toggle.checked = Boolean(ds.line2_enabled);
          if (dsLine2Wrap) dsLine2Wrap.style.display = dsLine2Toggle.checked ? "flex" : "none";
        }
        if (dsText2Input && ds.text_line2 !== undefined) dsText2Input.value = ds.text_line2;
        if (dsFont2Select && ds.font_family_line2) dsFont2Select.value = ds.font_family_line2;
        if (dsFontSize2Input && ds.font_size_line2 !== undefined) {
          dsFontSize2Input.value = ds.font_size_line2;
          if (dsFontSize2Val) dsFontSize2Val.textContent = `${ds.font_size_line2} mm`;
        }
        if (dsThickness2Input && ds.thickness_line2 !== undefined) {
          dsThickness2Input.value = ds.thickness_line2;
          if (dsThickness2Val) dsThickness2Val.textContent = `${ds.thickness_line2} mm`;
        }
        if (dsExtruderLine2Select && ds.extruder_line2 !== undefined) {
          dsExtruderLine2Select.value = ds.extruder_line2.toString();
        }
        if (dsBorderToggle && ds.border_enabled !== undefined) {
          dsBorderToggle.checked = Boolean(ds.border_enabled);
          if (dsBorderWrap) dsBorderWrap.style.display = dsBorderToggle.checked ? "flex" : "none";
        }
        if (dsBorderWidthInput && ds.border_width !== undefined) {
          dsBorderWidthInput.value = ds.border_width;
          if (dsBorderWidthVal) dsBorderWidthVal.textContent = `${ds.border_width} mm`;
        }
        if (dsBorderThicknessInput && ds.border_thickness !== undefined) {
          dsBorderThicknessInput.value = ds.border_thickness;
          if (dsBorderThicknessVal) dsBorderThicknessVal.textContent = `${ds.border_thickness} mm`;
        }
        if (dsCornerRadiusInput && (ds.corner_radius !== undefined || ds.cornerRadius !== undefined)) {
          const cr = ds.corner_radius !== undefined ? ds.corner_radius : ds.cornerRadius;
          dsCornerRadiusInput.value = cr;
          if (dsCornerRadiusVal) dsCornerRadiusVal.textContent = `${cr} mm`;
        }
        if (dsExtruderBorderSelect && ds.extruder_border !== undefined) {
          dsExtruderBorderSelect.value = ds.extruder_border.toString();
        }
      }

      // 4. Aggiorna Custom Dropdowns per riflettere le selezioni ripristinate
      refreshAllDropdowns();
      if (dropdownIcon) {
        dropdownIcon.updateFromSelect();
        dropdownIcon.renderOptions();
      }

      // 5. Attiva Tab salvata
      const targetProduct = state.currentProduct || (state.generator === "desk_sign" ? "desk_sign" : "keychain");
      setProduct(targetProduct, true);

      return true;
    } catch (err) {
      console.error("Errore ripristino stato da localStorage:", err);
      return false;
    }
  }

  function resetDefaults() {
    if (!confirm("Vuoi davvero ripristinare tutti i parametri e la palette ai valori predefiniti?")) {
      return;
    }
    try {
      localStorage.removeItem(STORAGE_STATE_KEY);
    } catch (e) {
      console.warn("Impossibile rimuovere lo stato da localStorage:", e);
    }

    // Reset Keychain
    if (textInput) textInput.value = "ANTONELLO";
    if (fontSelect) fontSelect.value = "Anton";
    if (fontSizeInput) {
      fontSizeInput.value = "14";
      if (fontSizeVal) fontSizeVal.textContent = "14 mm";
    }
    if (letterSpacingInput) {
      letterSpacingInput.value = "0";
      if (letterSpacingVal) letterSpacingVal.textContent = "0 mm";
    }
    const rBaseRec = document.querySelector('input[name="baseStyle"][value="rectangle"]');
    if (rBaseRec) rBaseRec.checked = true;
    if (baseThicknessInput) {
      baseThicknessInput.value = "2.4";
      if (baseThicknessVal) baseThicknessVal.textContent = "2.4 mm";
    }
    if (cornerRadiusInput) {
      cornerRadiusInput.value = "4";
      if (cornerRadiusVal) cornerRadiusVal.textContent = "4 mm";
    }
    if (paddingXInput) {
      paddingXInput.value = "5";
      if (paddingXVal) paddingXVal.textContent = "5 mm";
    }
    if (paddingYInput) {
      paddingYInput.value = "4.5";
      if (paddingYVal) paddingYVal.textContent = "4.5 mm";
    }
    const rTextEmb = document.querySelector('input[name="textMode"][value="embossed"]');
    if (rTextEmb) rTextEmb.checked = true;
    if (textThicknessInput) {
      textThicknessInput.value = "1.2";
      if (textThicknessVal) textThicknessVal.textContent = "1.2 mm";
    }
    if (holeToggle) {
      holeToggle.checked = true;
      if (holeOptionsWrap) holeOptionsWrap.style.display = "flex";
    }
    const rHoleLeft = document.querySelector('input[name="holePos"][value="left"]');
    if (rHoleLeft) rHoleLeft.checked = true;
    if (holeDiameterInput) {
      holeDiameterInput.value = "5";
      if (holeDiameterVal) holeDiameterVal.textContent = "5 mm";
    }
    if (iconSelect) {
      iconSelect.value = "none";
      if (iconOptionsWrap) iconOptionsWrap.style.display = "none";
    }
    const rIconLeft = document.querySelector('input[name="iconPos"][value="left"]');
    if (rIconLeft) rIconLeft.checked = true;
    if (extruderIconSelect) extruderIconSelect.value = "-1";
    if (extruderBaseSelect) extruderBaseSelect.value = "0";
    if (extruderTextSelect) extruderTextSelect.value = "1";

    // Reset Desk Sign
    const rWedge = document.querySelector('input[name="dsBaseMode"][value="wedge"]');
    if (rWedge) rWedge.checked = true;
    if (dsWedgeAngleGroup) dsWedgeAngleGroup.style.display = "flex";
    if (dsWedgeAngleInput) {
      dsWedgeAngleInput.value = "45";
      if (dsWedgeAngleVal) dsWedgeAngleVal.textContent = "45°";
    }
    if (dsBaseThicknessInput) {
      dsBaseThicknessInput.value = "3.0";
      if (dsBaseThicknessVal) dsBaseThicknessVal.textContent = "3.0 mm";
    }
    if (dsCornerRadiusInput) {
      dsCornerRadiusInput.value = "3";
      if (dsCornerRadiusVal) dsCornerRadiusVal.textContent = "3 mm";
    }
    if (dsPaddingXInput) {
      dsPaddingXInput.value = "8";
      if (dsPaddingXVal) dsPaddingXVal.textContent = "8 mm";
    }
    if (dsPaddingYInput) {
      dsPaddingYInput.value = "6";
      if (dsPaddingYVal) dsPaddingYVal.textContent = "6 mm";
    }
    if (dsLineSpacingInput) {
      dsLineSpacingInput.value = "3.5";
      if (dsLineSpacingVal) dsLineSpacingVal.textContent = "3.5 mm";
    }
    const rAlignCenter = document.querySelector('input[name="dsTextAlign"][value="center"]');
    if (rAlignCenter) rAlignCenter.checked = true;
    if (dsText1Input) dsText1Input.value = "STUDIO U1";
    if (dsFont1Select) dsFont1Select.value = "Anton";
    if (dsFontSize1Input) {
      dsFontSize1Input.value = "14";
      if (dsFontSize1Val) dsFontSize1Val.textContent = "14 mm";
    }
    if (dsThickness1Input) {
      dsThickness1Input.value = "1.2";
      if (dsThickness1Val) dsThickness1Val.textContent = "1.2 mm";
    }
    if (dsExtruderLine1Select) dsExtruderLine1Select.value = "1";

    if (dsLine2Toggle) {
      dsLine2Toggle.checked = true;
      if (dsLine2Wrap) dsLine2Wrap.style.display = "flex";
    }
    if (dsText2Input) dsText2Input.value = "BASE SET 1999";
    if (dsFont2Select) dsFont2Select.value = "Montserrat";
    if (dsFontSize2Input) {
      dsFontSize2Input.value = "7.5";
      if (dsFontSize2Val) dsFontSize2Val.textContent = "7.5 mm";
    }
    if (dsThickness2Input) {
      dsThickness2Input.value = "1.0";
      if (dsThickness2Val) dsThickness2Val.textContent = "1.0 mm";
    }
    if (dsExtruderLine2Select) dsExtruderLine2Select.value = "2";

    if (dsBorderToggle) {
      dsBorderToggle.checked = true;
      if (dsBorderWrap) dsBorderWrap.style.display = "flex";
    }
    if (dsBorderWidthInput) {
      dsBorderWidthInput.value = "2";
      if (dsBorderWidthVal) dsBorderWidthVal.textContent = "2 mm";
    }
    if (dsBorderThicknessInput) {
      dsBorderThicknessInput.value = "1";
      if (dsBorderThicknessVal) dsBorderThicknessVal.textContent = "1 mm";
    }
    if (dsCornerRadiusInput) {
      dsCornerRadiusInput.value = "3";
      if (dsCornerRadiusVal) dsCornerRadiusVal.textContent = "3 mm";
    }
    if (dsExtruderBorderSelect) dsExtruderBorderSelect.value = "3";

    // Palette U1 Official
    if (colorT0) colorT0.value = "#161616";
    if (colorT1) colorT1.value = "#ffffff";
    if (colorT2) colorT2.value = "#e31b23";
    if (colorT3) colorT3.value = "#ffd400";
    onPaletteChange();

    setProduct("keychain", true);
    refreshAllDropdowns();
    if (dropdownIcon) {
      dropdownIcon.updateFromSelect();
      dropdownIcon.renderOptions();
    }

    saveCurrentStateToLocalStorage();
    triggerPreview(true);

    ToastManager.show({
      type: "info",
      title: "Configurazione Ripristinata",
      message: "Tutti i parametri e la palette sono stati reimpostati ai valori di fabbrica.",
      duration: 4000
    });
  }

  safeAddListener(btnResetDefaults, "click", resetDefaults);

  // Esegui ripristino all'avvio: se esiste stato salvato, applicalo e avvia l'anteprima 3D
  const hasRestored = restoreStateFromLocalStorage();
  triggerPreview(true);

  // Caricamento asincrono icone dal backend (preserva la selezione)
  function loadIcons() {
    fetch(`${API_BASE_URL}/api/icons`)
      .then((res) => {
        if (!res.ok) throw new Error("Status " + res.status);
        return res.json();
      })
      .then((icons) => {
        if (Array.isArray(icons) && icons.length > 0) {
          globalIconsList = icons;
          populateIconOptions(iconSelect, globalIconsList, iconSelect?.value || "none");
          if (dropdownIcon) {
            dropdownIcon.updateFromSelect();
            dropdownIcon.renderOptions();
          }
        }
      })
      .catch(() => {});
  }
  loadIcons();

  // Caricamento asincrono font dal backend (preserva la selezione)
  function loadFonts(selectedId = null, triggerPreviewAfter = false) {
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
          if (triggerPreviewAfter) {
            triggerPreview(true);
          }
        }
      })
      .catch(() => {
        refreshAllDropdowns();
      });
  }
  loadFonts(null, false);

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
    saveCurrentStateToLocalStorage();
  }

  safeAddListener(colorT0, "input", onPaletteChange);
  safeAddListener(colorT1, "input", onPaletteChange);
  safeAddListener(colorT2, "input", onPaletteChange);
  safeAddListener(colorT3, "input", onPaletteChange);

  // ==========================================
  // 3.1 SINCRONIZZAZIONE SNAPMAKER U1 (RFID)
  // ==========================================
  const btnOpenSyncModal = document.getElementById("btnOpenSyncModal");
  const syncPrinterModal = document.getElementById("syncPrinterModal");
  const btnCloseSyncModal = document.getElementById("btnCloseSyncModal");
  const btnCancelSyncModal = document.getElementById("btnCancelSyncModal");
  const btnExecuteSync = document.getElementById("btnExecuteSync");
  const printerIpInput = document.getElementById("printerIpInput");
  const printerPortInput = document.getElementById("printerPortInput");
  const printerTokenInput = document.getElementById("printerTokenInput");
  const syncResultStatus = document.getElementById("syncResultStatus");

  // Ripristina impostazioni salvate da localStorage
  try {
    if (printerIpInput) {
      printerIpInput.value = localStorage.getItem("snapmaker_u1_ip") || "";
    }
    if (printerPortInput) {
      printerPortInput.value = localStorage.getItem("snapmaker_u1_port") || "8080";
    }
    if (printerTokenInput) {
      printerTokenInput.value = localStorage.getItem("snapmaker_u1_token") || "";
    }
  } catch (e) {
    console.warn("Accesso a localStorage non disponibile:", e);
  }

  function openSyncModal() {
    if (!syncPrinterModal) return;
    syncPrinterModal.style.display = "flex";
    if (syncResultStatus) {
      syncResultStatus.style.display = "none";
      syncResultStatus.innerHTML = "";
    }
    if (printerIpInput && !printerIpInput.value) {
      printerIpInput.focus();
    }
  }

  function closeSyncModal() {
    if (!syncPrinterModal) return;
    syncPrinterModal.style.display = "none";
  }

  safeAddListener(btnOpenSyncModal, "click", openSyncModal);
  safeAddListener(btnCloseSyncModal, "click", closeSyncModal);
  safeAddListener(btnCancelSyncModal, "click", closeSyncModal);

  if (syncPrinterModal) {
    syncPrinterModal.addEventListener("click", (e) => {
      if (e.target === syncPrinterModal) closeSyncModal();
    });
  }

  safeAddListener(btnExecuteSync, "click", async () => {
    const rawIp = printerIpInput ? printerIpInput.value.trim() : "";
    const port = printerPortInput ? parseInt(printerPortInput.value.trim()) || 8080 : 8080;
    const token = printerTokenInput ? printerTokenInput.value.trim() : "";

    if (!rawIp) {
      if (syncResultStatus) {
        syncResultStatus.style.display = "block";
        syncResultStatus.style.background = "rgba(255, 71, 87, 0.15)";
        syncResultStatus.style.border = "1px solid #ff4757";
        syncResultStatus.style.color = "#ff6b81";
        syncResultStatus.textContent = "Inserisci l'indirizzo IP della tua Snapmaker U1 (es. 192.168.1.150).";
      }
      return;
    }

    // Salva impostazioni in localStorage
    try {
      localStorage.setItem("snapmaker_u1_ip", rawIp);
      localStorage.setItem("snapmaker_u1_port", port.toString());
      localStorage.setItem("snapmaker_u1_token", token);
    } catch (e) {
      console.warn("Impossibile salvare su localStorage:", e);
    }

    // Stato di caricamento
    btnExecuteSync.disabled = true;
    btnExecuteSync.classList.add("loading");
    btnExecuteSync.innerHTML = `<span class="spinner"></span> Connessione in corso...`;

    if (syncResultStatus) {
      syncResultStatus.style.display = "block";
      syncResultStatus.style.background = "rgba(255, 255, 255, 0.05)";
      syncResultStatus.style.border = "1px solid var(--border-subtle)";
      syncResultStatus.style.color = "var(--text-main)";
      syncResultStatus.innerHTML = `Interrogazione Snapmaker U1 su <code>${rawIp}:${port}</code> in corso...`;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/printer/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: rawIp, port, token }),
      });

      const data = await response.json();

      if (data.status === "warning" && data.is_private_network) {
        if (syncResultStatus) {
          syncResultStatus.style.display = "block";
          syncResultStatus.style.background = "rgba(255, 165, 2, 0.15)";
          syncResultStatus.style.border = "1px solid #ffa502";
          syncResultStatus.style.color = "#ffbe76";
          syncResultStatus.innerHTML = `
            <strong>⚠️ Rete Privata Rilevata:</strong> ${data.detail}<br>
            <span style="font-size: 11px; margin-top: 6px; display: block; color: var(--text-muted);">${data.suggestion}</span>
          `;
        }
        ToastManager.show({
          type: "warning",
          title: "Snapmaker U1 su Rete Locale",
          message: "Il backend cloud non può accedere a IP privati della tua rete domestica. Avvia 'python run_web.py' per connetterti direttamente.",
          duration: 9000,
        });
        return;
      }

      if (data.status !== "success" || !data.colors) {
        throw new Error(data.detail || "Impossibile recuperare i dati dalla stampante.");
      }

      // Applica i colori agli slot
      if (colorT0 && data.colors[0]) colorT0.value = data.colors[0];
      if (colorT1 && data.colors[1]) colorT1.value = data.colors[1];
      if (colorT2 && data.colors[2]) colorT2.value = data.colors[2];
      if (colorT3 && data.colors[3]) colorT3.value = data.colors[3];

      onPaletteChange();
      triggerPreview(true);

      const matSummary = (data.materials || ["Slot 1", "Slot 2", "Slot 3", "Slot 4"]).join(", ");

      if (syncResultStatus) {
        syncResultStatus.style.display = "block";
        syncResultStatus.style.background = "rgba(46, 213, 115, 0.15)";
        syncResultStatus.style.border = "1px solid #2ed573";
        syncResultStatus.style.color = "#2ed573";
        syncResultStatus.innerHTML = `
          <strong>✓ Sincronizzazione Riuscita!</strong><br>
          Colori RFID: ${data.colors.join(" | ")}<br>
          <span style="font-size: 10.5px;">${matSummary}</span>
        `;
      }

      ToastManager.show({
        type: "success",
        title: "Palette Sincronizzata (Snapmaker U1)",
        message: `4 Slot aggiornati con successo da RFID: ${matSummary}`,
        duration: 6000,
      });

      setTimeout(() => {
        closeSyncModal();
      }, 1500);

    } catch (err) {
      console.error("Errore sincronizzazione stampante:", err);
      if (syncResultStatus) {
        syncResultStatus.style.display = "block";
        syncResultStatus.style.background = "rgba(255, 71, 87, 0.15)";
        syncResultStatus.style.border = "1px solid #ff4757";
        syncResultStatus.style.color = "#ff6b81";
        syncResultStatus.innerHTML = `
          <strong>Errore di Connessione:</strong> ${err.message}<br>
          <span style="font-size: 10.5px; margin-top: 4px; display: block;">
            Verifica che l'indirizzo IP sia corretto, che la porta sia accessibile (default 8080 o 80) e che la Snapmaker U1 sia accesa.
          </span>
        `;
      }
      ToastManager.show({
        type: "error",
        title: "Errore Connessione U1",
        message: err.message,
        duration: 7000,
      });
    } finally {
      btnExecuteSync.disabled = false;
      btnExecuteSync.classList.remove("loading");
      btnExecuteSync.innerHTML = `<span>⚡ Connetti & Sincronizza</span>`;
    }
  });

  // ==========================================
  // 4. EVENT LISTENERS DINAMICI
  // ==========================================
  // Portachiavi Icone
  safeAddListener(iconSelect, "change", (e) => {
    const val = e.target.value;
    if (iconOptionsWrap) {
      iconOptionsWrap.style.display = (val && val !== "none") ? "flex" : "none";
    }
    triggerPreview(true);
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
      const iconName = iconSelect ? iconSelect.value : "none";
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
    saveCurrentStateToLocalStorage();
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
