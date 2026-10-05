"""
Modulo backend per la convalida dei prezzi, calcolo del carrello con Promozione 3x2,
gestione codici Coupon sconto e opzioni di consegna (Spedizione vs Ritiro a mano).
Garantisce che l'importo inviato a PayPal e registrato nel database sia matematicamente certo.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

DATA_DIR = Path(__file__).resolve().parent / "data"
PRICING_FILE = DATA_DIR / "pricing_settings.json"
COUPONS_FILE = DATA_DIR / "coupons.json"

def get_pricing_settings() -> Dict[str, Any]:
    defaults = {
        "keychain_standard": 2.90,
        "keychain_complex": 3.90,
        "desk_sign": 6.90,
        "extra_line2": 2.00,
        "shipping_fixed": 4.90,
        "promo_3x2_enabled": True
    }
    if PRICING_FILE.exists() and PRICING_FILE.stat().st_size > 0:
        try:
            with open(PRICING_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults

def get_coupons() -> List[Dict[str, Any]]:
    """Carica la lista dei coupon registrati dal file JSON."""
    if COUPONS_FILE.exists() and COUPONS_FILE.stat().st_size > 0:
        try:
            with open(COUPONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("coupons", [])
        except Exception:
            pass
    return []

def save_coupons(coupons: List[Dict[str, Any]]):
    """Salva i coupon nel file JSON dedicato."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(COUPONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"coupons": coupons}, f, indent=2, ensure_ascii=False)

