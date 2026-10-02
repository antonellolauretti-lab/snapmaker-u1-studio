/**
 * UI Controller & Event Handlers (v4.0 - Multi-Prodotto)
 * Gestisce:
 * 1. Switch tra generatore "Portachiavi" e "Targhetta da Tavolo" (Desk Sign).
 * 2. Parametri geometrici reattivi con debounce per entrambi i template.
 * 3. Caricamento font esterni (.ttf/.otf) e selezione font per singola riga.
 * 4. Palette rapida a 4 slot per Snapmaker U1 con aggiornamento Three.js a 0 ms.
 * 5. Generazione e download 3MF nativo multi-volume per Snapmaker Orca.
 */
document.addEventListener("DOMContentLoaded", () => {
  const viewer = new ModelViewer("canvas-container");
  let debounceTimer = null;
  let isRequestPending = false;
  let currentProduct = "keychain"; // "keychain" | "desk_sign"

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
  const statusDot = statusPill.querySelector(".status-dot");
  const statusText = document.getElementById("statusText");

  // ==========================================
  // 1. GESTIONE SELETTORE PRODOTTO (TABS)
  // ==========================================
  function setProduct(product) {
    currentProduct = product;
    if (product === "desk_sign") {
      tabDeskSign.classList.add("active");
      tabKeychain.classList.remove("active");
      document.body.classList.add("mode-desksign");
    } else {
      tabKeychain.classList.add("active");
      tabDeskSign.classList.remove("active");
      document.body.classList.remove("mode-desksign");
    }
    triggerPreview(true);
  }

  tabKeychain.addEventListener("click", () => setProduct("keychain"));
  tabDeskSign.addEventListener("click", () => setProduct("desk_sign"));

  // ==============================================================================
  // 1.1 CONFIGURAZIONE DINAMICA API_BASE_URL (Supporto Localhost, Vercel & Render)
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
      return ""; // Relativo se servito direttamente da FastAPI
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
      if (apiStatusLabel) apiStatusLabel.textContent = "API: Offline / Disconnessa";
    }
  }

  if (btnApiSettings) {
    btnApiSettings.addEventListener("click", () => {
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
  }

  // Verifica salute API all'avvio
  checkApiHealth();

  // ==========================================
  // 2. INIZIALIZZAZIONE & CARICAMENTO FONT
  // ==========================================
  function populateFontSelect(selectElem, fonts, selectedId) {
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

  function loadFonts(selectedId = "Arial") {
    fetch(`${API_BASE_URL}/api/fonts`)
      .then((res) => res.json())
      .then((fonts) => {
        populateFontSelect(fontSelect, fonts, selectedId);
        populateFontSelect(dsFont1Select, fonts, "Arial");
        populateFontSelect(dsFont2Select, fonts, "Arial");
        triggerPreview(true);
      })
      .catch(() => triggerPreview(true));
  }

  loadFonts("Arial");

  // Upload Font .ttf / .otf
  btnUploadFont.addEventListener("click", () => fontFileInput.click());

  fontFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    fontUploadStatus.style.display = "block";
    fontUploadStatus.style.color = "#ffa502";
    fontUploadStatus.textContent = "Caricamento font...";

    try {
      const res = await fetch(`${API_BASE_URL}/api/fonts/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Errore upload font");
      }

      const data = await res.json();
      fontUploadStatus.style.color = "#2ed573";
      fontUploadStatus.textContent = `✓ Font ${file.name} caricato!`;

      loadFonts(data.font.id);
    } catch (err) {
      fontUploadStatus.style.color = "#ff4757";
      fontUploadStatus.textContent = `Errore: ${err.message}`;
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
        colorT0.value = colors[0];
        colorT1.value = colors[1];
        colorT2.value = colors[2];
        colorT3.value = colors[3];
        onPaletteChange();
      }
    });
  });

  function onPaletteChange() {
    const palette = [colorT0.value, colorT1.value, colorT2.value, colorT3.value];
    viewer.updateColors(palette);
  }

  colorT0.addEventListener("input", onPaletteChange);
  colorT1.addEventListener("input", onPaletteChange);
  colorT2.addEventListener("input", onPaletteChange);
  colorT3.addEventListener("input", onPaletteChange);

  // ==========================================
  // 4. EVENT LISTENERS DINAMICI
  // ==========================================
  // Portachiavi Icone
  document.querySelectorAll('input[name="iconName"]').forEach((r) => {
    r.addEventListener("change", (e) => {
      iconOptionsWrap.style.display = e.target.value !== "none" ? "flex" : "none";
      triggerPreview(true);
    });
  });

  document.querySelectorAll('input[name="iconPos"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });

  extruderIconSelect.addEventListener("change", () => triggerPreview(true));

  // Portachiavi Slider
  textInput.addEventListener("input", () => triggerPreview(false));
  fontSelect.addEventListener("change", () => triggerPreview(true));

  fontSizeInput.addEventListener("input", (e) => {
    fontSizeVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  letterSpacingInput.addEventListener("input", (e) => {
    letterSpacingVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  baseThicknessInput.addEventListener("input", (e) => {
    baseThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  cornerRadiusInput.addEventListener("input", (e) => {
    cornerRadiusVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  paddingXInput.addEventListener("input", (e) => {
    paddingXVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  paddingYInput.addEventListener("input", (e) => {
    paddingYVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  textThicknessInput.addEventListener("input", (e) => {
    textThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  holeDiameterInput.addEventListener("input", (e) => {
    holeDiameterVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  holeToggle.addEventListener("change", (e) => {
    holeOptionsWrap.style.display = e.target.checked ? "flex" : "none";
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
  extruderBaseSelect.addEventListener("change", () => triggerPreview(true));
  extruderTextSelect.addEventListener("change", () => triggerPreview(true));

  // --- Targhetta da Tavolo (Desk Sign) Event Listeners ---
  document.querySelectorAll('input[name="dsBaseMode"]').forEach((r) => {
    r.addEventListener("change", (e) => {
      dsWedgeAngleGroup.style.display = e.target.value === "wedge" ? "flex" : "none";
      triggerPreview(true);
    });
  });

  dsWedgeAngleInput.addEventListener("input", (e) => {
    dsWedgeAngleVal.textContent = `${e.target.value}°`;
    triggerPreview(false);
  });
  dsBaseThicknessInput.addEventListener("input", (e) => {
    dsBaseThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsPaddingXInput.addEventListener("input", (e) => {
    dsPaddingXVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsPaddingYInput.addEventListener("input", (e) => {
    dsPaddingYVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });

  dsText1Input.addEventListener("input", () => triggerPreview(false));
  dsFont1Select.addEventListener("change", () => triggerPreview(true));
  dsFontSize1Input.addEventListener("input", (e) => {
    dsFontSize1Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsThickness1Input.addEventListener("input", (e) => {
    dsThickness1Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsExtruderLine1Select.addEventListener("change", () => triggerPreview(true));

  dsLine2Toggle.addEventListener("change", (e) => {
    dsLine2Wrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });
  dsText2Input.addEventListener("input", () => triggerPreview(false));
  dsFont2Select.addEventListener("change", () => triggerPreview(true));
  dsFontSize2Input.addEventListener("input", (e) => {
    dsFontSize2Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsLineSpacingInput.addEventListener("input", (e) => {
    dsLineSpacingVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsThickness2Input.addEventListener("input", (e) => {
    dsThickness2Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsExtruderLine2Select.addEventListener("change", () => triggerPreview(true));

  dsBorderToggle.addEventListener("change", (e) => {
    dsBorderWrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });
  document.querySelectorAll('input[name="dsTextAlign"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  dsBorderWidthInput.addEventListener("input", (e) => {
    dsBorderWidthVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsBorderThicknessInput.addEventListener("input", (e) => {
    dsBorderThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsCornerRadiusInput.addEventListener("input", (e) => {
    dsCornerRadiusVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  dsExtruderBorderSelect.addEventListener("change", () => triggerPreview(true));

  // ==========================================
  // 5. RACCOLTA PARAMETRI PER L'API
  // ==========================================
  function getParams() {
    const palette = [colorT0.value, colorT1.value, colorT2.value, colorT3.value];
    const baseExtruder = parseInt(extruderBaseSelect.value);

    if (currentProduct === "desk_sign") {
      const baseMode = document.querySelector('input[name="dsBaseMode"]:checked')?.value || "wedge";
      const textAlign = document.querySelector('input[name="dsTextAlign"]:checked')?.value || "center";
      const font1Opt = dsFont1Select.options[dsFont1Select.selectedIndex];
      const font2Opt = dsFont2Select.options[dsFont2Select.selectedIndex];

      return {
        generator: "desk_sign",
        base_mode: baseMode,
        wedge_angle: parseFloat(dsWedgeAngleInput.value),
        base_thickness: parseFloat(dsBaseThicknessInput.value),
        corner_radius: parseFloat(dsCornerRadiusInput.value),
        padding_x: parseFloat(dsPaddingXInput.value),
        padding_y: parseFloat(dsPaddingYInput.value),
        line_spacing: parseFloat(dsLineSpacingInput.value),
        text_align: textAlign,
        text_line1: dsText1Input.value.trim() || "CHARIZARD",
        font_family_line1: dsFont1Select.value || "Arial",
        font_path_line1: font1Opt?.dataset?.path || null,
        font_size_line1: parseFloat(dsFontSize1Input.value),
        thickness_line1: parseFloat(dsThickness1Input.value),
        extruder_line1: parseInt(dsExtruderLine1Select.value),
        line2_enabled: dsLine2Toggle.checked,
        text_line2: dsText2Input.value.trim(),
        font_family_line2: dsFont2Select.value || "Arial",
        font_path_line2: font2Opt?.dataset?.path || null,
        font_size_line2: parseFloat(dsFontSize2Input.value),
        thickness_line2: parseFloat(dsThickness2Input.value),
        extruder_line2: parseInt(dsExtruderLine2Select.value),
        border_enabled: dsBorderToggle.checked,
        border_width: parseFloat(dsBorderWidthInput.value),
        border_thickness: parseFloat(dsBorderThicknessInput.value),
        extruder_border: parseInt(dsExtruderBorderSelect.value),
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
      const selectedFontOpt = fontSelect.options[fontSelect.selectedIndex];
      const textExtruder = parseInt(extruderTextSelect.value);
      let iconExtruder = parseInt(extruderIconSelect.value);
      if (iconExtruder === -1) iconExtruder = textExtruder;

      return {
        generator: "keychain",
        text: textInput.value.trim() || "NOME",
        font_family: fontSelect.value || "Arial",
        font_path: selectedFontOpt?.dataset?.path || null,
        font_size: parseFloat(fontSizeInput.value),
        letter_spacing: parseFloat(letterSpacingInput.value),
        base_style: baseStyle,
        base_thickness: parseFloat(baseThicknessInput.value),
        text_thickness: parseFloat(textThicknessInput.value),
        text_mode: textMode,
        corner_radius: parseFloat(cornerRadiusInput.value),
        padding_x: parseFloat(paddingXInput.value),
        padding_y: parseFloat(paddingYInput.value),
        hole_enabled: holeToggle.checked,
        hole_position: holePos,
        hole_diameter: parseFloat(holeDiameterInput.value),
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
      statusDot.classList.add("busy");
      statusText.textContent = "Modifica in corso...";
      debounceTimer = setTimeout(executePreview, 260);
    }
  }

  async function executePreview() {
    const params = getParams();
    statusDot.classList.add("busy");
    statusText.textContent = "Calcolo geometria 3D...";
    isRequestPending = true;

    try {
      const response = await fetch(`${API_BASE_URL}/api/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Errore di anteprima");
      }

      const data = await response.json();
      viewer.updateGeometry(data, params.filament_colors, params.extruder_base, params.extruder_text || params.extruder_line1);

      if (data.dimensions) {
        dimWidth.textContent = `${data.dimensions.width} mm`;
        dimHeight.textContent = `${data.dimensions.height} mm`;
        dimDepth.textContent = `${data.dimensions.depth} mm`;
      }

      statusDot.classList.remove("busy");
      statusText.textContent = "Pronto per la stampa";
    } catch (error) {
      console.error(error);
      statusDot.classList.remove("busy");
      statusText.textContent = "Errore di calcolo";
    } finally {
      isRequestPending = false;
    }
  }

  // ==========================================
  // 7. TOOLBAR CAMERA & WIREFRAME
  // ==========================================
  document.getElementById("btnResetView").addEventListener("click", () => viewer.resetView());
  document.getElementById("btnTopView").addEventListener("click", () => viewer.topView());
  document.getElementById("btnFrontView").addEventListener("click", () => viewer.frontView());
  document.getElementById("btnWireframe").addEventListener("click", function () {
    const isWire = viewer.toggleWireframe();
    this.classList.toggle("active", isWire);
  });

  // ==========================================
  // 8. DOWNLOAD PROGETTO 3MF
  // ==========================================
  btnGenerate.addEventListener("click", async () => {
    const params = getParams();
    btnGenerate.classList.add("loading");
    btnGenerate.innerHTML = `<span class="spinner"></span> Generazione 3MF in corso...`;

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error("Errore durante la generazione del file 3MF.");
      }

      const disposition = response.headers.get("Content-Disposition");
      let filename = currentProduct === "desk_sign"
        ? `${params.text_line1}_DeskSign_Snapmaker_U1.3mf`
        : `${params.text}_Keychain_Snapmaker_U1.3mf`;

      if (disposition && disposition.indexOf("filename=") !== -1) {
        const matches = /filename="?([^"]+)"?/.exec(disposition);
        if (matches != null && matches[1]) filename = matches[1];
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      statusText.textContent = "✓ 3MF scaricato!";
    } catch (err) {
      alert("Errore generazione 3MF: " + err.message);
    } finally {
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
});
