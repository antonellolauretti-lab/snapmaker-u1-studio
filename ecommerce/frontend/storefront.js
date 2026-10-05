/**
 * STOREFRONT CLIENTE E-COMMERCE & CHECKOUT SNAPMAKER U1
 * Gestione Configurazione, Three.js, Carrello con Promo 3x2 e PayPal SDK
 */

import { determineItemPrice, calculateCartSummary, SHIPPING_COST_FIXED, updatePricingSettings } from '../cart_engine.js';

export class SnapmakerStorefront {
  constructor(options = {}) {
    this.apiBaseUrl = options.apiBaseUrl || '';
    this.paypalClientId = options.paypalClientId || 'sb'; // 'sb' for sandbox default
    this.cart = [];
    this.availableFilaments = [];
    this.currentConfig = {
      productType: 'keychain', // 'keychain' o 'desk_sign'
      textLine1: 'MARCO',
      line2Enabled: false,
      textLine2: '',
      fontId: 'Montserrat',
      iconId: 'none',
      baseFilamentId: null,
      baseColorName: 'SnapSpeed PLA Black',
      baseColorHex: '#080A0D',
      baseGroupName: 'SnapSpeed PLA',
      textFilamentId: null,
      textColorName: 'SnapSpeed PLA Cool White',
      textColorHex: '#D9DFE5',
      textGroupName: 'SnapSpeed PLA'
    };

    this.curatedFonts = [
      { id: 'Montserrat', name: 'Montserrat Bold', previewText: 'MODERNO GEOMETRICO' },
      { id: 'Bebas Neue', name: 'Bebas Neue', previewText: 'ALTO IMPATTO' },
      { id: 'Pacifico', name: 'Pacifico Script', previewText: 'Elegante Corsivo' },
      { id: 'Bangers', name: 'Bangers Comic', previewText: 'STILE FUMETTO' },
      { id: 'Orbitron', name: 'Orbitron Tech', previewText: 'FUTURISTICO' },
      { id: 'Poppins', name: 'Poppins Clean', previewText: 'Morbido & Pulito' },
      { id: 'Playfair Display', name: 'Playfair Serif', previewText: 'Classico Lusso' },
      { id: 'Bungee', name: 'Bungee 3D', previewText: 'EXTRA SPESSO' }
    ];

    this.icons = [
      { id: 'none', label: 'Nessuno' },
      { id: 'heart', label: '❤️ Cuore' },
      { id: 'star', label: '⭐ Stella' },
      { id: 'paw', label: '🐾 Zampina' },
      { id: 'music', label: '🎵 Nota Musica' },
      { id: 'crown', label: '👑 Corona' },
      { id: 'fire', label: '🔥 Fiamma' }
    ];
  }

  async init() {
    await this.loadPricingSettings();
    await this.loadAvailableFilaments();
    this.renderFontSelector();
    this.renderIconSelector();
    this.renderColorSelectors();
    this.setupEventListeners();
    this.updateLivePriceBadge();
    this.renderCartUI();
  }

  async loadPricingSettings() {
    try {
      const resp = await fetch(`${this.apiBaseUrl}/api/store/pricing`);
      if (resp.ok) {
        const pricing = await resp.json();
        updatePricingSettings(pricing);
      }
    } catch (e) {
      console.warn("Impossibile caricare listino dinamico:", e);
    }
  }

  /**
   * Recupera dal backend (e Supabase) solo i filamenti attualmente contrassegnati come DISPONIBILI
   */
  async loadAvailableFilaments() {
    try {
      const resp = await fetch(`${this.apiBaseUrl}/api/store/filaments`);
      if (resp.ok) {
        const data = await resp.json();
        // Filtra solo quelli disponibili
        this.availableFilaments = data.filter(f => f.is_available);
      }
    } catch (e) {
      console.warn("Impossibile contattare Supabase per filamenti, uso catalogo locale:", e);
      // Fallback catalogo predefinito Snapmaker
      this.availableFilaments = [
        { id: 'f1', sku: '34062', name: 'SnapSpeed PLA Black', group_name: 'SnapSpeed PLA', hex_color: '#080A0D', is_available: true },
        { id: 'f2', sku: '34073', name: 'SnapSpeed PLA Cool White', group_name: 'SnapSpeed PLA', hex_color: '#D9DFE5', is_available: true },
        { id: 'f3', sku: '34065', name: 'SnapSpeed PLA Red', group_name: 'SnapSpeed PLA', hex_color: '#E72F1D', is_available: true },
        { id: 'f4', sku: '34064', name: 'SnapSpeed PLA Blue', group_name: 'SnapSpeed PLA', hex_color: '#003776', is_available: true },
        { id: 'f5', sku: '34112', name: 'SnapSpeed PLA Bright Yellow', group_name: 'SnapSpeed PLA', hex_color: '#F8F81C', is_available: true },
        { id: 'f6', sku: '34202', name: 'Silk Sunset Ember', group_name: 'Silk Dual-Color', hex_color: '#D9A63A', secondary_hex_color: '#CC434F', is_available: true }
      ];
    }
  }

