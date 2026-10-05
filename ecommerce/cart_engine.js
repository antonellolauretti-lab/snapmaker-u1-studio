/**
 * MOTORE DI CALCOLO CARRELLO & PROMOZIONE "PRENDI 3 PAGHI 2"
 * Snapmaker U1 E-Commerce Storefront
 */

export let CATALOG_PRICING = {
  KEYCHAIN_STANDARD: 4.90, // 1 riga, 2 colori base standard
  KEYCHAIN_COMPLEX: 6.90,  // 2 righe, oppure bicolore Silk, oppure icona 3D
  DESK_SIGN: 9.90          // Targhetta da tavolo professionale
};

export let SHIPPING_COST_FIXED = 5.00; // Corriere BRT / SDA per l'intero ordine
export let PROMO_3X2_ENABLED = true;

/**
 * Aggiorna dinamicamente i parametri di prezzo, spedizione e promo da API
 */
export function updatePricingSettings(settings) {
  if (!settings) return;
  if (typeof settings.keychain_standard === 'number') CATALOG_PRICING.KEYCHAIN_STANDARD = settings.keychain_standard;
  if (typeof settings.keychain_complex === 'number') CATALOG_PRICING.KEYCHAIN_COMPLEX = settings.keychain_complex;
  if (typeof settings.desk_sign === 'number') CATALOG_PRICING.DESK_SIGN = settings.desk_sign;
  if (typeof settings.shipping_fixed === 'number') SHIPPING_COST_FIXED = settings.shipping_fixed;
  if (typeof settings.promo_3x2_enabled === 'boolean') PROMO_3X2_ENABLED = settings.promo_3x2_enabled;
}

/**
 * Determina il prezzo unitario del prodotto in base alle sue opzioni
 * @param {Object} itemConfig 
 * @returns {number} Prezzo in Euro (4.90, 6.90 o 9.90)
 */
export function determineItemPrice(itemConfig) {
  if (itemConfig.productType === 'desk_sign' || itemConfig.product_type === 'desk_sign') {
    return CATALOG_PRICING.DESK_SIGN;
  }
  
  if (itemConfig.productType === 'keychain_complex' || itemConfig.product_type === 'keychain_complex') {
    return CATALOG_PRICING.KEYCHAIN_COMPLEX;
  }
  
  // Per i portachiavi configurati:
  const isTwoLines = Boolean(itemConfig.line2Enabled && itemConfig.textLine2 && itemConfig.textLine2.trim()) ||
                     Boolean(itemConfig.line2_enabled && itemConfig.text_line2 && itemConfig.text_line2.trim());
  const hasIcon = Boolean((itemConfig.iconId && itemConfig.iconId !== 'none') || (itemConfig.icon_name && itemConfig.icon_name !== 'none'));
  const hasCustomIconColor = Boolean(itemConfig.hasCustomIconColor || itemConfig.has_custom_icon_color);
  const isSilk = Boolean(
    (itemConfig.baseGroupName && itemConfig.baseGroupName.includes('Silk')) ||
    (itemConfig.textGroupName && itemConfig.textGroupName.includes('Silk')) ||
    (itemConfig.iconGroupName && itemConfig.iconGroupName.includes('Silk'))
  );

  if (isTwoLines || hasIcon || isSilk || hasCustomIconColor) {
    return CATALOG_PRICING.KEYCHAIN_COMPLEX; // 6.90 €
  }

  return CATALOG_PRICING.KEYCHAIN_STANDARD; // 4.90 €
}

/**
 * Calcola i totali del carrello applicando la promozione "Prendi 3 Paghi 2"
 * e la tariffa fissa di spedizione con corriere espresso BRT/SDA.
 * 
 * Regola 3x2:
 * Per ogni terzina di articoli presenti nel carrello (floor(N / 3)), 
 * l'articolo meno caro di ciascuna terzina viene scontato al 100% (gratis).
 * Questo equivale ad ordinare tutti gli articoli per prezzo crescente
 * e azzerare il costo dei primi floor(N / 3) articoli.
 * 
 * @param {Array<Object>} items Lista degli articoli nel carrello
 * @returns {Object} Dettaglio completo dei calcoli per UI e Checkout
 */
export function calculateCartSummary(items = []) {
  if (!items || items.length === 0) {
    return {
      itemCount: 0,
      subtotal: 0.00,
      discountAmount: 0.00,
      freeItemsCount: 0,
      freeItemIndices: [],
      promoApplied: false,
      promoLabel: null,
      shippingCost: 0.00,
      shippingLabel: "Corriere espresso (BRT / SDA)",
      total: 0.00,
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
  const subtotal = mappedItems.reduce((acc, it) => acc + it.unitPrice, 0);

  // 3. Calcolo Promo 3x2
  // Numero di pezzi in omaggio: 1 ogni 3 (se la promozione è attiva)
  const freeItemsCount = PROMO_3X2_ENABLED ? Math.floor(mappedItems.length / 3) : 0;
  let discountAmount = 0.00;
  const freeItemIndices = [];

  if (freeItemsCount > 0) {
    // Ordina una copia degli elementi per prezzo crescente (dal più economico al più costoso)
    const sortedByIndexAndPrice = [...mappedItems]
      .sort((a, b) => a.unitPrice - b.unitPrice);

    // I primi 'freeItemsCount' articoli più economici sono scontati al 100%
    for (let i = 0; i < freeItemsCount; i++) {
      const freeItem = sortedByIndexAndPrice[i];
      discountAmount += freeItem.unitPrice;
      freeItemIndices.push(freeItem.cartIndex);
    }
  }

  // Arrotonda sconti
  discountAmount = Math.round(discountAmount * 100) / 100;
  const promoApplied = freeItemsCount > 0;
  const promoLabel = promoApplied 
    ? `Promo 3x2 applicata: -${discountAmount.toFixed(2).replace('.', ',')} € (${freeItemsCount} ${freeItemsCount === 1 ? 'articolo in omaggio' : 'articoli in omaggio'})`
    : null;

  // 4. Marca gli elementi omaggio nella lista finale
  const itemsWithPromo = mappedItems.map(it => ({
    ...it,
    isFreePromo: freeItemIndices.includes(it.cartIndex)
  }));

  // 5. Spedizione fissa
  const shippingCost = SHIPPING_COST_FIXED;

  // 6. Totale finale
  const discountedSubtotal = Math.max(0, subtotal - discountAmount);
  const total = Math.round((discountedSubtotal + shippingCost) * 100) / 100;

  return {
    itemCount: items.length,
    subtotal: Math.round(subtotal * 100) / 100,
    discountAmount,
    freeItemsCount,
    freeItemIndices,
    promoApplied,
    promoLabel,
    shippingCost,
    shippingLabel: "Corriere espresso (BRT / SDA)",
    total,
    itemsWithPromo
  };
}
