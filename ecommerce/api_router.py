"""
Router FastAPI per lo Storefront E-Commerce e il Gestionale Admin Snapmaker U1.
Collega:
- Supabase (PostgreSQL) per tabelle filaments, orders, order_items
- PayPal REST API v2 per ordini e pagamenti
- Resend per notifiche email automatiche
- Snapmaker3MFPackager per il download istantaneo del 3MF nativo (zero prime tower)
- Motore Coupon Sconto e Ritiro a Mano / Contanti
"""
import os
import sys
import uuid
import datetime
import zoneinfo
import json
import hmac
import hashlib
import time
import secrets
import collections
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from decimal import Decimal

def get_rome_now() -> datetime.datetime:
    """Restituisce il timestamp corrente con fuso orario italiano Europe/Rome."""
    try:
        return datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Rome"))
    except Exception:
        # Fallback sicuro UTC+2
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))

from fastapi import APIRouter, HTTPException, Depends, Header, Response, Query, Request
from fastapi.responses import FileResponse, JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ecommerce.cart_engine import (
    calculate_cart_totals,
    get_coupons,
    save_coupons,
    validate_coupon_code
)
from ecommerce.services.paypal_service import create_paypal_order, capture_paypal_order, get_paypal_config
from ecommerce.services.notification_service import (
    send_customer_order_confirmation,
    send_admin_new_order_alert
)
from ecommerce.services.resend_service import send_order_shipped_notification
from ecommerce.services.model_generator_service import compile_order_item_to_3mf

router = APIRouter(prefix="/api", tags=["ecommerce"])

