"""
Integrazione PayPal SDK & REST API v2 per Storefront Snapmaker U1
Gestisce la creazione degli ordini con dettaglio sconti (Promo 3x2) e la cattura sicura del pagamento.
Destinatario/Payee: antonello.lauretti@gmail.com
"""
import os
import json
import base64
import logging
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

logger = logging.getLogger("paypal_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [PayPal] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
    """Ottiene un token Bearer OAuth2 da PayPal con logging dettagliato."""
    cfg = get_paypal_config()
    if not cfg["client_id"] or not cfg["client_secret"]:
        err_msg = "PAYPAL_CLIENT_ID e PAYPAL_CLIENT_SECRET (o PAYPAL_SECRET) devono essere configurati nelle variabili d'ambiente."
        logger.error(f"Errore configurazione credenziali: {err_msg}")
        raise ValueError(err_msg)

    url = f"{cfg['base_url']}/v1/oauth2/token"
    logger.info(f"Richiesta token OAuth2 PayPal: {url} | Mode: {cfg['mode']} | ClientId: {cfg['client_id'][:8]}...")
    
    auth_str = f"{cfg['client_id']}:{cfg['client_secret']}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = b"grant_type=client_credentials"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            token = body.get("access_token")
            logger.info("Token OAuth2 PayPal ottenuto con successo.")
            return token
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        logger.error(f"PayPal OAuth Error [{cfg['mode']}] (HTTP {e.code}): {err_msg}")
        raise RuntimeError(f"Errore autenticazione PayPal [{cfg['mode']}] ({e.code}): {err_msg}")
    except Exception as e:
        logger.error(f"PayPal OAuth Unexpected Exception: {str(e)}")
        raise

def create_paypal_order(items: List[Dict[str, Any]], customer_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea l'ordine PayPal lato server con la composizione esatta:
    - Subtotale articoli
    - Sconto Promo 3x2 (discount, solo se > 0)
    - Spedizione fissa Corriere BRT/SDA
    - Destinatario: antonello.lauretti@gmail.com
    Formattazione rigorosa a 2 decimali come stringa (es. '7.80').
    """
    totals = calculate_cart_totals(items)
    
    subtotal_str = f"{totals['subtotal']:.2f}"
    discount_val = totals['discount_amount']
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

    breakdown = {
        "item_total": {
            "currency_code": "EUR",
            "value": subtotal_str
        },
        "shipping": {
            "currency_code": "EUR",
            "value": shipping_str
        }
    }
    # NOTA: PayPal v2 rifiuta 'discount' se il valore è '0.00' (errore 422). Lo includiamo solo se > 0.
    if discount_val > Decimal("0.00"):
        breakdown["discount"] = {
            "currency_code": "EUR",
            "value": f"{discount_val:.2f}"
        }

    purchase_unit = {
        "reference_id": "GADGETPOINT_ORDER",
        "payee": {
            "email_address": cfg["payee_email"]
        },
        "description": "Ordine Oggetti Personalizzati GadgetPoint.it",
        "amount": {
            "currency_code": "EUR",
            "value": total_str,
            "breakdown": breakdown
        },
        "items": item_breakdown_list
    }

    # Dati di spedizione forniti dal cliente
    shipping_addr = (customer_info.get("shipping_address") or "").strip()
    shipping_city = (customer_info.get("shipping_city") or "").strip()
    shipping_prov = (customer_info.get("shipping_province") or "").strip()[:2].upper()
    shipping_zip = str(customer_info.get("shipping_zip") or "").strip()
    cust_name = (customer_info.get("customer_name") or "Cliente").strip()

    if shipping_addr and shipping_city and shipping_zip:
        purchase_unit["shipping"] = {
            "name": {
                "full_name": cust_name
            },
            "address": {
                "address_line_1": shipping_addr,
                "admin_area_2": shipping_city,
                "admin_area_1": shipping_prov or "RM",
                "postal_code": shipping_zip,
                "country_code": "IT"
            }
        }
        shipping_pref = "SET_PROVIDED_ADDRESS"
    else:
        shipping_pref = "GET_FROM_FILE"

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [purchase_unit],
        "application_context": {
            "brand_name": "GadgetPoint.it",
            "locale": "it-IT",
            "landing_page": "NO_PREFERENCE",
            "shipping_preference": shipping_pref,
            "user_action": "PAY_NOW"
        }
    }

    token = _get_access_token()
    url = f"{cfg['base_url']}/v2/checkout/orders"
    req_data = json.dumps(payload).encode("utf-8")
    logger.info(f"Invio ordine PayPal a: {url} | Totale: {total_str} EUR | Subtotale: {subtotal_str} | Spedizione: {shipping_str}")

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
            logger.info(f"Ordine PayPal creato con successo: ID={res_body.get('id')}, Status={res_body.get('status')}")
            return res_body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"PayPal Order Creation Error (HTTP {e.code}): {err_body}")
        raise RuntimeError(f"Errore creazione ordine PayPal ({e.code}): {err_body}")
    except Exception as e:
        logger.error(f"PayPal Order Creation Unexpected Exception: {str(e)}")
        raise

def capture_paypal_order(paypal_order_id: str) -> Dict[str, Any]:
    """Cattura il pagamento di un ordine approvato dal cliente con logging esplicito."""
    cfg = get_paypal_config()
    token = _get_access_token()
    url = f"{cfg['base_url']}/v2/checkout/orders/{paypal_order_id}/capture"
    logger.info(f"Cattura pagamento PayPal ordine ID={paypal_order_id} a: {url}")
    
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
            logger.info(f"Pagamento PayPal catturato con successo: ID={capture_res.get('id')}, Status={capture_res.get('status')}")
            return capture_res
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"PayPal Capture Error (HTTP {e.code}): {err_body}")
        raise RuntimeError(f"Errore cattura pagamento PayPal ({e.code}): {err_body}")
    except Exception as e:
        logger.error(f"PayPal Capture Unexpected Exception: {str(e)}")
        raise
