"""
Router FastAPI per lo Storefront E-Commerce e il Gestionale Admin Snapmaker U1.
Collega:
- Supabase (PostgreSQL) per tabelle filaments, orders, order_items
- PayPal REST API v2 per ordini e pagamenti
- Resend per notifiche email automatiche
- Snapmaker3MFPackager per il download istantaneo del 3MF nativo (zero prime tower)
"""
import os
import sys
import uuid
import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

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

from ecommerce.cart_engine import calculate_cart_totals
from ecommerce.services.paypal_service import create_paypal_order, capture_paypal_order
from ecommerce.services.resend_service import (
    send_customer_order_confirmation,
    send_admin_new_order_alert,
    send_order_shipped_notification
)
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

DATA_DIR = PROJECT_ROOT / "ecommerce" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "orders_db.json"

def _load_local_db():
    global _LOCAL_ORDERS_DB, _LOCAL_ORDER_ITEMS_DB, _LOCAL_FILAMENTS_DB
    if DB_FILE.exists() and DB_FILE.stat().st_size > 0:
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _LOCAL_ORDERS_DB = data.get("orders", [])
                _LOCAL_ORDER_ITEMS_DB = data.get("order_items", [])
                if data.get("filaments"):
                    _LOCAL_FILAMENTS_DB = data["filaments"]
        except Exception as e:
            print(f"[WARN] Impossibile caricare {DB_FILE}: {e}")

def _save_local_db():
    try:
        content = json.dumps({
            "orders": _LOCAL_ORDERS_DB,
            "order_items": _LOCAL_ORDER_ITEMS_DB,
            "filaments": _LOCAL_FILAMENTS_DB
        }, indent=2, ensure_ascii=False, default=str)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[WARN] Impossibile salvare {DB_FILE}: {e}")

_load_local_db()

def verify_admin_auth(
    x_admin_pin: Optional[str] = Header(None),
    pin: Optional[str] = Query(None)
):
    expected_pin = os.getenv("ADMIN_PIN", "L21dic82").strip()
    provided = str(x_admin_pin or pin or "").strip()
    if not provided or provided != expected_pin:
        raise HTTPException(status_code=401, detail="PIN di accesso non valido.")
    return True

@router.post("/admin/verify-pin")
@router.get("/admin/verify-pin")
async def api_verify_pin(
    request: Request,
    x_admin_pin: Optional[str] = Header(None),
    pin: Optional[str] = Query(None)
):
    """Endpoint dedicato per la verifica della chiave PIN admin."""
    expected_pin = os.getenv("ADMIN_PIN", "L21dic82").strip()
    provided = ""

    # 1. Prova da JSON body (se presente in POST)
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                provided = body.get("pin") or body.get("admin_pin") or ""
            elif isinstance(body, str):
                provided = body
        except Exception:
            pass

    # 2. Fallback su Header o Query string
    if not provided:
        provided = x_admin_pin or pin or ""

    provided = str(provided).strip()
    if not provided or provided != expected_pin:
        raise HTTPException(status_code=401, detail="PIN non corretto!")
    return {"status": "ok", "valid": True, "message": "Autenticazione riuscita."}

