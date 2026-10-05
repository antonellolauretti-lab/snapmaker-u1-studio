"""
Servizio di Notifiche Email Transazionali via Resend API per Snapmaker U1 Storefront.
1. Conferma ordine al cliente
2. Notifica istantanea all'amministratore (antonello.lauretti@gmail.com)
3. Notifica di avvenuta spedizione con corriere espresso BRT / SDA
"""
import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RESEND_API_URL = "https://api.resend.com/emails"

def get_resend_config() -> Dict[str, str]:
    """Recupera la configurazione email corrente dall'ambiente con fallback sicuri."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    from_email = (os.environ.get("FROM_EMAIL") or os.environ.get("RESEND_FROM_EMAIL") or "ordini@gadgetpoint.it").strip()
    store_owner_email = (os.environ.get("STORE_OWNER_EMAIL") or os.environ.get("ADMIN_EMAIL") or "antonello.lauretti@gmail.com").strip()
    app_url = os.environ.get("APP_URL", "http://localhost:8000").rstrip("/")
    return {
        "api_key": api_key,
        "from_email": from_email,
        "store_owner_email": store_owner_email,
        "app_url": app_url
    }

def _send_email(to_email: str, subject: str, html_body: str) -> Dict[str, Any]:
    """Invia un'email transazionale tramite l'API Resend."""
    cfg = get_resend_config()
    if not cfg["api_key"]:
        print(f"[RESEND SIMULATION] API Key non impostata. Email verso '{to_email}' simulata. Oggetto: {subject}")
        return {"id": "simulated_id", "status": "simulated"}

    payload = {
        "from": cfg["from_email"],
        "to": [to_email],
        "subject": subject,
        "html": html_body
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        RESEND_API_URL,
        data=req_data,
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        raise RuntimeError(f"Errore invio email Resend ({e.code}): {err_msg}")


def send_customer_order_confirmation(order: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Invia l'email di conferma d'ordine al cliente finale."""
    items_html = ""
    for idx, item in enumerate(items, start=1):
        promo_badge = '<span style="background:#22c55e;color:#fff;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:bold;margin-left:6px;">OMAGGIO 3x2</span>' if item.get("is_free_promo") else ""
        price_display = f"<s>{item.get('unit_price', 0):.2f} €</s> <strong style='color:#16a34a;'>0,00 €</strong>" if item.get("is_free_promo") else f"<strong>{item.get('unit_price', 0):.2f} €</strong>"
        
        t2_str = f"<br><small style='color:#666;'>Seconda riga: <em>{item.get('custom_text_line2')}</em></small>" if item.get("custom_text_line2") else ""
        icon_str = f" - Simbolo: {item.get('icon_id')}" if item.get("icon_id") and item.get("icon_id") != "none" else ""

        items_html += f"""
        <div style="border-bottom: 1px solid #e5e7eb; padding: 12px 0;">
            <div style="font-size: 15px; font-weight: 600; color: #111827;">
                #{idx} {item.get('product_title', 'Oggetto 3D')} {promo_badge}
            </div>
            <div style="font-size: 13px; color: #4b5563; margin-top: 4px;">
                Testo: <strong style="color: #1f2937;">{item.get('custom_text_line1', '')}</strong> (Font: {item.get('font_id', 'Standard')}){icon_str}
                {t2_str}
            </div>
            <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                Base: <span style="display:inline-block;width:10px;height:10px;background:{item.get('base_color_hex')};border-radius:50%;margin-right:3px;"></span>{item.get('base_color_name')} | 
                Scritta: <span style="display:inline-block;width:10px;height:10px;background:{item.get('text_color_hex')};border-radius:50%;margin-right:3px;"></span>{item.get('text_color_name')}
            </div>
            <div style="text-align: right; margin-top: 6px; font-size: 14px;">
                {price_display}
            </div>
        </div>
        """

    promo_row = ""
    if float(order.get("discount_amount", 0)) > 0:
        promo_row = f"""
        <tr>
            <td style="padding: 6px 0; color: #16a34a; font-weight: 600;">Promo 3x2 (1 articolo omaggio):</td>
            <td style="padding: 6px 0; text-align: right; color: #16a34a; font-weight: 600;">-{float(order.get('discount_amount', 0)):.2f} €</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
            
            <div style="text-align: center; border-bottom: 2px solid #f3f4f6; padding-bottom: 20px;">
                <h1 style="color: #0f172a; margin: 0; font-size: 24px; font-weight: 800;">Conferma Ordine #{order.get('order_number')}</h1>
                <p style="color: #64748b; font-size: 14px; margin-top: 6px;">Grazie per il tuo acquisto su GadgetPoint.it!</p>
            </div>

            <div style="margin: 24px 0;">
                <p style="font-size: 15px; color: #334155; line-height: 1.5;">
                    Ciao <strong>{order.get('customer_name')}</strong>,<br>
                    il tuo ordine è stato ricevuto con successo ed è entrato in coda per la produzione 3D personalizzata.
                </p>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <h3 style="margin-top: 0; color: #1e293b; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Riepilogo Articoli</h3>
                {items_html}

                <table style="width: 100%; margin-top: 16px; font-size: 14px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                    <tr>
                        <td style="padding: 6px 0; color: #64748b;">Subtotale articoli:</td>
                        <td style="padding: 6px 0; text-align: right; color: #1e293b;">{float(order.get('subtotal_amount', 0)):.2f} €</td>
                    </tr>
                    {promo_row}
                    <tr>
                        <td style="padding: 6px 0; color: #64748b;">Spedizione espressa (BRT / SDA):</td>
                        <td style="padding: 6px 0; text-align: right; color: #1e293b;">{float(order.get('shipping_amount', 5.00)):.2f} €</td>
                    </tr>
                    <tr style="border-top: 2px solid #cbd5e1; font-size: 17px; font-weight: bold;">
                        <td style="padding: 10px 0; color: #0f172a;">Totale Pagato:</td>
                        <td style="padding: 10px 0; text-align: right; color: #0f172a;">{float(order.get('total_amount', 0)):.2f} €</td>
                    </tr>
                </table>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <h3 style="margin-top: 0; color: #1e293b; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Indirizzo di Spedizione</h3>
                <p style="margin: 0; font-size: 14px; color: #334155; line-height: 1.6;">
                    <strong>{order.get('customer_name')}</strong><br>
                    {order.get('shipping_address')}<br>
                    {order.get('shipping_zip')} {order.get('shipping_city')} ({order.get('shipping_province')})<br>
                    Telefono per corriere: <strong>{order.get('customer_phone')}</strong>
                </p>
            </div>

            <div style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px;">
                Riceverai un'ulteriore email non appena il pacco verrà affidato al corriere con il relativo codice di tracciamento.
            </div>
        </div>
    </body>
    </html>
    """
    return _send_email(
        to_email=order.get("customer_email"),
        subject=f"✅ Ricevuta e Conferma Ordine #{order.get('order_number')} - GadgetPoint.it",
        html_body=html
    )


