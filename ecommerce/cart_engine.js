/**
 * MOTORE DI CALCOLO CARRELLO, PROMOZIONE "PRENDI 3 PAGHI 2", COUPON & RITIRO A MANO
 * Snapmaker U1 E-Commerce Storefront
 */

export let CATALOG_PRICING = {
  KEYCHAIN_STANDARD: 2.90, // 1 riga, 2 colori base standard
  KEYCHAIN_COMPLEX: 3.90,  // 2 righe, oppure bicolore Silk, oppure icona 3D
  DESK_SIGN: 6.90,         // Targhetta da tavolo professionale
  EXTRA_LINE2: 2.00        // Seconda riga extra (+2.00 €)
};

export let SHIPPING_COST_FIXED = 4.90; // Corriere BRT / SDA per l'intero ordine
export let PROMO_3X2_ENABLED = true;

/**
 * Aggiorna dinamicamente i parametri di prezzo, spedizione e promo da API
 */
export function updatePricingSettings(settings) {
  if (!settings) return;
  if (typeof settings.keychain_standard === 'number') CATALOG_PRICING.KEYCHAIN_STANDARD = settings.keychain_standard;
  if (typeof settings.keychain_complex === 'number') CATALOG_PRICING.KEYCHAIN_COMPLEX = settings.keychain_complex;
  if (typeof settings.desk_sign === 'number') CATALOG_PRICING.DESK_SIGN = settings.desk_sign;
  if (typeof settings.extra_line2 === 'number') CATALOG_PRICING.EXTRA_LINE2 = settings.extra_line2;
  if (typeof settings.shipping_fixed === 'number') SHIPPING_COST_FIXED = settings.shipping_fixed;
  if (typeof settings.promo_3x2_enabled === 'boolean') PROMO_3X2_ENABLED = settings.promo_3x2_enabled;
}

/**
 * Determina il prezzo unitario del prodotto in base alle sue opzioni
 * @param {Object} itemConfig 
 * @returns {number} Prezzo in Euro
 */
export function determineItemPrice(itemConfig) {
  const isTwoLines = Boolean(itemConfig.line2Enabled || itemConfig.line2_enabled || (itemConfig.textLine2 && itemConfig.textLine2.trim()) || (itemConfig.text_line2 && itemConfig.text_line2.trim()));

  if (itemConfig.productType === 'desk_sign' || itemConfig.product_type === 'desk_sign') {
    if (isTwoLines) {
      return Math.round((CATALOG_PRICING.DESK_SIGN + (CATALOG_PRICING.EXTRA_LINE2 || 2.00)) * 100) / 100;
    }
    return CATALOG_PRICING.DESK_SIGN;
  }
  
  if (itemConfig.productType === 'keychain_complex' || itemConfig.product_type === 'keychain_complex') {
    return CATALOG_PRICING.KEYCHAIN_COMPLEX;
  }
  
  // Per i portachiavi configurati:
  const hasIcon = Boolean((itemConfig.iconId && itemConfig.iconId !== 'none') || (itemConfig.icon_name && itemConfig.icon_name !== 'none'));
  const hasCustomIconColor = Boolean(itemConfig.hasCustomIconColor || itemConfig.has_custom_icon_color);
  const isSilk = Boolean(
    (itemConfig.baseGroupName && itemConfig.baseGroupName.includes('Silk')) ||
    (itemConfig.textGroupName && itemConfig.textGroupName.includes('Silk')) ||
    (itemConfig.iconGroupName && itemConfig.iconGroupName.includes('Silk'))
  );

  if (isTwoLines || hasIcon || isSilk || hasCustomIconColor) {
    return CATALOG_PRICING.KEYCHAIN_COMPLEX;
  }

  return CATALOG_PRICING.KEYCHAIN_STANDARD;
}

/**
 * Calcola i totali del carrello applicando la promozione "Prendi 3 Paghi 2",
 * coupon sconto (% o fisso) e opzione di consegna (Corriere BRT/SDA vs Ritiro a mano gratuito).
 * 
 * @param {Array<Object>} items Lista degli articoli nel carrello
 * @param {Object} options { coupon: Object|null, deliveryMethod: 'shipping'|'pickup' }
 * @returns {Object} Dettaglio completo dei calcoli per UI e Checkout
 */