EXPECTED_PIN = os.getenv("ADMIN_PIN", "L21dic82") # PIN di protezione gestionale
ADMIN_PIN = EXPECTED_PIN
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# In-memory storage di fallback (se Supabase non è ancora agganciato con credenziali live)
_LOCAL_FILAMENTS_DB = [
    {"id": "fil-01", "sku": "34062", "name": "SnapSpeed PLA Black", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#080A0D", "secondary_hex_color": None, "icon": "⚫", "is_available": True},
    {"id": "fil-02", "sku": "34073", "name": "SnapSpeed PLA Cool White", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#D9DFE5", "secondary_hex_color": None, "icon": "⚪", "is_available": True},
    {"id": "fil-03", "sku": "34061", "name": "SnapSpeed PLA Pearl White", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#E2DEDB", "secondary_hex_color": None, "icon": "◽", "is_available": True},
    {"id": "fil-04", "sku": "34065", "name": "SnapSpeed PLA Red", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#E72F1D", "secondary_hex_color": None, "icon": "🔴", "is_available": True},
    {"id": "fil-05", "sku": "34064", "name": "SnapSpeed PLA Blue", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#003776", "secondary_hex_color": None, "icon": "🔵", "is_available": True},
    {"id": "fil-06", "sku": "34112", "name": "SnapSpeed PLA Bright Yellow", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#F8F81C", "secondary_hex_color": None, "icon": "🟡", "is_available": True},
    {"id": "fil-07", "sku": "34067", "name": "SnapSpeed PLA Orange", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#F97429", "secondary_hex_color": None, "icon": "🟠", "is_available": True},
    {"id": "fil-08", "sku": "34068", "name": "SnapSpeed PLA Green", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#2D9E59", "secondary_hex_color": None, "icon": "🟢", "is_available": True},
    {"id": "fil-09", "sku": "34074", "name": "SnapSpeed PLA Magenta", "group_name": "SnapSpeed PLA", "material_type": "PLA", "hex_color": "#F24574", "secondary_hex_color": None, "icon": "🌺", "is_available": True},
    {"id": "fil-10", "sku": "34202", "name": "Silk Sunset Ember", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#d9251d", "secondary_hex_color": "#eab308", "icon": "✨", "is_available": True},
    {"id": "fil-11", "sku": "34203", "name": "Silk Aurora Gold", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#0284c7", "secondary_hex_color": "#eab308", "icon": "✨", "is_available": True},
    {"id": "fil-12", "sku": "34204", "name": "Silk Solar Alloy", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#ea580c", "secondary_hex_color": "#10b981", "icon": "✨", "is_available": True},
    {"id": "fil-13", "sku": "34205", "name": "Silk Mint Lemonade", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#ECED17", "secondary_hex_color": "#44ADE5", "icon": "✨", "is_available": True},
    {"id": "fil-14", "sku": "34206", "name": "Silk Sea Glass", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#44ADE5", "secondary_hex_color": "#18CCAF", "icon": "✨", "is_available": True},
    {"id": "fil-15", "sku": "34207", "name": "Silk Ice Lake", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#C4C7D9", "secondary_hex_color": "#44ADE5", "icon": "✨", "is_available": True},
    {"id": "fil-16", "sku": "34208", "name": "Silk City Billboard", "group_name": "Silk Dual-Color", "material_type": "PLA", "hex_color": "#CBF914", "secondary_hex_color": "#D623AA", "icon": "✨", "is_available": True}
]
_LOCAL_ORDERS_DB = []
_LOCAL_ORDER_ITEMS_DB = []

# ==============================================================================
# PERSISTENZA ORDINI & COSTANTE UNIFICATA PERCORSO DATABASE
# ==============================================================================
DATA_DIR = (PROJECT_ROOT / "ecommerce" / "data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Costante unificata per garantire allineamento assoluto tra checkout e Admin
_CUSTOM_ORDERS_PATH = os.getenv("ORDERS_FILE_PATH", "").strip()
if _CUSTOM_ORDERS_PATH:
    ORDERS_FILE_PATH = Path(_CUSTOM_ORDERS_PATH).resolve()
else:
    ORDERS_FILE_PATH = (DATA_DIR / "orders_db.json").resolve()

ALT_ORDERS_FILE = (DATA_DIR / "orders.json").resolve()
DB_FILE = ORDERS_FILE_PATH

def _load_local_db():
    global _LOCAL_ORDERS_DB, _LOCAL_ORDER_ITEMS_DB, _LOCAL_FILAMENTS_DB
    target_file = ORDERS_FILE_PATH
    if not target_file.exists() and ALT_ORDERS_FILE.exists() and ALT_ORDERS_FILE.stat().st_size > 0:
        target_file = ALT_ORDERS_FILE

    if target_file.exists() and target_file.stat().st_size > 0:
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                _LOCAL_ORDERS_DB = data.get("orders", [])
                _LOCAL_ORDER_ITEMS_DB = data.get("order_items", [])
                if data.get("filaments"):
                    _LOCAL_FILAMENTS_DB = data["filaments"]
        except Exception as e:
            print(f"[WARN] Impossibile caricare {target_file}: {e}")

def _save_local_db():
    try:
        ORDERS_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps({
            "orders": _LOCAL_ORDERS_DB,
            "order_items": _LOCAL_ORDER_ITEMS_DB,
            "filaments": _LOCAL_FILAMENTS_DB
        }, indent=2, ensure_ascii=False, default=str)
        with open(ORDERS_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        # Mirror sincrono su orders.json per massima interoperabilità
        try:
            with open(ALT_ORDERS_FILE, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass
    except Exception as e:
        print(f"[WARN] Impossibile salvare {ORDERS_FILE_PATH}: {e}")

_load_local_db()

# ==============================================================================
# SICUREZZA, TOKEN DI SESSIONE & RATE LIMITING
# ==============================================================================

_RATE_LIMIT_STORE = collections.defaultdict(list)
ORDER_RATE_LIMIT_WINDOW = 60 # 60 secondi
ORDER_RATE_LIMIT_MAX = 10 # massimo 10 ordini al minuto per IP

def check_order_rate_limit(request: Optional[Request] = None):
    """Limita la frequenza di creazione ordini per singolo IP per prevenire attacchi di spam e DoS."""
    if not request:
        return
    client_ip = "unknown"
    if request.client and request.client.host:
        client_ip = request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    now = time.time()
    timestamps = _RATE_LIMIT_STORE[client_ip]
    _RATE_LIMIT_STORE[client_ip] = [t for t in timestamps if now - t < ORDER_RATE_LIMIT_WINDOW]

    if len(_RATE_LIMIT_STORE[client_ip]) >= ORDER_RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Troppe richieste inviate. Attendi un momento prima di inoltrare un nuovo ordine."
        )

    _RATE_LIMIT_STORE[client_ip].append(now)

def _sanitize_customer_info(customer_info: Dict[str, Any]) -> Dict[str, Any]:
    """Sanifica e limita la lunghezza dei campi inseriti dall'utente prima del salvataggio."""
    return {
        "customer_name": str(customer_info.get("customer_name") or "Cliente")[:100].strip(),
        "customer_email": str(customer_info.get("customer_email") or "")[:120].strip(),
        "customer_phone": str(customer_info.get("customer_phone") or "")[:40].strip(),
        "shipping_address": str(customer_info.get("shipping_address") or "")[:200].strip(),
        "shipping_city": str(customer_info.get("shipping_city") or "")[:100].strip(),
        "shipping_zip": str(customer_info.get("shipping_zip") or "")[:20].strip(),
        "shipping_province": str(customer_info.get("shipping_province") or "")[:10].strip().upper(),
        "order_notes": str(customer_info.get("order_notes") or "")[:500].strip(),
    }

ADMIN_SESSION_SECRET = os.getenv("SESSION_SECRET") or hashlib.sha256(EXPECTED_PIN.encode("utf-8")).hexdigest()

def generate_admin_token() -> str:
    """Genera un token di sessione firmato HMAC-SHA256 con scadenza a 24 ore."""
    exp = int(time.time()) + 86400
    nonce = secrets.token_hex(8)
    payload = f"{exp}:{nonce}"
    signature = hmac.new(ADMIN_SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"

def verify_admin_token(token_str: str) -> bool:
    """Verifica crittograficamente la validità e la scadenza del token di sessione admin."""
    if not token_str or ":" not in token_str:
        return False
    parts = token_str.strip().split(":")
    if len(parts) != 3:
        return False
    exp_str, nonce, signature = parts
    try:
        exp = int(exp_str)
        if time.time() > exp:
            return False
    except (ValueError, TypeError):
        return False

    payload = f"{exp_str}:{nonce}"
    expected_sig = hmac.new(ADMIN_SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected_sig)

def verify_admin_auth(
    x_admin_pin: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    pin: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
) -> bool:
    """
    Verifica l'autenticazione per gli endpoint amministrativi.
    Supporta:
    1. Header Authorization: Bearer <token>
    2. Header X-Admin-Token o query param 'token' (firmato HMAC)
    3. Header X-Admin-Pin o query param 'pin' (confronto timing-attack safe con expected_pin)
    """
    # 1. Bearer Token
    if authorization and authorization.lower().startswith("bearer "):
        bearer_val = authorization.split(" ", 1)[1].strip()
        if verify_admin_token(bearer_val):
            return True

    # 2. X-Admin-Token / Query token
    cand_token = (x_admin_token or token or "").strip()
    if cand_token and verify_admin_token(cand_token):
        return True

    # 3. PIN (Header o Query) con confronto a tempo costante
    expected_pin = os.getenv("ADMIN_PIN", "L21dic82").strip()
    cand_pin = str(x_admin_pin or pin or "").strip()
    if cand_pin and hmac.compare_digest(cand_pin, expected_pin):
        return True

    raise HTTPException(status_code=401, detail="Non autorizzato: PIN o token amministrativo non valido.")

@router.post("/admin/verify-pin")
@router.get("/admin/verify-pin")
async def api_verify_pin(
    request: Request,
    payload: Optional[Dict[str, Any]] = None,
    x_admin_pin: Optional[str] = Header(None),
    pin: Optional[str] = Query(None)
):
    """Endpoint dedicato per la verifica della chiave PIN admin e rilascio token di sessione HMAC."""
    expected_pin = os.getenv("ADMIN_PIN", "L21dic82").strip()
    provided = ""

    # 1. Da payload dizionario
    if payload and isinstance(payload, dict):
        provided = payload.get("pin") or payload.get("admin_pin") or ""

    # 2. Da JSON body (se presente in POST)
    if not provided and request and request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                provided = body.get("pin") or body.get("admin_pin") or ""
            elif isinstance(body, str):
                provided = body
        except Exception:
            pass

    # 3. Fallback su Header o Query string
    if not provided:
        provided = x_admin_pin or pin or ""

    provided = str(provided).strip()
    if not provided or not hmac.compare_digest(provided, expected_pin):
        raise HTTPException(status_code=401, detail="PIN non corretto!")

    token = generate_admin_token()
    return {
        "status": "ok",
        "valid": True,
        "token": token,
        "expires_in": 86400,
        "message": "Autenticazione riuscita."
    }

DEFAULT_PRICING_SETTINGS = {
    "keychain_standard": 2.90,
    "keychain_complex": 3.90,
    "desk_sign": 6.90,
    "extra_line2": 2.00,
    "shipping_fixed": 4.90,
    "promo_3x2_enabled": True
}

def _load_pricing_settings() -> Dict[str, Any]:
    pricing_file = DATA_DIR / "pricing_settings.json"
    if pricing_file.exists() and pricing_file.stat().st_size > 0:
        try:
            with open(pricing_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Impossibile caricare {pricing_file}: {e}")
    return DEFAULT_PRICING_SETTINGS.copy()

def _save_pricing_settings(settings: dict):
    pricing_file = DATA_DIR / "pricing_settings.json"
    try:
        with open(pricing_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] Impossibile salvare {pricing_file}: {e}")

# ==============================================================================
# 1. STOREFRONT PUBBLICO (FILAMENTI, LISTINO, CARRELLO & COUPON)
# ==============================================================================

@router.get("/store/filaments")
def get_available_filaments():
    """Restituisce esclusivamente i filamenti contrassegnati come DISPONIBILI per lo Storefront."""
    return [fil for fil in _LOCAL_FILAMENTS_DB if fil.get("is_available") is True]

@router.get("/store/pricing")
def get_store_pricing():
    """Restituisce il listino prezzi, promozioni e configurazione PayPal per lo Storefront."""
    settings = _load_pricing_settings()
    paypal_cfg = get_paypal_config()
    settings["paypal_client_id"] = paypal_cfg["client_id"] or "sb"
    settings["paypal_mode"] = paypal_cfg["mode"]
    return settings

@router.post("/store/calculate-cart")
def api_calculate_cart(payload: Dict[str, Any]):
    """Calcola in modo deterministico il totale, promo 3x2, coupon e spedizione/ritiro."""
    items = payload.get("items", [])
    coupon_code = payload.get("coupon_code") or payload.get("coupon")
    delivery_method = payload.get("delivery_method") or payload.get("deliveryMethod") or "shipping"
    totals = calculate_cart_totals(items, coupon_code=coupon_code, delivery_method=delivery_method)
    return {
        "item_count": totals["item_count"],
        "subtotal": float(totals["subtotal"]),
        "promo_discount": float(totals["promo_discount"]),
        "coupon_discount": float(totals["coupon_discount"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": float(totals["shipping_amount"]),
        "shipping_label": totals["shipping_label"],
        "total_amount": float(totals["total_amount"]),
        "free_items_count": totals["free_items_count"],
        "promo_applied": totals["promo_applied"],
        "promo_label": totals["promo_label"],
        "coupon_applied": totals["coupon_applied"],
        "coupon_code": totals["coupon_code"],
        "coupon_label": totals["coupon_label"],
        "delivery_method": totals["delivery_method"]
    }

@router.post("/store/validate-coupon")
def api_validate_coupon(payload: Dict[str, Any]):
    """Verifica e calcola lo sconto di un codice coupon inserito dal cliente."""
    code = payload.get("code") or payload.get("coupon_code") or ""
    subtotal_val = payload.get("subtotal", 0.0)
    try:
        subtotal = Decimal(str(subtotal_val))
    except Exception:
        subtotal = Decimal("0.0")

    res = validate_coupon_code(code, subtotal)
    if not res["valid"]:
        return JSONResponse(status_code=400, content={"valid": False, "message": res["message"]})

    coupon = res["coupon"]
    return {
        "valid": True,
        "code": coupon["code"],
        "type": coupon.get("type", "percentage"),
        "value": float(coupon.get("value", 0.0)),
        "min_spend": float(coupon.get("min_spend", 0.0)),
        "discount_amount": float(res["discount_amount"]),
        "message": res["message"]
    }

# ==============================================================================
# 2. CHECKOUT & ORDINI (PAYPAL, CONTANTI AL RITIRO & TEST)
# ==============================================================================

@router.post("/store/orders/create-paypal")
@router.post("/orders/create-paypal-order")
@router.post("/orders/create-paypal")
def api_create_paypal_order(payload: Dict[str, Any], request: Request):
    """Crea un ordine PayPal sicuro con importi calcolati dal server e logging esplicito."""
    check_order_rate_limit(request)
    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Il carrello è vuoto.")
    if len(items) > 50:
        raise HTTPException(status_code=400, detail="Il carrello non può contenere più di 50 articoli per ordine.")

    customer_info = _sanitize_customer_info(payload.get("customerInfo", {}))
    coupon_code = payload.get("coupon_code") or customer_info.get("coupon_code") or payload.get("coupon")
    delivery_method = payload.get("delivery_method") or customer_info.get("delivery_method") or "shipping"

    cfg = get_paypal_config()
    print(f"[API] Richiesta creazione ordine PayPal | Mode: {cfg['mode']} | Articoli: {len(items)} | Delivery: {delivery_method} | Coupon: {coupon_code}")

    if not cfg["client_id"] or not cfg["client_secret"] or cfg["client_id"] == "sb":
        mock_id = f"PAYPAL_MOCK_{uuid.uuid4().hex[:10].upper()}"
        print(f"[API] Credenziali PayPal non configurate o default 'sb', generato mock ID: {mock_id}")
        return {"id": mock_id, "status": "CREATED", "mode": "mock"}

    try:
        order_res = create_paypal_order(items, customer_info, coupon_code=coupon_code, delivery_method=delivery_method)
        return order_res
    except Exception as e:
        print(f"[API] Errore creazione ordine PayPal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store/orders/capture-paypal")
@router.post("/orders/capture-paypal-order")
@router.post("/orders/capture-paypal")
def api_capture_paypal_order(payload: Dict[str, Any], request: Request):
    """Cattura il pagamento PayPal, salva l'ordine in DB e avvia le notifiche Resend."""
    check_order_rate_limit(request)
    paypal_order_id = payload.get("paypalOrderId") or payload.get("orderID") or payload.get("paypal_order_id")
    items = payload.get("items", [])
    if not paypal_order_id or not items:
        raise HTTPException(status_code=400, detail="Dati ordine mancanti (paypalOrderId o items).")
    if len(items) > 50:
        raise HTTPException(status_code=400, detail="Il carrello non può contenere più di 50 articoli per ordine.")

    customer_info = _sanitize_customer_info(payload.get("customerInfo", {}))
    coupon_code = payload.get("coupon_code") or customer_info.get("coupon_code") or payload.get("coupon")
    delivery_method = payload.get("delivery_method") or customer_info.get("delivery_method") or "shipping"
    is_pickup = delivery_method == "pickup"

    cfg = get_paypal_config()
    print(f"[API] Richiesta cattura ordine PayPal ID: {paypal_order_id} | Delivery: {delivery_method} | Coupon: {coupon_code}")

    # Calcolo totale verificato
    totals = calculate_cart_totals(items, coupon_code=coupon_code, delivery_method=delivery_method)
    
    # Genera codice ordine
    _load_local_db()
    now = get_rome_now()
    order_number = f"U1-{now.strftime('%Y%m%d')}-{len(_LOCAL_ORDERS_DB) + 1:04d}"
    order_id = str(uuid.uuid4())

    capture_id = f"CAP_{uuid.uuid4().hex[:8]}"
    if cfg["client_id"] and cfg["client_secret"] and cfg["client_id"] != "sb" and not paypal_order_id.startswith("PAYPAL_MOCK_"):
        try:
            capture_res = capture_paypal_order(paypal_order_id)
            capture_id = capture_res.get("id", capture_id)
        except Exception as e:
            print(f"[API] Errore cattura PayPal: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Errore cattura PayPal: {str(e)}")

    order_record = {
        "id": order_id,
        "order_number": order_number,
        "customer_name": customer_info.get("customer_name", "Cliente"),
        "customer_email": customer_info.get("customer_email", ""),
        "customer_phone": customer_info.get("customer_phone", ""),
        "shipping_address": customer_info.get("shipping_address", "Ritiro a mano" if is_pickup else ""),
        "shipping_city": customer_info.get("shipping_city", "Laboratorio" if is_pickup else ""),
        "shipping_zip": customer_info.get("shipping_zip", "00000" if is_pickup else ""),
        "shipping_province": customer_info.get("shipping_province", "RM" if is_pickup else ""),
        "order_notes": customer_info.get("order_notes", ""),
        "delivery_method": "pickup" if is_pickup else "shipping",
        "payment_method": "paypal",
        "coupon_code": totals.get("coupon_code"),
        "coupon_discount": float(totals.get("coupon_discount", 0.0)),
        "promo_discount": float(totals.get("promo_discount", 0.0)),
        "subtotal_amount": float(totals["subtotal"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": float(totals["shipping_amount"]),
        "total_amount": float(totals["total_amount"]),
        "paypal_order_id": paypal_order_id,
        "paypal_capture_id": capture_id,
        "payment_status": "paid",
        "order_status": "da_stampare",
        "courier": "Ritiro a mano di persona" if is_pickup else "BRT / SDA",
        "created_at": now.isoformat()
    }

    _LOCAL_ORDERS_DB.insert(0, order_record)

    # Registra i singoli articoli con i parametri 3D completi
    saved_items = []
    for it in totals["items"]:
        raw = it["raw"]
        item_id = str(uuid.uuid4())
        item_record = {
            "id": item_id,
            "order_id": order_id,
            "product_type": raw.get("productType") or raw.get("product_type") or "keychain",
            "product_title": raw.get("productTitle") or raw.get("product_title") or "Portachiavi",
            "unit_price": float(it["unit_price"]),
            "is_free_promo": it["is_free_promo"],
            "custom_text_line1": raw.get("customTextLine1") or raw.get("custom_text_line1") or "TEST",
            "custom_text_line2": raw.get("customTextLine2") or raw.get("custom_text_line2"),
            "font_id": raw.get("fontId") or raw.get("font_id") or "Montserrat",
            "icon_id": raw.get("iconId") or raw.get("icon_id") or raw.get("icon_name"),
            "icon_position": raw.get("iconPosition") or raw.get("icon_position") or "right",
            "icon_color_hex": raw.get("iconColorHex") or raw.get("icon_color_hex"),
            "has_custom_icon_color": raw.get("hasCustomIconColor") or raw.get("has_custom_icon_color") or False,
            "base_style": raw.get("baseStyle") or raw.get("base_style") or "rectangle",
            "hole_position": raw.get("holePosition") or raw.get("hole_position") or "left",
            "base_color_name": raw.get("baseColorName") or raw.get("base_color_name") or "Black",
            "base_color_hex": raw.get("baseColorHex") or raw.get("base_color_hex") or "#080A0D",
            "text_color_name": raw.get("textColorName") or raw.get("text_color_name") or "Cool White",
            "text_color_hex": raw.get("textColorHex") or raw.get("text_color_hex") or "#D9DFE5",
            "generator_params": raw.get("generatorParams") or raw.get("generator_params") or {}
        }
        _LOCAL_ORDER_ITEMS_DB.append(item_record)
        saved_items.append(item_record)

    _save_local_db()

    # Notifiche email via Resend con blocchi separati per isolare errori
    try:
        cust_res = send_customer_order_confirmation(order_record, saved_items)
        if cust_res and isinstance(cust_res, dict) and cust_res.get("error"):
            print(f"[WARN] Invio conferma cliente PayPal non riuscito ({order_number}): {cust_res}")
    except Exception as e:
        print(f"[WARN] Errore imprevisto invio email cliente PayPal ({order_number}): {e}")

    try:
        admin_res = send_admin_new_order_alert(order_record, saved_items)
        if admin_res and isinstance(admin_res, dict) and admin_res.get("error"):
            print(f"[WARN] Invio notifica admin PayPal non riuscito ({order_number}): {admin_res}")
    except Exception as e:
        print(f"[WARN] Errore imprevisto invio email admin PayPal ({order_number}): {e}")

    return {
        "status": "success",
        "order_number": order_number,
        "customer_email": order_record["customer_email"],
        "total": order_record["total_amount"],
        "delivery_method": order_record["delivery_method"],
        "payment_method": "paypal"
    }

@router.post("/store/orders/create-pickup-cash")
@router.post("/orders/create-pickup-cash")
def api_create_pickup_cash_order(payload: Dict[str, Any], request: Request):
    """
    Registra un ordine con consegna 'Ritiro a Mano' e pagamento 'Contanti al Ritiro'.
    Salta PayPal, assegna stato 'da_stampare' e payment_status 'in_attesa_al_ritiro',
    invia le notifiche email al cliente e all'amministratore.
    """
    check_order_rate_limit(request)
    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Il carrello è vuoto.")
    if len(items) > 50:
        raise HTTPException(status_code=400, detail="Il carrello non può contenere più di 50 articoli per ordine.")

    customer_info = _sanitize_customer_info(payload.get("customerInfo", {}))
    coupon_code = payload.get("coupon_code") or customer_info.get("coupon_code") or payload.get("coupon")

    cust_name = customer_info["customer_name"]
    cust_email = customer_info["customer_email"]
    cust_phone = customer_info["customer_phone"]

    if not cust_name or not cust_email or not cust_phone:
        raise HTTPException(status_code=400, detail="Nome, Email e Cellulare sono obbligatori per il ritiro a mano.")

    if "@" not in cust_email or "." not in cust_email:
        raise HTTPException(status_code=400, detail="Inserisci un indirizzo email valido.")

    # Calcolo totale verificato con delivery_method='pickup'
    totals = calculate_cart_totals(items, coupon_code=coupon_code, delivery_method="pickup")

    _load_local_db()
    now = get_rome_now()
    order_number = f"U1-RIT-{now.strftime('%Y%m%d')}-{len(_LOCAL_ORDERS_DB) + 1:04d}"
    order_id = str(uuid.uuid4())

    order_record = {
        "id": order_id,
        "order_number": order_number,
        "customer_name": cust_name,
        "customer_email": cust_email,
        "customer_phone": cust_phone,
        "shipping_address": customer_info.get("shipping_address") or "Ritiro a mano di persona",
        "shipping_city": customer_info.get("shipping_city") or "Laboratorio",
        "shipping_zip": customer_info.get("shipping_zip") or "00000",
        "shipping_province": customer_info.get("shipping_province") or "RM",
        "order_notes": customer_info.get("order_notes", ""),
        "delivery_method": "pickup",
        "payment_method": "cash_on_pickup",
        "coupon_code": totals.get("coupon_code"),
        "coupon_discount": float(totals.get("coupon_discount", 0.0)),
        "promo_discount": float(totals.get("promo_discount", 0.0)),
        "subtotal_amount": float(totals["subtotal"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": 0.0,
        "total_amount": float(totals["total_amount"]),
        "paypal_order_id": None,
        "paypal_capture_id": None,
        "payment_status": "in_attesa_al_ritiro",
        "order_status": "da_stampare",
        "courier": "Ritiro a mano (Contanti)",
        "created_at": now.isoformat()
    }

    _LOCAL_ORDERS_DB.insert(0, order_record)

    saved_items = []
    for it in totals["items"]:
        raw = it["raw"]
        item_id = str(uuid.uuid4())
        item_record = {
            "id": item_id,
            "order_id": order_id,
            "product_type": raw.get("productType") or raw.get("product_type") or "keychain",
            "product_title": raw.get("productTitle") or raw.get("product_title") or "Portachiavi",
            "unit_price": float(it["unit_price"]),
            "is_free_promo": it["is_free_promo"],
            "custom_text_line1": raw.get("customTextLine1") or raw.get("custom_text_line1") or "TEST",
            "custom_text_line2": raw.get("customTextLine2") or raw.get("custom_text_line2"),
            "font_id": raw.get("fontId") or raw.get("font_id") or "Montserrat",
            "icon_id": raw.get("iconId") or raw.get("icon_id") or raw.get("icon_name"),
            "icon_position": raw.get("iconPosition") or raw.get("icon_position") or "right",
            "icon_color_hex": raw.get("iconColorHex") or raw.get("icon_color_hex"),
            "has_custom_icon_color": raw.get("hasCustomIconColor") or raw.get("has_custom_icon_color") or False,
            "base_style": raw.get("baseStyle") or raw.get("base_style") or "rectangle",
            "hole_position": raw.get("holePosition") or raw.get("hole_position") or "left",
            "base_color_name": raw.get("baseColorName") or raw.get("base_color_name") or "Black",
            "base_color_hex": raw.get("baseColorHex") or raw.get("base_color_hex") or "#080A0D",
            "text_color_name": raw.get("textColorName") or raw.get("text_color_name") or "Cool White",
            "text_color_hex": raw.get("textColorHex") or raw.get("text_color_hex") or "#D9DFE5",
            "generator_params": raw.get("generatorParams") or raw.get("generator_params") or {}
        }
        _LOCAL_ORDER_ITEMS_DB.append(item_record)
        saved_items.append(item_record)

    _save_local_db()

    # Notifiche email via Resend con blocchi separati per isolare errori
    try:
        cust_res = send_customer_order_confirmation(order_record, saved_items)
        if cust_res and isinstance(cust_res, dict) and cust_res.get("error"):
            print(f"[WARN] Invio conferma cliente ritiro non riuscito ({order_number}): {cust_res}")
    except Exception as e:
        print(f"[WARN] Errore imprevisto invio email cliente ritiro ({order_number}): {e}")

    try:
        admin_res = send_admin_new_order_alert(order_record, saved_items)
        if admin_res and isinstance(admin_res, dict) and admin_res.get("error"):
            print(f"[WARN] Invio notifica admin ritiro non riuscito ({order_number}): {admin_res}")
    except Exception as e:
        print(f"[WARN] Errore imprevisto invio email admin ritiro ({order_number}): {e}")

    return {
        "status": "success",
        "order_number": order_number,
        "customer_email": order_record["customer_email"],
        "total": order_record["total_amount"],
        "delivery_method": "pickup",
        "payment_method": "cash_on_pickup"
    }

@router.post("/store/orders/create-test")
def api_create_test_order(payload: Dict[str, Any], request: Request):
    """
    MODALITÀ TEST CHECKOUT:
    Crea e registra un ordine di test senza richiedere transazioni monetarie reali su PayPal.
    """
    check_order_rate_limit(request)
    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Il carrello è vuoto.")
    if len(items) > 50:
        raise HTTPException(status_code=400, detail="Il carrello non può contenere più di 50 articoli per ordine.")

    customer_info = _sanitize_customer_info(payload.get("customerInfo", {}))
    coupon_code = payload.get("coupon_code") or customer_info.get("coupon_code") or payload.get("coupon")
    delivery_method = payload.get("delivery_method") or customer_info.get("delivery_method") or "shipping"
    is_pickup = delivery_method == "pickup"

    if not items:
        raise HTTPException(status_code=400, detail="Il carrello è vuoto.")

    totals = calculate_cart_totals(items, coupon_code=coupon_code, delivery_method=delivery_method)
    _load_local_db()
    now = get_rome_now()
    order_number = f"TEST-U1-{now.strftime('%Y%m%d')}-{len(_LOCAL_ORDERS_DB) + 1:04d}"
    order_id = str(uuid.uuid4())

    order_record = {
        "id": order_id,
        "order_number": order_number,
        "customer_name": customer_info.get("customer_name") or "Tester Sviluppatore",
        "customer_email": customer_info.get("customer_email") or "test@snapmaker-studio.it",
        "customer_phone": customer_info.get("customer_phone") or "340 0000000",
        "shipping_address": customer_info.get("shipping_address") or ("Ritiro a mano" if is_pickup else "Via Laboratorio 3D, 1"),
        "shipping_city": customer_info.get("shipping_city") or ("Laboratorio" if is_pickup else "Roma"),
        "shipping_zip": customer_info.get("shipping_zip") or ("00000" if is_pickup else "00100"),
        "shipping_province": customer_info.get("shipping_province") or "RM",
        "order_notes": customer_info.get("order_notes") or "Ordine di Prova (Test Senza Pagamento)",
        "delivery_method": "pickup" if is_pickup else "shipping",
        "payment_method": "test_simulation",
        "coupon_code": totals.get("coupon_code"),
        "coupon_discount": float(totals.get("coupon_discount", 0.0)),
        "promo_discount": float(totals.get("promo_discount", 0.0)),
        "subtotal_amount": float(totals["subtotal"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": float(totals["shipping_amount"]),
        "total_amount": float(totals["total_amount"]),
        "paypal_order_id": f"TEST_SIMULATION_{uuid.uuid4().hex[:8].upper()}",
        "paypal_capture_id": f"TEST_CAP_{uuid.uuid4().hex[:8].upper()}",
        "payment_provider": "test_simulation",
        "payment_status": "paid",
        "order_status": "da_stampare",
        "courier": "Ritiro a mano di persona" if is_pickup else "BRT / SDA",
        "created_at": now.isoformat()
    }

    _LOCAL_ORDERS_DB.insert(0, order_record)

    saved_items = []
    for it in totals["items"]:
        raw = it["raw"]
        item_id = str(uuid.uuid4())
        item_record = {
            "id": item_id,
            "order_id": order_id,
            "product_type": raw.get("productType") or raw.get("product_type") or "keychain",
            "product_title": raw.get("productTitle") or raw.get("product_title") or "Portachiavi",
            "unit_price": float(it["unit_price"]),
            "is_free_promo": it["is_free_promo"],
            "custom_text_line1": raw.get("customTextLine1") or raw.get("custom_text_line1") or "TEST",
            "custom_text_line2": raw.get("customTextLine2") or raw.get("custom_text_line2"),
            "font_id": raw.get("fontId") or raw.get("font_id") or "Montserrat",
            "icon_id": raw.get("iconId") or raw.get("icon_id") or raw.get("icon_name"),
            "icon_position": raw.get("iconPosition") or raw.get("icon_position") or "right",
            "icon_color_hex": raw.get("iconColorHex") or raw.get("icon_color_hex"),
            "has_custom_icon_color": raw.get("hasCustomIconColor") or raw.get("has_custom_icon_color") or False,
            "base_style": raw.get("baseStyle") or raw.get("base_style") or "rectangle",
            "hole_position": raw.get("holePosition") or raw.get("hole_position") or "left",
            "base_color_name": raw.get("baseColorName") or raw.get("base_color_name") or "Black",
            "base_color_hex": raw.get("baseColorHex") or raw.get("base_color_hex") or "#080A0D",
            "text_color_name": raw.get("textColorName") or raw.get("text_color_name") or "Cool White",
            "text_color_hex": raw.get("textColorHex") or raw.get("text_color_hex") or "#D9DFE5",
            "generator_params": raw.get("generatorParams") or raw.get("generator_params") or {}
        }
        _LOCAL_ORDER_ITEMS_DB.append(item_record)
        saved_items.append(item_record)

    _save_local_db()

    try:
        send_admin_new_order_alert(order_record, saved_items)
    except Exception as e:
        print(f"[WARN] Invio email test non riuscito: {e}")

    return {
        "success": True,
        "status": "success",
        "id": order_id,
        "order_number": order_number,
        "customer_email": order_record["customer_email"],
        "total": order_record["total_amount"],
        "is_test": True
    }

# ==============================================================================
# 3. GESTIONALE ADMIN (PROTETTO DA PIN)
# ==============================================================================

@router.get("/admin/filaments")
def admin_list_filaments(auth: bool = Depends(verify_admin_auth)):
    """Restituisce la lista completa dei filamenti per il pannello di gestione."""
    return _LOCAL_FILAMENTS_DB

@router.post("/admin/filaments/{filament_id}/toggle")
def admin_toggle_filament(filament_id: str, auth: bool = Depends(verify_admin_auth)):
    """Inverte lo stato del filamento [Disponibile / Esaurito]."""
    for fil in _LOCAL_FILAMENTS_DB:
        if fil["id"] == filament_id or fil["sku"] == filament_id:
            fil["is_available"] = not fil["is_available"]
            _save_local_db()
            return {"status": "ok", "filament": fil}
    raise HTTPException(status_code=404, detail="Filamento non trovato.")

@router.get("/admin/pricing")
def get_admin_pricing(auth: bool = Depends(verify_admin_auth)):
    """Restituisce il listino prezzi e promozioni per il pannello Admin."""
    return _load_pricing_settings()

@router.post("/admin/pricing")
def update_admin_pricing(payload: Dict[str, Any], auth: bool = Depends(verify_admin_auth)):
    """Salva le nuove impostazioni del listino prezzi e promozioni."""
    current = _load_pricing_settings()
    for k, v in payload.items():
        if k in current:
            if k == "promo_3x2_enabled":
                current[k] = bool(v)
            else:
                try:
                    current[k] = round(float(v), 2)
                except (ValueError, TypeError):
                    pass
    _save_pricing_settings(current)
    return {"success": True, "settings": current}

# ----------------- GESTIONE COUPON ADMIN -----------------

@router.get("/admin/coupons")
def admin_list_coupons(auth: bool = Depends(verify_admin_auth)):
    """Restituisce l'elenco di tutti i coupon sconto configurati."""
    return get_coupons()

@router.post("/admin/coupons")
def admin_create_coupon(payload: Dict[str, Any], auth: bool = Depends(verify_admin_auth)):
    """Crea un nuovo coupon sconto."""
    code = str(payload.get("code", "")).strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Il codice coupon è obbligatorio.")
    
    coupons = get_coupons()
    if any(str(c.get("code", "")).strip().upper() == code for c in coupons):
        raise HTTPException(status_code=400, detail=f"Un coupon con codice '{code}' esiste già.")
    
    c_type = str(payload.get("type", "percentage")).lower()
    if c_type not in ["percentage", "fixed"]:
        c_type = "percentage"
        
    try:
        value = round(float(payload.get("value", 0.0)), 2)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Valore sconto non valido.")
    
    if value <= 0:
        raise HTTPException(status_code=400, detail="Il valore dello sconto deve essere maggiore di zero.")
        
    try:
        min_spend = max(0.0, round(float(payload.get("min_spend", 0.0)), 2))
    except (ValueError, TypeError):
        min_spend = 0.0

    new_coupon = {
        "id": f"coupon-{uuid.uuid4().hex[:8]}",
        "code": code,
        "type": c_type,
        "value": value,
        "active": bool(payload.get("active", True)),
        "min_spend": min_spend
    }
    coupons.append(new_coupon)
    save_coupons(coupons)
    return {"status": "ok", "coupon": new_coupon}

@router.put("/admin/coupons/{coupon_id}")
def admin_update_coupon(coupon_id: str, payload: Dict[str, Any], auth: bool = Depends(verify_admin_auth)):
    """Modifica un coupon esistente."""
    coupons = get_coupons()
    idx = next((i for i, c in enumerate(coupons) if str(c.get("id")) == coupon_id or str(c.get("code", "")).upper() == coupon_id.upper()), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Coupon non trovato.")
    
    current = coupons[idx]
    if "code" in payload:
        new_code = str(payload["code"]).strip().upper()
        if new_code:
            if any(str(c.get("code", "")).strip().upper() == new_code and i != idx for i, c in enumerate(coupons)):
                raise HTTPException(status_code=400, detail=f"Un coupon con codice '{new_code}' esiste già.")
            current["code"] = new_code
    
    if "type" in payload:
        t = str(payload["type"]).lower()
        if t in ["percentage", "fixed"]:
            current["type"] = t
            
    if "value" in payload:
        try:
            val = round(float(payload["value"]), 2)
            if val > 0:
                current["value"] = val
        except (ValueError, TypeError):
            pass

    if "min_spend" in payload:
        try:
            current["min_spend"] = max(0.0, round(float(payload["min_spend"]), 2))
        except (ValueError, TypeError):
            pass
            
    if "active" in payload:
        current["active"] = bool(payload["active"])

    coupons[idx] = current
    save_coupons(coupons)
    return {"status": "ok", "coupon": current}

@router.post("/admin/coupons/{coupon_id}/toggle")
def admin_toggle_coupon(coupon_id: str, auth: bool = Depends(verify_admin_auth)):
    """Inverte lo stato del coupon [Attivo / Disattivato]."""
    coupons = get_coupons()
    for c in coupons:
        if str(c.get("id")) == coupon_id or str(c.get("code", "")).upper() == coupon_id.upper():
            c["active"] = not c.get("active", True)
            save_coupons(coupons)
            return {"status": "ok", "coupon": c}
    raise HTTPException(status_code=404, detail="Coupon non trovato.")

@router.delete("/admin/coupons/{coupon_id}")
def admin_delete_coupon(coupon_id: str, auth: bool = Depends(verify_admin_auth)):
    """Elimina definitivamente un coupon sconto."""
    coupons = get_coupons()
    new_list = [c for c in coupons if str(c.get("id")) != coupon_id and str(c.get("code", "")).upper() != coupon_id.upper()]
    if len(new_list) == len(coupons):
        raise HTTPException(status_code=404, detail="Coupon non trovato.")
    save_coupons(new_list)
    return {"status": "ok", "message": "Coupon eliminato con successo."}

# ----------------- GESTIONE ORDINI ADMIN -----------------

@router.get("/admin/orders")
def admin_get_orders(auth: bool = Depends(verify_admin_auth)):
    """Restituisce tutti gli ordini registrati con gli articoli associati."""
    _load_local_db()
    enriched_orders = []
    for order in _LOCAL_ORDERS_DB:
        items = [it for it in _LOCAL_ORDER_ITEMS_DB if it["order_id"] == order["id"]]
        enriched = dict(order)
        enriched["items"] = items
        enriched_orders.append(enriched)
    return enriched_orders

@router.post("/admin/orders/{order_id}/status")
def admin_update_order_status(order_id: str, payload: Dict[str, Any], auth: bool = Depends(verify_admin_auth)):
    """Aggiorna lo stato dell'ordine e, se impostato su 'spedito', invia l'email al cliente."""
    _load_local_db()
    new_status = payload.get("status")
    tracking = payload.get("tracking_number")

    for ord_item in _LOCAL_ORDERS_DB:
        if ord_item["id"] == order_id or ord_item["order_number"] == order_id:
            old_status = ord_item["order_status"]
            ord_item["order_status"] = new_status
            if tracking:
                ord_item["tracking_number"] = tracking

            _save_local_db()

            # Se lo stato diventa 'spedito', invia l'email automatica al cliente
            if new_status in ["spedito", "pronto_ritiro"] and old_status != new_status:
                try:
                    send_order_shipped_notification(ord_item)
                except Exception as e:
                    print(f"[WARN] Errore invio notifica spedizione: {e}")

            return {"status": "ok", "order": ord_item}
    raise HTTPException(status_code=404, detail="Ordine non trovato.")

@router.delete("/admin/orders/{order_id}")
@router.post("/admin/orders/{order_id}/delete")
def admin_delete_order(order_id: str, auth: bool = Depends(verify_admin_auth)):
    """Elimina definitivamente un ordine dal database gestionale e dai file JSON."""
    global _LOCAL_ORDERS_DB, _LOCAL_ORDER_ITEMS_DB
    _load_local_db()

    target_order = None
    for o in _LOCAL_ORDERS_DB:
        if str(o.get("id")) == str(order_id) or str(o.get("order_number")) == str(order_id):
            target_order = o
            break

    if not target_order:
        raise HTTPException(status_code=404, detail="Ordine non trovato nel database.")

    target_id = target_order.get("id")
    target_num = target_order.get("order_number")

    _LOCAL_ORDERS_DB = [o for o in _LOCAL_ORDERS_DB if str(o.get("id")) != str(target_id) and str(o.get("order_number")) != str(target_num)]
    _LOCAL_ORDER_ITEMS_DB = [it for it in _LOCAL_ORDER_ITEMS_DB if str(it.get("order_id")) != str(target_id)]

    _save_local_db()
    print(f"[ADMIN] Ordine #{target_num} (ID: {target_id}) eliminato definitivamente.")
    return {
        "success": True,
        "status": "ok",
        "deleted_id": target_id,
        "deleted_order_number": target_num,
        "message": f"Ordine #{target_num} eliminato con successo."
    }

@router.get("/admin/items/{item_id}/download-3mf")
async def api_download_order_item_3mf(
    item_id: str,
    auth: bool = Depends(verify_admin_auth)
):
    """
    GENERAZIONE AUTOMATICA 3MF CON UN CLIC:
    Compila istantaneamente il file .3mf per Snapmaker U1 con zero torre di spurgo.
    Richiede autenticazione amministratore tramite Header (X-Admin-Pin, X-Admin-Token, Bearer)
    oppure Query string (?pin=... o ?token=...) per download diretto dal browser.
    """
    item = next((it for it in _LOCAL_ORDER_ITEMS_DB if str(it.get("id")) == str(item_id)), None)
    if not item:
        _load_local_db()
        item = next((it for it in _LOCAL_ORDER_ITEMS_DB if str(it.get("id")) == str(item_id)), None)

    if not item:
        raise HTTPException(status_code=404, detail=f"Articolo non trovato nel database: {item_id}")

    order = next((o for o in _LOCAL_ORDERS_DB if str(o.get("id")) == str(item.get("order_id"))), {"order_number": "ORD"})
    order_number = order.get("order_number", "ORD")

    try:
        import tempfile
        file_path, filename = compile_order_item_to_3mf(order_number, item)
        resolved_fp = Path(file_path).resolve()
        temp_dir = Path(tempfile.gettempdir()).resolve()
        if not (resolved_fp == temp_dir or resolved_fp.is_relative_to(temp_dir)):
            raise HTTPException(status_code=403, detail="Percorso file 3MF non autorizzato.")

        with open(resolved_fp, "rb") as f:
            bytes_3mf = f.read()

        # Sanitize filename in header
        safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)

        return Response(
            content=bytes_3mf,
            media_type="application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore generazione 3MF per {item_id}: {str(e)}")