def send_admin_new_order_alert(order: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Invia notifica istantanea all'amministratore del negozio."""
    cfg = get_resend_config()
    items_list_txt = "".join([
        f"<li><strong>{it.get('product_title')}</strong>: '{it.get('custom_text_line1')}' | Base: {it.get('base_color_name')} | Testo: {it.get('text_color_name')} | Font: {it.get('font_id')}</li>"
        for it in items
    ])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 24px;">
            <h2 style="color: #38bdf8; margin-top: 0;">🚀 NUOVO ORDINE DA STAMPARE: #{order.get('order_number')}</h2>
            <p style="font-size: 16px;">È arrivato un nuovo ordine pagato via PayPal!</p>
            
            <div style="background: #0f172a; padding: 16px; border-radius: 6px; margin: 16px 0; border: 1px solid #334155;">
                <p><strong>Cliente:</strong> {order.get('customer_name')}</p>
                <p><strong>Email:</strong> {order.get('customer_email')}</p>
                <p><strong>Telefono BRT/SDA:</strong> <span style="color:#f59e0b;font-weight:bold;">{order.get('customer_phone')}</span></p>
                <p><strong>Destinazione:</strong> {order.get('shipping_address')}, {order.get('shipping_zip')} {order.get('shipping_city')} ({order.get('shipping_province')})</p>
                <p><strong>Totale Incassato:</strong> <span style="color:#22c55e;font-size:18px;font-weight:bold;">{float(order.get('total_amount', 0)):.2f} €</span></p>
                <p><strong>ID Transazione PayPal:</strong> {order.get('paypal_capture_id') or order.get('paypal_order_id')}</p>
            </div>

            <h3 style="color: #94a3b8;">Pezzi da stampare ({len(items)}):</h3>
            <ul style="line-height: 1.8; color: #e2e8f0;">
                {items_list_txt}
            </ul>

            <div style="margin-top: 24px; text-align: center;">
                <a href="{cfg['app_url']}/admin" style="background: #0284c7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Apri Gestionale e Scarica 3MF
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return _send_email(
        to_email=cfg["store_owner_email"],
        subject=f"🔔 [GadgetPoint Admin] Nuovo Ordine Ricevuto: #{order.get('order_number')} ({float(order.get('total_amount', 0)):.2f} €)",
        html_body=html
    )


def send_order_shipped_notification(order: Dict[str, Any]) -> Dict[str, Any]:
    """Invia email al cliente quando l'amministratore imposta lo stato su 'Spedito'."""
    courier = order.get("courier", "Corriere espresso BRT / SDA")
    tracking = order.get("tracking_number") or "In caricamento nelle prossime ore dal corriere"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; border: 1px solid #e5e7eb; padding: 32px;">
            <div style="text-align: center; border-bottom: 2px solid #f3f4f6; padding-bottom: 20px;">
                <h1 style="color: #0f172a; margin: 0; font-size: 24px; font-weight: 800;">📦 Il tuo ordine #{order.get('order_number')} è stato spedito!</h1>
            </div>

            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin-top: 20px;">
                Gentile <strong>{order.get('customer_name')}</strong>,<br>
                i tuoi pezzi personalizzati sono stati stampati, rifiniti e accuratamente imballati. Il pacco è stato affidato al corriere!
            </p>

            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; font-size: 14px; color: #065f46;"><strong>Corriere Incaricato:</strong> {courier}</p>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #065f46;"><strong>Lettera di Vettura / Tracking:</strong> <span style="font-family: monospace; font-size: 15px; font-weight: bold;">{tracking}</span></p>
                <p style="margin: 8px 0 0 0; font-size: 13px; color: #047857;">La consegna è prevista indicativamente entro 24/48 ore lavorative all'indirizzo comunicato.</p>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                <h4 style="margin: 0 0 8px 0; color: #334155;">Indirizzo di Consegna:</h4>
                <p style="margin: 0; font-size: 13px; color: #64748b;">
                    {order.get('shipping_address')}, {order.get('shipping_zip')} {order.get('shipping_city')} ({order.get('shipping_province')})<br>
                    Recapito telefonico per il corriere: {order.get('customer_phone')}
                </p>
            </div>
            
            <p style="font-size: 13px; color: #64748b; text-align: center; margin-top: 28px;">
                Grazie per aver scelto GadgetPoint.it!
            </p>
        </div>
    </body>
    </html>
    """
    return _send_email(
        to_email=order.get("customer_email"),
        subject=f"📦 Spedizione in Corso: Il tuo pacco #{order.get('order_number')} è partito con {courier}",
        html_body=html
    )
