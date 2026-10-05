"""
Servizio di Notifiche Email Resend per Snapmaker U1 Storefront.
Gestisce l'invio sicuro di notifiche al proprietario dello store (STORE_OWNER_EMAIL)
e al cliente finale per la conferma d'ordine (sia PayPal che Contanti al Ritiro).
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

        delivery_method = order.get("delivery_method", "shipping")
        is_pickup = delivery_method == "pickup"
        payment_method = order.get("payment_method", "paypal")
        is_cash = payment_method == "cash_on_pickup"

        items_summary = "".join([
            f"<li><strong>{it.get('product_title')}</strong>: '{it.get('custom_text_line1')}' "
            f"(Base: {it.get('base_color_name')} | Testo: {it.get('text_color_name')} | Font: {it.get('font_id')})</li>"
            for it in items
        ])

        coupon_line = ""
        if order.get("coupon_code"):
            coupon_line = f"<p><strong>🎟️ Coupon Applicato:</strong> {order.get('coupon_code')}</p>"

        if is_cash:
            payment_line = f"<p><strong>💵 Metodo Pagamento:</strong> <span style='color: #f59e0b; font-weight: bold;'>CONTANTI AL RITIRO</span> (Da incassare: {total} €)</p>"
        else:
            tx_id = order.get('paypal_capture_id') or order.get('paypal_order_id', 'N/D')
            payment_line = f"<p><strong>💳 Metodo Pagamento:</strong> PayPal (ID Transazione: {tx_id})</p>"

        if is_pickup:
            delivery_line = "<p><strong>🤝 Modalità Consegna:</strong> Ritiro a mano di persona (0,00 €)</p>"
        else:
            delivery_line = f"""
            <p><strong>🚚 Spedizione Corriere:</strong> BRT / SDA</p>
            <p><strong>Indirizzo:</strong> {order.get('shipping_address', 'N/D')}, {order.get('shipping_zip', '')} {order.get('shipping_city', '')} ({order.get('shipping_province', '')})</p>
            """

        html = f"""
        <div style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 8px;">
            <h2 style="color: #38bdf8;">Nuovo Ordine Ricevuto! #{order_id}</h2>
            <p><strong>Codice Ordine:</strong> #{order_id}<br>Totale: <strong>{total} €</strong></p>
            <div style="background: #1e293b; padding: 14px; border-radius: 6px; margin: 16px 0;">
                <p><strong>Cliente:</strong> {order.get('customer_name', 'N/D')}</p>
                <p><strong>Email:</strong> {order.get('customer_email', 'N/D')}</p>
                <p><strong>Cellulare:</strong> {order.get('customer_phone', 'N/D')}</p>
                {delivery_line}
                {payment_line}
                {coupon_line}
                {f"<p><strong>Note Ordine:</strong> {order.get('order_notes')}</p>" if order.get('order_notes') else ""}
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
            subject=f"Nuovo Ordine #{order_id} ({'Contanti al Ritiro' if is_cash else 'PayPal'})",
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

        delivery_method = order.get("delivery_method", "shipping")
        is_pickup = delivery_method == "pickup"
        payment_method = order.get("payment_method", "paypal")
        is_cash = payment_method == "cash_on_pickup"

        if is_cash:
            pay_desc = f"<p><strong>Metodo di Pagamento:</strong> Contanti al momento del ritiro<br><strong>Importo da saldare:</strong> <strong>{total} €</strong></p>"
            delivery_desc = "<p><strong>Consegna:</strong> <strong>Ritiro a mano di persona (Gratuito)</strong>.<br>I tuoi articoli sono stati inseriti nella nostra coda di stampa 3D. Ti contatteremo via email e cellulare non appena l'ordine sarà pronto per il ritiro!</p>"
            subject = f"Conferma Ordine #{order_id} - Ritiro a Mano & Contanti - GadgetPoint.it"
        else:
            pay_desc = f"<p><strong>Metodo di Pagamento:</strong> PayPal (Pagamento confermato)<br><strong>Totale Pagato:</strong> <strong>{total} €</strong></p>"
            if is_pickup:
                delivery_desc = "<p><strong>Consegna:</strong> Ritiro a mano di persona.<br>Ti invieremo un aggiornamento appena i pezzi saranno pronti per il ritiro!</p>"
            else:
                delivery_desc = f"<p><strong>Consegna:</strong> Corriere Espresso BRT / SDA.<br>Destinazione: {order.get('shipping_address')}, {order.get('shipping_city')}</p>"
            subject = f"Conferma Ricezione Ordine #{order_id} - GadgetPoint.it"

        coupon_line = ""
        if order.get("coupon_code"):
            coupon_line = f"<p><strong>Codice Sconto Applicato:</strong> {order.get('coupon_code')}</p>"

        html = f"""
        <div style="font-family: Arial, sans-serif; background: #ffffff; color: #1e293b; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h2 style="color: #0284c7;">Conferma Ricezione Ordine #{order_id}</h2>
            <p>Gentile <strong>{order.get('customer_name', 'Cliente')}</strong>,<br>
            grazie per il tuo ordine personalizzato su GadgetPoint.it!</p>
            <div style="background: #f8fafc; padding: 16px; border-radius: 6px; margin: 16px 0; border: 1px solid #e2e8f0;">
                <p><strong>Codice Ordine:</strong> #{order_id}</p>
                {pay_desc}
                {delivery_desc}
                {coupon_line}
            </div>
            <p>I tuoi oggetti sono ora in produzione con tecnologia di stampa 3D multicolore Snapmaker U1 ad alta precisione.</p>
            <div style="margin: 24px 0; padding: 16px; background-color: #f3f4f6; border-radius: 8px; border-left: 4px solid #10b981; text-align: center;">
                <p style="margin: 0 0 6px 0; font-size: 14px; color: #374151; font-weight: 600;">Un piccolo regalo per il tuo prossimo ordine!</p>
                <p style="margin: 0; font-size: 13px; color: #4b5563;">Usa il codice coupon <strong style="color: #10b981; font-size: 15px; letter-spacing: 1px;">RIECCOMI5</strong> al carrello per ottenere subito il <strong>5% di sconto</strong> sul tuo prossimo acquisto personalizzato.</p>
            </div>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <small style="color: #64748b;">GadgetPoint.it - Stampa 3D Personalizzata di Precisione</small>
        </div>
        """
        return _send_resend_email(
            from_addr=from_email,
            to_addrs=[customer_email],
            subject=subject,
            html_content=html
        )
    except Exception as e:
        logger.warning(f"Invio email al cliente non riuscito: {str(e)}")
        return None