  renderFontSelector() {
    const container = document.getElementById('fontSelectorContainer');
    if (!container) return;
    const userText = (this.currentConfig.textLine1 || '').trim();
    container.innerHTML = this.curatedFonts.map(f => {
      const previewText = userText || f.name;
      return `
        <label class="font-option-card ${this.currentConfig.fontId === f.id ? 'selected' : ''}">
          <input type="radio" name="fontSelection" value="${f.id}" ${this.currentConfig.fontId === f.id ? 'checked' : ''}>
          <div class="font-name">${f.name}</div>
          <div class="font-preview font-preview-text" data-font-name="${f.name}" style="font-family: '${f.id}', sans-serif;">${previewText}</div>
        </label>
      `;
    }).join('');
  }

  renderIconSelector() {
    const container = document.getElementById('iconSelectorContainer');
    if (!container) return;
    container.innerHTML = this.icons.map(ic => `
      <button type="button" class="icon-chip ${this.currentConfig.iconId === ic.id ? 'active' : ''}" data-icon="${ic.id}">
        ${ic.label}
      </button>
    `).join('');
  }

  renderColorSelectors() {
    const baseContainer = document.getElementById('baseColorSwatches');
    const textContainer = document.getElementById('textColorSwatches');
    if (!baseContainer || !textContainer) return;

    const createSwatches = (targetType, selectedHex) => {
      return this.availableFilaments.map(fil => {
        const isSelected = fil.hex_color.toLowerCase() === selectedHex.toLowerCase();
        const bgStyle = fil.secondary_hex_color
          ? `background: linear-gradient(135deg, ${fil.hex_color} 50%, ${fil.secondary_hex_color} 50%)`
          : `background: ${fil.hex_color}`;

        return `
          <div class="color-swatch-item ${isSelected ? 'selected' : ''}" 
               data-target="${targetType}"
               data-id="${fil.id}"
               data-hex="${fil.hex_color}"
               data-name="${fil.name}"
               data-group="${fil.group_name}"
               style="${bgStyle}"
               title="${fil.name} (${fil.group_name})">
            ${isSelected ? '<span class="check-mark">✓</span>' : ''}
          </div>
        `;
      }).join('');
    };

    baseContainer.innerHTML = createSwatches('base', this.currentConfig.baseColorHex);
    textContainer.innerHTML = createSwatches('text', this.currentConfig.textColorHex);
  }

  updateLivePriceBadge() {
    const badge = document.getElementById('liveItemPriceBadge');
    if (!badge) return;
    const price = determineItemPrice(this.currentConfig);
    badge.textContent = `${price.toFixed(2).replace('.', ',')} €`;
  }

