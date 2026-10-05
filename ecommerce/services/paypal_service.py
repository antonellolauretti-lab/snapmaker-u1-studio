"""
Integrazione PayPal SDK & REST API v2 per Storefront Snapmaker U1
Gestisce la creazione degli ordini con dettaglio sconti (Promo 3x2) e la cattura sicura del pagamento.
Destinatario/Payee: antonello.lauretti@gmail.com
"""
import os
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, List
from decimal import Decimal

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ecommerce.cart_engine import calculate_cart_totals

def get_paypal_config() -> Dict[str, str]:
    """Recupera la configurazione PayPal corrente dall'ambiente con fallback sicuri."""
    mode = os.environ.get("PAYPAL_MODE", "sandbox").strip().lower()
    client_id = os.environ.get("PAYPAL_CLIENT_ID", "").strip()
    client_secret = (os.environ.get("PAYPAL_CLIENT_SECRET") or os.environ.get("PAYPAL_SECRET") or "").strip()
    payee_email = (os.environ.get("PAYPAL_PAYEE_EMAIL") or "antonello.lauretti@gmail.com").strip()
    base_url = "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"
    return {
        "mode": mode,
        "client_id": client_id,
        "client_secret": client_secret,
        "payee_email": payee_email,
        "base_url": base_url
    }

def _get_access_token() -> str:
    """Ottiene un token Bearer OAuth2 da PayPal."""
    cfg = get_paypal_config()
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise ValueError(
            "PAYPAL_CLIENT_ID e PAYPAL_CLIENT_SECRET (o PAYPAL_SECRET) devono essere configurati nelle variabili d'ambiente."
        )

    url = f"{cfg['base_url']}/v1/oauth2/token"
    auth_str = f"{cfg['client_id']}:{cfg['client_secret']}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = b"grant_type=client_credentials"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["access_token"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        raise RuntimeError(f"Errore autenticazione PayPal [{cfg['mode']}] ({e.code}): {err_msg}")

def create_paypal_order(items: List[Dict[str, Any]], customer_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea l'ordine PayPal lato server con la composizione esatta:
    - Subtotale articoli
    - Sconto Promo 3x2 (discount)
    - Spedizione fissa Corriere BRT/SDA: 5,00 €
    - Destinatario: antonello.lauretti@gmail.com
    """
    totals = calculate_cart_totals(items)
    
    subtotal_str = f"{totals['subtotal']:.2f}"
    discount_str = f"{totals['discount_amount']:.2f}"
    shipping_str = f"{totals['shipping_amount']:.2f}"
    total_str = f"{totals['total_amount']:.2f}"

    item_breakdown_list = []
    for it in totals["items"]:
        raw = it["raw"]
        title = raw.get("product_title") or raw.get("productTitle") or (
            "Targhetta da Tavolo" if "desk_sign" in str(raw.get("product_type") or raw.get("productType")).lower() else "Portachiavi Personalizzato"
        )
        item_breakdown_list.append({
            "name": str(title)[:120],
            "description": f"Testo: {raw.get('custom_text_line1', '')} - Base: {raw.get('base_color_name', '')} - Testo: {raw.get('text_color_name', '')}"[:120],
            "unit_amount": {
                "currency_code": "EUR",
                "value": f"{it['unit_price']:.2f}"
            },
            "quantity": "1",
            "category": "PHYSICAL_GOODS"
        })

    cfg = get_paypal_config()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": "GADGETPOINT_ORDER",
                "payee": {
                    "email_address": cfg["payee_email"]
                },
                "description": "Ordine Oggetti Personalizzati GadgetPoint.it",
                "amount": {
                    "currency_code": "EUR",
                    "value": total_str,
                    "breakdown": {
                        "item_total": {
                            "currency_code": "EUR",
                            "value": subtotal_str
                        },
                        "discount": {
                            "currency_code": "EUR",
                            "value": discount_str
                        },
                        "shipping": {
                            "currency_code": "EUR",
                            "value": shipping_str
                        }
                    }
                },
                "items": item_breakdown_list,
                "shipping": {
                    "name": {
                        "full_name": customer_info.get("customer_name", "Cliente")
                    },
                    "address": {
                        "address_line_1": customer_info.get("shipping_address", ""),
                        "admin_area_2": customer_info.get("shipping_city", ""),
                        "admin_area_1": customer_info.get("shipping_province", ""),
                        "postal_code": customer_info.get("shipping_zip", ""),
                        "country_code": "IT"
                    }
                }
            }
        ],
        "application_context": {
            "brand_name": "GadgetPoint.it",
            "locale": "it-IT",
            "landing_page": "NO_PREFERENCE",
            "shipping_preference": "SET_PROVIDED_ADDRESS",
            "user_action": "PAY_NOW"
        }
    }

    token = _get_access_token()
    url = f"{cfg['base_url']}/v2/checkout/orders"
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_body = json.loads(resp.read().decode("utf-8"))
            return res_body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"Errore creazione ordine PayPal ({e.code}): {err_body}")

def capture_paypal_order(paypal_order_id: str) -> Dict[str, Any]:
    """Cattura il pagamento di un ordine approvato dal cliente."""
    cfg = get_paypal_config()
    token = _get_access_token()
    url = f"{cfg['base_url']}/v2/checkout/orders/{paypal_order_id}/capture"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            capture_res = json.loads(resp.read().decode("utf-8"))
            return capture_res
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"Errore cattura pagamento PayPal ({e.code}): {err_body}")