DEFAULT_PRICING_SETTINGS = {
    "keychain_standard": 4.90,
    "keychain_complex": 6.90,
    "desk_sign": 9.90,
    "extra_line2": 2.00,
    "shipping_fixed": 5.00,
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
# 1. STOREFRONT PUBBLICO (FILAMENTI, LISTINO & CARRELLO)
# ==============================================================================

@router.get("/store/filaments")
def get_available_filaments():
    """Restituisce esclusivamente i filamenti contrassegnati come DISPONIBILI per lo Storefront."""
    return [fil for fil in _LOCAL_FILAMENTS_DB if fil.get("is_available") is True]

@router.get("/store/pricing")
def get_store_pricing():
    """Restituisce il listino prezzi e le promozioni correnti per lo Storefront."""
    return _load_pricing_settings()

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

@router.post("/store/calculate-cart")
def api_calculate_cart(payload: Dict[str, Any]):
    """Calcola in modo deterministico il totale, promo 3x2 e spedizione 5,00 €."""
    items = payload.get("items", [])
    totals = calculate_cart_totals(items)
    return {
        "item_count": totals["item_count"],
        "subtotal": float(totals["subtotal"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": float(totals["shipping_amount"]),
        "total_amount": float(totals["total_amount"]),
        "free_items_count": totals["free_items_count"],
        "promo_applied": totals["promo_applied"],
        "promo_label": totals["promo_label"]
    }

# ==============================================================================
# 2. CHECKOUT & INTEGRAZIONE PAYPAL SMART BUTTONS
# ==============================================================================

@router.post("/store/orders/create-paypal")
def api_create_paypal_order(payload: Dict[str, Any]):
    """Crea un ordine PayPal sicuro con importi calcolati dal server."""
    items = payload.get("items", [])
    customer_info = payload.get("customerInfo", {})

    if not items:
        raise HTTPException(status_code=400, detail="Il carrello è vuoto.")

    # Se le credenziali PayPal non sono fornite, genera un ID mock di test
    if not os.environ.get("PAYPAL_CLIENT_ID"):
        mock_id = f"PAYPAL_MOCK_{uuid.uuid4().hex[:10].upper()}"
        return {"id": mock_id, "status": "CREATED", "mode": "mock"}

    try:
        order_res = create_paypal_order(items, customer_info)
        return order_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store/orders/capture-paypal")
def api_capture_paypal_order(payload: Dict[str, Any]):
    """Cattura il pagamento, salva l'ordine in DB e avvia le notifiche Resend."""
    paypal_order_id = payload.get("paypalOrderId")
    items = payload.get("items", [])
    customer_info = payload.get("customerInfo", {})

    if not paypal_order_id or not items:
        raise HTTPException(status_code=400, detail="Dati ordine mancanti.")

    # Calcolo totale verificato
    totals = calculate_cart_totals(items)
    
    # Genera codice ordine
    now = datetime.datetime.now()
    order_number = f"U1-{now.strftime('%Y%m%d')}-{len(_LOCAL_ORDERS_DB) + 1:04d}"
    order_id = str(uuid.uuid4())

    capture_id = f"CAP_{uuid.uuid4().hex[:8]}"
    if os.environ.get("PAYPAL_CLIENT_ID") and not paypal_order_id.startswith("PAYPAL_MOCK_"):
        try:
            capture_res = capture_paypal_order(paypal_order_id)
            capture_id = capture_res.get("id", capture_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore cattura PayPal: {str(e)}")

    order_record = {
        "id": order_id,
        "order_number": order_number,
        "customer_name": customer_info.get("customer_name", "Cliente"),
        "customer_email": customer_info.get("customer_email", ""),
        "customer_phone": customer_info.get("customer_phone", ""),
        "shipping_address": customer_info.get("shipping_address", ""),
        "shipping_city": customer_info.get("shipping_city", ""),
        "shipping_zip": customer_info.get("shipping_zip", ""),
        "shipping_province": customer_info.get("shipping_province", ""),
        "order_notes": customer_info.get("order_notes", ""),
        "subtotal_amount": float(totals["subtotal"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": float(totals["shipping_amount"]),
        "total_amount": float(totals["total_amount"]),
        "paypal_order_id": paypal_order_id,
        "paypal_capture_id": capture_id,
        "payment_status": "paid",
        "order_status": "da_stampare",
        "courier": "BRT / SDA",
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

    # 3. Notifiche email via Resend
    try:
        send_customer_order_confirmation(order_record, saved_items)
        send_admin_new_order_alert(order_record, saved_items)
    except Exception as e:
        print(f"[WARN] Invio email non riuscito: {e}")

    return {
        "status": "success",
        "order_number": order_number,
        "customer_email": order_record["customer_email"],
        "total": order_record["total_amount"]
    }

@router.post("/store/orders/create-test")
def api_create_test_order(payload: Dict[str, Any]):
    """
    MODALITÀ TEST CHECKOUT:
    Crea e registra un ordine di test senza richiedere transazioni monetarie reali su PayPal.
    L'ordine comparirà all'istante nel gestionale /admin con stato 'da_stampare'
    e il pulsante 'Scarica 3MF per Snapmaker U1' funzionante.
    """
    items = payload.get("items", [])
    customer_info = payload.get("customerInfo", {})

    if not items:
        raise HTTPException(status_code=400, detail="Il carrello è vuoto.")

    totals = calculate_cart_totals(items)
    now = datetime.datetime.now()
    order_number = f"TEST-U1-{now.strftime('%Y%m%d')}-{len(_LOCAL_ORDERS_DB) + 1:04d}"
    order_id = str(uuid.uuid4())

    order_record = {
        "id": order_id,
        "order_number": order_number,
        "customer_name": customer_info.get("customer_name") or "Tester Sviluppatore",
        "customer_email": customer_info.get("customer_email") or "test@snapmaker-studio.it",
        "customer_phone": customer_info.get("customer_phone") or "340 0000000",
        "shipping_address": customer_info.get("shipping_address") or "Via Laboratorio 3D, 1",
        "shipping_city": customer_info.get("shipping_city") or "Roma",
        "shipping_zip": customer_info.get("shipping_zip") or "00100",
        "shipping_province": customer_info.get("shipping_province") or "RM",
        "order_notes": customer_info.get("order_notes") or "Ordine di Prova (Test Senza Pagamento)",
        "subtotal_amount": float(totals["subtotal"]),
        "discount_amount": float(totals["discount_amount"]),
        "shipping_amount": float(totals["shipping_amount"]),
        "total_amount": float(totals["total_amount"]),
        "paypal_order_id": f"TEST_SIMULATION_{uuid.uuid4().hex[:8].upper()}",
        "paypal_capture_id": f"TEST_CAP_{uuid.uuid4().hex[:8].upper()}",
        "payment_provider": "test_simulation",
        "payment_status": "paid",
        "order_status": "da_stampare",
        "courier": "BRT / SDA",
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

@router.get("/admin/orders")
def admin_get_orders(auth: bool = Depends(verify_admin_auth)):
    """Restituisce tutti gli ordini registrati con gli articoli associati."""
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
            if new_status == "spedito" and old_status != "spedito":
                try:
                    send_order_shipped_notification(ord_item)
                except Exception as e:
                    print(f"[WARN] Errore invio notifica spedizione: {e}")

            return {"status": "ok", "order": ord_item}
    raise HTTPException(status_code=404, detail="Ordine non trovato.")

@router.get("/admin/items/{item_id}/download-3mf")
async def api_download_order_item_3mf(item_id: str):
    """
    GENERAZIONE AUTOMATICA 3MF CON UN CLIC:
    Compila istantaneamente il file .3mf per Snapmaker U1 con zero torre di spurgo.
    Restituisce i byte direttamente al browser per il download senza blocchi o dipendenze da header.
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
        file_path, filename = compile_order_item_to_3mf(order_number, item)
        with open(file_path, "rb") as f:
            bytes_3mf = f.read()

        return Response(
            content=bytes_3mf,
            media_type="application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore generazione 3MF per {item_id}: {str(e)}")