  setupEventListeners() {
    // Tipo prodotto
    document.querySelectorAll('.product-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.product-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentConfig.productType = btn.dataset.product;
        this.updateLivePriceBadge();
        this.refresh3DPreview();
      });
    });

    // Testi
    const line1Input = document.getElementById('customTextLine1');
    if (line1Input) {
      line1Input.addEventListener('input', (e) => {
        this.currentConfig.textLine1 = e.target.value.toUpperCase();
        const userText = this.currentConfig.textLine1.trim();
        document.querySelectorAll('.font-preview').forEach(el => {
          const fallback = el.dataset.fontName || 'Font';
          el.textContent = userText || fallback;
        });
        this.refresh3DPreview();
      });
    }

    const line2Toggle = document.getElementById('line2Toggle');
    const line2Input = document.getElementById('customTextLine2');
    if (line2Toggle) {
      line2Toggle.addEventListener('change', (e) => {
        this.currentConfig.line2Enabled = e.target.checked;
        if (line2Input) line2Input.disabled = !e.target.checked;
        this.updateLivePriceBadge();
        this.refresh3DPreview();
      });
    }

    if (line2Input) {
      line2Input.addEventListener('input', (e) => {
        this.currentConfig.textLine2 = e.target.value;
        this.updateLivePriceBadge();
        this.refresh3DPreview();
      });
    }

    // Font selection
    document.addEventListener('change', (e) => {
      if (e.target.name === 'fontSelection') {
        this.currentConfig.fontId = e.target.value;
        this.refresh3DPreview();
      }
    });

    // Icon selection
    document.addEventListener('click', (e) => {
      const chip = e.target.closest('.icon-chip');
      if (chip) {
        document.querySelectorAll('.icon-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        this.currentConfig.iconId = chip.dataset.icon;
        this.updateLivePriceBadge();
        this.refresh3DPreview();
      }
    });

    // Swatches selection
    document.addEventListener('click', (e) => {
      const swatch = e.target.closest('.color-swatch-item');
      if (swatch) {
        const target = swatch.dataset.target;
        if (target === 'base') {
          this.currentConfig.baseFilamentId = swatch.dataset.id;
          this.currentConfig.baseColorHex = swatch.dataset.hex;
          this.currentConfig.baseColorName = swatch.dataset.name;
          this.currentConfig.baseGroupName = swatch.dataset.group;
        } else {
          this.currentConfig.textFilamentId = swatch.dataset.id;
          this.currentConfig.textColorHex = swatch.dataset.hex;
          this.currentConfig.textColorName = swatch.dataset.name;
          this.currentConfig.textGroupName = swatch.dataset.group;
        }
        this.renderColorSelectors();
        this.updateLivePriceBadge();
        this.refresh3DPreview();
      }
    });

    // Aggiungi al carrello
    const btnAddToCart = document.getElementById('btnAddToCart');
    if (btnAddToCart) {
      btnAddToCart.addEventListener('click', () => {
        this.addToCart();
      });
    }

    // Apri carrello
    const btnOpenCart = document.getElementById('btnOpenCart');
    if (btnOpenCart) {
      btnOpenCart.addEventListener('click', () => {
        this.openCartModal();
      });
    }
  }

  addToCart() {
    if (!this.currentConfig.textLine1.trim()) {
      alert("Inserisci un nome o testo per la personalizzazione!");
      return;
    }

    // Crea snapshot dell'articolo
    const price = determineItemPrice(this.currentConfig);
    const itemSnapshot = {
      id: 'cart_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
      productType: this.currentConfig.productType,
      productTitle: this.currentConfig.productType === 'desk_sign' ? 'Targhetta da Tavolo' : 'Portachiavi Personalizzato',
      unitPrice: price,
      customTextLine1: this.currentConfig.textLine1,
      customTextLine2: this.currentConfig.line2Enabled ? this.currentConfig.textLine2 : '',
      fontId: this.currentConfig.fontId,
      iconId: this.currentConfig.iconId,
      baseFilamentId: this.currentConfig.baseFilamentId,
      baseColorName: this.currentConfig.baseColorName,
      baseColorHex: this.currentConfig.baseColorHex,
      textFilamentId: this.currentConfig.textFilamentId,
      textColorName: this.currentConfig.textColorName,
      textColorHex: this.currentConfig.textColorHex,
      // Salva parametri completi per generatore nativo Snapmaker 3MF
      generatorParams: {
        generator: this.currentConfig.productType,
        text: this.currentConfig.textLine1,
        text_line1: this.currentConfig.textLine1,
        line2_enabled: this.currentConfig.line2Enabled,
        text_line2: this.currentConfig.textLine2,
        font_family: this.currentConfig.fontId,
        icon_id: this.currentConfig.iconId,
        base_color: this.currentConfig.baseColorHex,
        text_color: this.currentConfig.textColorHex
      }
    };

    this.cart.push(itemSnapshot);
    this.renderCartUI();
    this.openCartModal();
  }

  removeFromCart(index) {
    this.cart.splice(index, 1);
    this.renderCartUI();
  }

  renderCartUI() {
    const summary = calculateCartSummary(this.cart);

    // Badge quantità
    const badge = document.getElementById('cartCounterBadge');
    if (badge) {
      badge.textContent = summary.itemCount;
      badge.style.display = summary.itemCount > 0 ? 'inline-flex' : 'none';
    }

    // Lista articoli nel drawer/modal
    const listContainer = document.getElementById('cartItemsList');
    if (!listContainer) return;

    if (summary.itemCount === 0) {
      listContainer.innerHTML = `
        <div class="empty-cart-state">
          <div style="font-size: 40px; margin-bottom: 12px;">🛒</div>
          <p>Il tuo carrello è vuoto.</p>
          <small>Configura un portachiavi o una targhetta e aggiungila qui!</small>
        </div>
      `;
    } else {
      listContainer.innerHTML = summary.itemsWithPromo.map((it, idx) => `
        <div class="cart-item-row ${it.isFreePromo ? 'free-promo-item' : ''}">
          <div class="cart-item-info">
            <div class="cart-item-title">
              ${it.productTitle}
              ${it.isFreePromo ? '<span class="promo-omaggio-tag">100% OMAGGIO 3x2</span>' : ''}
            </div>
            <div class="cart-item-sub">
              Testo: <strong>${it.customTextLine1}</strong> (Font: ${it.fontId})
              ${it.customTextLine2 ? ` - Riga 2: <em>${it.customTextLine2}</em>` : ''}
            </div>
            <div class="cart-item-colors">
              Base: <span class="color-dot" style="background:${it.baseColorHex};"></span>${it.baseColorName} | 
              Scritta: <span class="color-dot" style="background:${it.textColorHex};"></span>${it.textColorName}
            </div>
          </div>
          <div class="cart-item-right">
            <div class="cart-item-price">
              ${it.isFreePromo ? `<s>${it.unitPrice.toFixed(2).replace('.', ',')} €</s> <span class="free-text">0,00 €</span>` : `${it.unitPrice.toFixed(2).replace('.', ',')} €`}
            </div>
            <button type="button" class="btn-remove-item" data-index="${idx}" title="Rimuovi">&times;</button>
          </div>
        </div>
      `).join('');

      // Event listener rimozione
      listContainer.querySelectorAll('.btn-remove-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const idx = parseInt(e.target.dataset.index, 10);
          this.removeFromCart(idx);
        });
      });
    }

    // Riepilogo Economico
    const subtotalEl = document.getElementById('cartSubtotalAmount');
    if (subtotalEl) subtotalEl.textContent = `${summary.subtotal.toFixed(2).replace('.', ',')} €`;

    // Riga Promo 3x2
    const promoRowEl = document.getElementById('cartPromoRow');
    if (promoRowEl) {
      if (summary.promoApplied) {
        promoRowEl.style.display = 'flex';
        promoRowEl.innerHTML = `
          <span class="promo-highlight-text">🎉 ${summary.promoLabel}</span>
          <span class="promo-discount-val">-${summary.discountAmount.toFixed(2).replace('.', ',')} €</span>
        `;
      } else {
        promoRowEl.style.display = 'none';
      }
    }

    // Spedizione
    const shippingEl = document.getElementById('cartShippingAmount');
    if (shippingEl) shippingEl.textContent = `${summary.shippingCost.toFixed(2).replace('.', ',')} €`;

    // Totale
    const totalEl = document.getElementById('cartTotalAmount');
    if (totalEl) totalEl.textContent = `${summary.total.toFixed(2).replace('.', ',')} €`;

    // Se il carrello ha articoli, inizializza o aggiorna PayPal SDK
    if (summary.itemCount > 0) {
      this.initPayPalSmartButtons(summary);
    }
  }

  /**
   * Inizializzazione PayPal Smart Buttons SDK
   */
  initPayPalSmartButtons(summary) {
    const container = document.getElementById('paypal-button-container');
    if (!container) return;

    // Se l'SDK di PayPal non è ancora caricato dinamicamente, caricalo
    if (!window.paypal) {
      const script = document.createElement('script');
      script.src = `https://www.paypal.com/sdk/js?client-id=${this.paypalClientId}&currency=EUR&locale=it_IT&components=buttons`;
      script.async = true;
      script.onload = () => {
        this.renderPayPalButtons(summary);
      };
      document.body.appendChild(script);
    } else {
      this.renderPayPalButtons(summary);
    }
  }

  renderPayPalButtons(summary) {
    const container = document.getElementById('paypal-button-container');
    if (!container) return;
    container.innerHTML = ''; // Reset container

    window.paypal.Buttons({
      style: {
        layout: 'vertical',
        color: 'gold',
        shape: 'rect',
        label: 'pay'
      },

      // Validazione form checkout prima di aprire PayPal
      onClick: (data, actions) => {
        const form = document.getElementById('checkoutForm');
        if (form && !form.checkValidity()) {
          form.reportValidity();
          return actions.reject();
        }
        return actions.resolve();
      },

      // 1. Creazione ordine
      createOrder: async (data, actions) => {
        const customerInfo = this.getCheckoutFormData();
        
        // Chiama endpoint backend per generare l'ordine PayPal in sicurezza
        try {
          const resp = await fetch(`${this.apiBaseUrl}/api/store/orders/create-paypal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              items: this.cart,
              customerInfo
            })
          });

          if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "Errore creazione ordine PayPal");
          }

          const orderData = await resp.json();
          return orderData.id; // Restituisce il PayPal Order ID
        } catch (e) {
          alert(`Errore Checkout: ${e.message}`);
          throw e;
        }
      },

      // 2. Cattura pagamento avvenuto
      onApprove: async (data, actions) => {
        const customerInfo = this.getCheckoutFormData();
        try {
          const resp = await fetch(`${this.apiBaseUrl}/api/store/orders/capture-paypal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              paypalOrderId: data.orderID,
              items: this.cart,
              customerInfo
            })
          });

          if (!resp.ok) {
            throw new Error("Errore durante la registrazione dell'ordine");
          }

          const result = await resp.json();
          // Svuota carrello e mostra schermata di successo
          this.cart = [];
          this.renderCartUI();
          this.showOrderSuccessScreen(result);
        } catch (e) {
          alert(`Errore cattura pagamento: ${e.message}`);
        }
      },

      onError: (err) => {
        console.error("Errore PayPal Smart Buttons:", err);
        alert("Si è verificato un errore con PayPal. Riprova o scegli un altro metodo di pagamento.");
      }
    }).render('#paypal-button-container');
  }

  getCheckoutFormData() {
    return {
      customer_name: (document.getElementById('shippingFullName')?.value || '').trim(),
      customer_email: (document.getElementById('shippingEmail')?.value || '').trim(),
      customer_phone: (document.getElementById('shippingPhone')?.value || '').trim(),
      shipping_address: (document.getElementById('shippingAddress')?.value || '').trim(),
      shipping_city: (document.getElementById('shippingCity')?.value || '').trim(),
      shipping_zip: (document.getElementById('shippingZip')?.value || '').trim(),
      shipping_province: (document.getElementById('shippingProvince')?.value || '').trim().toUpperCase(),
      order_notes: (document.getElementById('shippingNotes')?.value || '').trim()
    };
  }

  showOrderSuccessScreen(orderResult) {
    const modal = document.getElementById('checkoutModal');
    if (modal) modal.style.display = 'none';

    const successContainer = document.getElementById('orderConfirmationView');
    if (successContainer) {
      successContainer.style.display = 'block';
      successContainer.innerHTML = `
        <div class="order-success-card">
          <div class="success-icon">🎉</div>
          <h2>Grazie per il tuo ordine!</h2>
          <p class="order-code">Codice Ordine: <strong>#${orderResult.order_number}</strong></p>
          <p>Abbiamo inviato un'email di conferma con tutti i dettagli a <strong>${orderResult.customer_email}</strong>.</p>
          <div class="success-steps">
            <div>1. 🖨️ Stampa 3D ad alta precisione con Snapmaker U1 in avvio</div>
            <div>2. 📦 Imballaggio e affidamento a Corriere Espresso (BRT / SDA)</div>
            <div>3. 🚚 Riceverai un SMS/Email con il codice di tracciamento BRT/SDA</div>
          </div>
          <button type="button" class="btn-primary" onclick="window.location.reload()">Crea un altro modello</button>
        </div>
      `;
    }
  }

  openCartModal() {
    const modal = document.getElementById('cartDrawer');
    if (modal) modal.classList.add('open');
  }

  refresh3DPreview() {
    // Richiama l'engine Three.js esistente con i parametri attuali
    if (window.U1Viewer && typeof window.U1Viewer.renderFromConfig === 'function') {
      window.U1Viewer.renderFromConfig(this.currentConfig);
    }
  }
}
