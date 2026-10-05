"""
Servizio di Notifiche Email Resend per Snapmaker U1 Storefront.
Gestisce l'invio sicuro di notifiche al proprietario dello store (STORE_OWNER_EMAIL)
e al cliente finale per la conferma d'ordine.
"""
import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

logger = logging.getLogger("notification_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [Resend] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
STORE_OWNER_EMAIL = os.getenv("STORE_OWNER_EMAIL", "antonello.lauretti82@gmail.com")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

def _send_resend_email(from_addr: str, to_addrs: List[str], subject: str, html_content: str) -> Optional[Dict[str, Any]]:
    """Invia email con libreria resend ufficiale se disponibile, o tramite API REST diretta."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning(f"RESEND_API_KEY non impostata. Email a {to_addrs} con oggetto '{subject}' simulata in console.")
        return {"id": "simulated", "status": "simulated"}

    try:
        import resend
        resend.api_key = api_key
        params = {
            "from": from_addr,
            "to": to_addrs,
            "subject": subject,
            "html": html_content,
        }
        email_res = resend.Emails.send(params)
        logger.info(f"Notifica Resend inviata con successo: {email_res}")
        return email_res
    except ImportError:
        # Fallback a richiesta HTTP nativa
        url = "https://api.resend.com/emails"
        req_data = json.dumps({
            "from": from_addr,
            "to": to_addrs,
            "subject": subject,
            "html": html_content
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            logger.info(f"Notifica Resend inviata via REST con successo: {body}")
            return body

def send_admin_new_order_alert(order: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Invia notifica istantanea all'amministratore (STORE_OWNER_EMAIL)."""
    try:
        order_id = order.get("order_number") or order.get("id", "N/D")
        total = f"{float(order.get('total_amount', 0)):.2f}"
        from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
        store_owner = os.getenv("STORE_OWNER_EMAIL", "antonello.lauretti82@gmail.com")

        items_summary = "".join([
            f"<li><strong>{it.get('product_title')}</strong>: '{it.get('custom_text_line1')}' "
            f"(Base: {it.get('base_color_name')} | Testo: {it.get('text_color_name')} | Font: {it.get('font_id')})</li>"
            for it in items
        ])

        html = f"""
        <div style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 8px;">
            <h2 style="color: #38bdf8;">Nuovo Ordine Ricevuto! #{order_id}</h2>
            <p><strong>Nuovo ordine completato:</strong> #{order_id}<br>Totale: <strong>{total} €</strong></p>
            <div style="background: #1e293b; padding: 14px; border-radius: 6px; margin: 16px 0;">
                <p><strong>Cliente:</strong> {order.get('customer_name', 'N/D')}</p>
                <p><strong>Email:</strong> {order.get('customer_email', 'N/D')}</p>
                <p><strong>Cellulare Corriere:</strong> {order.get('customer_phone', 'N/D')}</p>
                <p><strong>Indirizzo:</strong> {order.get('shipping_address', 'N/D')}, {order.get('shipping_zip', '')} {order.get('shipping_city', '')} ({order.get('shipping_province', '')})</p>
                <p><strong>Transazione PayPal:</strong> {order.get('paypal_capture_id') or order.get('paypal_order_id', 'N/D')}</p>
            </div>
            <h3>Pezzi da stampare ({len(items)}):</h3>
            <ul>
                {items_summary}
            </ul>
        </div>
        """
        return _send_resend_email(
            from_addr=from_email,
            to_addrs=[store_owner],
            subject=f"Nuovo Ordine Ricevuto! #{order_id}",
            html_content=html
        )
    except Exception as e:
        logger.error(f"Errore durante l'invio dell'email con Resend: {str(e)}")
        return None

def send_customer_order_confirmation(order: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Invia email di conferma d'ordine al cliente, senza bloccare il flusso in caso di errore."""
    customer_email = order.get("customer_email")
    if not customer_email:
        return None

    try:
        order_id = order.get("order_number") or order.get("id", "N/D")
        total = f"{float(order.get('total_amount', 0)):.2f}"
        from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

        html = f"""
        <div style="font-family: Arial, sans-serif; background: #ffffff; color: #1e293b; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h2 style="color: #0284c7;">Conferma Ricezione Ordine #{order_id}</h2>
            <p>Gentile <strong>{order.get('customer_name', 'Cliente')}</strong>,<br>
            abbiamo ricevuto con successo il tuo ordine personalizzato su GadgetPoint.it!</p>
            <p><strong>Codice Ordine:</strong> #{order_id}<br><strong>Totale Pagato:</strong> {total} €</p>
            <p>I tuoi oggetti sono ora in coda di produzione per la stampa 3D multicolore con Snapmaker U1.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <small style="color: #64748b;">GadgetPoint.it - Stampa 3D Personalizzata di Precisione</small>
        </div>
        """
        return _send_resend_email(
            from_addr=from_email,
            to_addrs=[customer_email],
            subject=f"Conferma Ordine #{order_id} - GadgetPoint.it",
            html_content=html
        )
    except Exception as e:
        logger.warning(f"Invio email al cliente non riuscito (es. restrizione sandbox Resend): {str(e)}")
        return None