def validate_coupon_code(code: str, net_subtotal: Decimal) -> Dict[str, Any]:
    """
    Verifica la validità di un codice coupon rispetto al subtotale della merce.
    Ritorna { valid: bool, coupon: dict, discount_amount: Decimal, message: str }.
    """
    if not code:
        return {"valid": False, "message": "Nessun codice coupon specificato."}
    
    clean_code = str(code).strip().upper()
    coupons = get_coupons()
    coupon = next((c for c in coupons if str(c.get("code", "")).strip().upper() == clean_code), None)
    
    if not coupon:
        return {"valid": False, "message": f"Il codice coupon '{clean_code}' non esiste."}
    
    if not coupon.get("active", True):
        return {"valid": False, "message": f"Il coupon '{clean_code}' non è attivo o è scaduto."}
    
    min_spend = Decimal(str(coupon.get("min_spend", 0.0)))
    if net_subtotal < min_spend:
        return {
            "valid": False,
            "message": f"Spesa minima richiesta per il coupon {clean_code}: {min_spend:.2f} € (Carrello attuale: {net_subtotal:.2f} €)."
        }
    
    c_type = str(coupon.get("type", "percentage")).lower()
    c_val = Decimal(str(coupon.get("value", 0.0)))
    
    if c_type == "percentage":
        discount = (net_subtotal * (c_val / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        discount = min(net_subtotal, c_val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    return {
        "valid": True,
        "coupon": coupon,
        "discount_amount": discount,
        "message": f"Coupon {clean_code} applicato con successo!"
    }

def determine_item_price(item: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> Decimal:
    """Calcola il prezzo unitario esatto in base alla tipologia di prodotto e al listino dinamico."""
    if settings is None:
        settings = get_pricing_settings()

    price_desk_sign = Decimal(str(settings.get("desk_sign", 6.90)))
    price_keychain_complex = Decimal(str(settings.get("keychain_complex", 3.90)))
    price_keychain_standard = Decimal(str(settings.get("keychain_standard", 2.90)))

    product_type = str(item.get("productType") or item.get("product_type") or "").lower()
    if product_type in ["desk_sign", "targhetta"]:
        return price_desk_sign
    
    if product_type in ["keychain_complex", "portachiavi_complesso"]:
        return price_keychain_complex
    
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
        return price_keychain_complex
    
    return price_keychain_standard

def calculate_cart_totals(
    items: List[Dict[str, Any]],
    coupon_code: Optional[str] = None,
    delivery_method: str = "shipping"
) -> Dict[str, Any]:
    """
    Calcola Subtotale, Sconto Promo 3x2, Sconto Coupon, Spedizione (o Ritiro gratuito) e Totale finale.
    Regola 3x2: ogni 3 pezzi, il pezzo meno costoso tra i 3 viene scontato al 100%.
    Regola Coupon: applicato sulla merce rimanente al netto della promo 3x2.
    """
    settings = get_pricing_settings()
    shipping_fixed = Decimal(str(settings.get("shipping_fixed", 4.90)))
    promo_enabled = bool(settings.get("promo_3x2_enabled", True))

    is_pickup = str(delivery_method).strip().lower() in ["pickup", "ritiro", "ritiro_a_mano", "ritiro_in_sede"]
    shipping_amount = Decimal("0.00") if is_pickup else shipping_fixed
    shipping_label = "Ritiro a mano di persona (0,00 €)" if is_pickup else "Corriere espresso (BRT / SDA)"

    if not items:
        return {
            "item_count": 0,
            "subtotal": Decimal("0.00"),
            "promo_discount": Decimal("0.00"),
            "coupon_discount": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "shipping_amount": shipping_amount,
            "shipping_label": shipping_label,
            "total_amount": shipping_amount,
            "free_items_count": 0,
            "promo_applied": False,
            "promo_label": "",
            "coupon_applied": False,
            "coupon_code": None,
            "coupon_label": "",
            "delivery_method": "pickup" if is_pickup else "shipping",
            "items": []
        }

    evaluated_items = []
    for idx, raw_item in enumerate(items):
        price = determine_item_price(raw_item, settings)
        evaluated_items.append({
            "cart_index": idx,
            "raw": raw_item,
            "unit_price": price,
            "is_free_promo": False
        })

    subtotal = sum(it["unit_price"] for it in evaluated_items)
    free_count = (len(evaluated_items) // 3) if promo_enabled else 0
    promo_discount = Decimal("0.00")
    free_indices = set()

    if free_count > 0:
        # Ordina per prezzo crescente
        sorted_by_price = sorted(evaluated_items, key=lambda x: x["unit_price"])
        for i in range(free_count):
            free_item = sorted_by_price[i]
            promo_discount += free_item["unit_price"]
            free_indices.add(free_item["cart_index"])

    for it in evaluated_items:
        if it["cart_index"] in free_indices:
            it["is_free_promo"] = True

    net_after_promo = max(Decimal("0.00"), subtotal - promo_discount)

    # Calcolo Coupon
    coupon_discount = Decimal("0.00")
    coupon_applied = False
    coupon_label = ""
    valid_coupon_code = None

    if coupon_code and net_after_promo > Decimal("0.00"):
        c_check = validate_coupon_code(coupon_code, net_after_promo)
        if c_check["valid"]:
            coupon_discount = c_check["discount_amount"]
            coupon_applied = True
            valid_coupon_code = str(coupon_code).strip().upper()
            c_data = c_check["coupon"]
            if str(c_data.get("type")).lower() == "percentage":
                coupon_label = f"Coupon {valid_coupon_code} (-{float(c_data.get('value')):.0f}%): -{coupon_discount:.2f} €"
            else:
                coupon_label = f"Coupon {valid_coupon_code}: -{coupon_discount:.2f} €"

    total_discount = promo_discount + coupon_discount
    discounted_subtotal = max(Decimal("0.00"), subtotal - total_discount)
    total_amount = discounted_subtotal + shipping_amount

    promo_label = (
        f"Promo 3x2 applicata: -{promo_discount:.2f} € ({free_count} articolo in omaggio)"
        if free_count == 1
        else (f"Promo 3x2 applicata: -{promo_discount:.2f} € ({free_count} articoli in omaggio)" if free_count > 1 else "")
    )

    return {
        "item_count": len(evaluated_items),
        "subtotal": subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "promo_discount": promo_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "coupon_discount": coupon_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "discount_amount": total_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "shipping_amount": shipping_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "shipping_label": shipping_label,
        "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "free_items_count": free_count,
        "promo_applied": free_count > 0,
        "promo_label": promo_label,
        "coupon_applied": coupon_applied,
        "coupon_code": valid_coupon_code,
        "coupon_label": coupon_label,
        "delivery_method": "pickup" if is_pickup else "shipping",
        "items": evaluated_items
    }
