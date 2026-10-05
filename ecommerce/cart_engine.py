"""
Modulo backend per la convalida dei prezzi e il calcolo del carrello con Promozione 3x2.
Garantisce che l'importo inviato a PayPal e registrato su Supabase sia matematicamente certo.
"""
from typing import List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

PRICE_KEYCHAIN_STANDARD = Decimal("4.90")
PRICE_KEYCHAIN_COMPLEX = Decimal("6.90")
PRICE_DESK_SIGN = Decimal("9.90")
SHIPPING_FIXED_BRT_SDA = Decimal("5.00")

def determine_item_price(item: Dict[str, Any]) -> Decimal:
    """Calcola il prezzo unitario esatto in base alla tipologia di prodotto."""
    product_type = str(item.get("productType") or item.get("product_type") or "").lower()
    if product_type in ["desk_sign", "targhetta"]:
        return PRICE_DESK_SIGN
    
    if product_type in ["keychain_complex", "portachiavi_complesso"]:
        return PRICE_KEYCHAIN_COMPLEX
    
    # Portachiavi
    line2_enabled = bool(item.get("line2Enabled") or item.get("line2_enabled"))
    text_line2 = (item.get("textLine2") or item.get("text_line2") or "").strip()
    has_line2 = line2_enabled and len(text_line2) > 0
    
    icon_id = (item.get("iconId") or item.get("icon_id") or item.get("icon_name") or "").strip()
    has_icon = bool(icon_id and icon_id.lower() not in ("none", ""))
    has_custom_icon_color = bool(item.get("hasCustomIconColor") or item.get("has_custom_icon_color"))
    
    base_group = (item.get("baseGroupName") or item.get("base_group_name") or "")
    text_group = (item.get("textGroupName") or item.get("text_group_name") or "")
    icon_group = (item.get("iconGroupName") or item.get("icon_group_name") or "")
    is_silk = "silk" in base_group.lower() or "silk" in text_group.lower() or "silk" in icon_group.lower()

    if has_line2 or has_icon or is_silk or has_custom_icon_color:
        return PRICE_KEYCHAIN_COMPLEX
    
    return PRICE_KEYCHAIN_STANDARD

def calculate_cart_totals(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcola Subtotale, Sconto 3x2, Spedizione fissa e Totale finale.
    Regola 3x2: ogni 3 pezzi, il pezzo meno costoso tra i 3 viene scontato al 100%.
    """
    if not items:
        return {
            "item_count": 0,
            "subtotal": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "shipping_amount": Decimal("0.00"),
            "total_amount": Decimal("0.00"),
            "free_items_count": 0,
            "promo_applied": False,
            "promo_label": "",
            "items": []
        }

    evaluated_items = []
    for idx, raw_item in enumerate(items):
        price = determine_item_price(raw_item)
        evaluated_items.append({
            "cart_index": idx,
            "raw": raw_item,
            "unit_price": price,
            "is_free_promo": False
        })

    subtotal = sum(it["unit_price"] for it in evaluated_items)
    free_count = len(evaluated_items) // 3
    discount_amount = Decimal("0.00")
    free_indices = set()

    if free_count > 0:
        # Ordina per prezzo crescente
        sorted_by_price = sorted(evaluated_items, key=lambda x: x["unit_price"])
        for i in range(free_count):
            free_item = sorted_by_price[i]
            discount_amount += free_item["unit_price"]
            free_indices.add(free_item["cart_index"])

    for it in evaluated_items:
        if it["cart_index"] in free_indices:
            it["is_free_promo"] = True

    discounted_subtotal = max(Decimal("0.00"), subtotal - discount_amount)
    shipping_amount = SHIPPING_FIXED_BRT_SDA
    total_amount = discounted_subtotal + shipping_amount

    promo_label = (
        f"Promo 3x2 applicata: -{discount_amount:.2f} € ({free_count} articolo in omaggio)"
        if free_count == 1
        else (f"Promo 3x2 applicata: -{discount_amount:.2f} € ({free_count} articoli in omaggio)" if free_count > 1 else "")
    )

    return {
        "item_count": len(evaluated_items),
        "subtotal": subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "discount_amount": discount_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "shipping_amount": shipping_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "free_items_count": free_count,
        "promo_applied": free_count > 0,
        "promo_label": promo_label,
        "items": evaluated_items
    }