export function calculateCartSummary(items = [], options = {}) {
  const deliveryMethod = (options && options.deliveryMethod === 'pickup') ? 'pickup' : 'shipping';
  const shippingCost = deliveryMethod === 'pickup' ? 0.00 : SHIPPING_COST_FIXED;
  const shippingLabel = deliveryMethod === 'pickup' ? "Ritiro a mano di persona (0,00 €)" : "Corriere espresso (BRT / SDA)";

  if (!items || items.length === 0) {
    return {
      itemCount: 0,
      subtotal: 0.00,
      promoDiscount: 0.00,
      couponDiscount: 0.00,
      discountAmount: 0.00,
      freeItemsCount: 0,
      freeItemIndices: [],
      promoApplied: false,
      promoLabel: null,
      couponApplied: false,
      couponCode: null,
      couponLabel: null,
      deliveryMethod,
      shippingCost,
      shippingLabel,
      total: shippingCost,
      itemsWithPromo: []
    };
  }

  // 1. Mappa e calcola il prezzo di ciascun articolo
  const mappedItems = items.map((item, index) => {
    const price = typeof item.unitPrice === 'number' ? item.unitPrice : determineItemPrice(item);
    return {
      ...item,
      cartIndex: index,
      unitPrice: Math.round(price * 100) / 100,
      isFreePromo: false
    };
  });

  // 2. Calcola il subtotale lordo
  const subtotal = Math.round(mappedItems.reduce((acc, it) => acc + it.unitPrice, 0) * 100) / 100;

  // 3. Calcolo Promo 3x2
  const freeItemsCount = PROMO_3X2_ENABLED ? Math.floor(mappedItems.length / 3) : 0;
  let promoDiscount = 0.00;
  const freeItemIndices = [];

  if (freeItemsCount > 0) {
    const sortedByIndexAndPrice = [...mappedItems]
      .sort((a, b) => a.unitPrice - b.unitPrice);

    for (let i = 0; i < freeItemsCount; i++) {
      const freeItem = sortedByIndexAndPrice[i];
      promoDiscount += freeItem.unitPrice;
      freeItemIndices.push(freeItem.cartIndex);
    }
  }

  promoDiscount = Math.round(promoDiscount * 100) / 100;
  const promoApplied = freeItemsCount > 0;
  const promoLabel = promoApplied 
    ? `Promo 3x2 applicata: -${promoDiscount.toFixed(2).replace('.', ',')} € (${freeItemsCount} ${freeItemsCount === 1 ? 'articolo in omaggio' : 'articoli in omaggio'})`
    : null;

  // 4. Marca gli elementi omaggio nella lista finale
  const itemsWithPromo = mappedItems.map(it => ({
    ...it,
    isFreePromo: freeItemIndices.includes(it.cartIndex)
  }));

  const netAfterPromo = Math.max(0, Math.round((subtotal - promoDiscount) * 100) / 100);

  // 5. Calcolo Coupon Sconto
  let couponDiscount = 0.00;
  let couponApplied = false;
  let couponCode = null;
  let couponLabel = null;

  if (options && options.coupon && netAfterPromo > 0) {
    const c = options.coupon;
    const minSpend = typeof c.min_spend === 'number' ? c.min_spend : 0.0;
    if (netAfterPromo >= minSpend) {
      if (c.type === 'percentage') {
        couponDiscount = Math.round((netAfterPromo * (c.value / 100)) * 100) / 100;
      } else {
        couponDiscount = Math.min(netAfterPromo, Math.round(c.value * 100) / 100);
      }
      couponDiscount = Math.round(couponDiscount * 100) / 100;
      if (couponDiscount > 0) {
        couponApplied = true;
        couponCode = c.code ? String(c.code).toUpperCase() : '';
        couponLabel = c.type === 'percentage'
          ? `Coupon ${couponCode} (-${c.value}%): -${couponDiscount.toFixed(2).replace('.', ',')} €`
          : `Coupon ${couponCode}: -${couponDiscount.toFixed(2).replace('.', ',')} €`;
      }
    }
  }

  const totalDiscount = Math.round((promoDiscount + couponDiscount) * 100) / 100;
  const discountedSubtotal = Math.max(0, Math.round((subtotal - totalDiscount) * 100) / 100);
  const total = Math.round((discountedSubtotal + shippingCost) * 100) / 100;

  return {
    itemCount: items.length,
    subtotal,
    promoDiscount,
    couponDiscount,
    discountAmount: totalDiscount,
    freeItemsCount,
    freeItemIndices,
    promoApplied,
    promoLabel,
    couponApplied,
    couponCode,
    couponLabel,
    deliveryMethod,
    shippingCost,
    shippingLabel,
    total,
    itemsWithPromo
  };
}
