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

def get_notification_config() -> Dict[str, str]:
    """Recupera la configurazione email supportando tutti gli alias delle variabili d'ambiente."""
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    from_email = (
        os.getenv("FROM_EMAIL")
        or os.getenv("RESEND_FROM_EMAIL")
        or "onboarding@resend.dev"
    ).strip()
    store_owner = (
        os.getenv("ADMIN_NOTIFICATION_EMAIL")
        or os.getenv("STORE_OWNER_EMAIL")
        or os.getenv("ADMIN_EMAIL")
        or "antonello.lauretti82@gmail.com"
    ).strip()
    return {
        "api_key": api_key,
        "from_email": from_email,
        "store_owner": store_owner
    }

def _send_resend_email(from_addr: str, to_addrs: List[str], subject: str, html_content: str) -> Optional[Dict[str, Any]]:
    """Invia email con libreria resend ufficiale se disponibile, o tramite API REST diretta con logging diagnostico completo."""
    cfg = get_notification_config()
    api_key = cfg["api_key"]
    if not api_key:
        logger.error(
            f"[EMAIL NON CONFIGURATA] RESEND_API_KEY mancante! Impossibile inviare email a {to_addrs} (Oggetto: '{subject}'). "
            "Aggiungi la variabile 'RESEND_API_KEY' nella Dashboard di Render (Environment)."
        )
        return {"id": "simulated", "status": "simulated", "error": "RESEND_API_KEY_MANCANTE"}

    logger.info(f"[EMAIL SENDING] Tentativo invio da '{from_addr}' a {to_addrs} | Oggetto: '{subject}'")

    # Tentativo 1: SDK resend ufficiale
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
        logger.info(f"[EMAIL RESEND SDK] Risposta invio per {to_addrs}: {email_res}")
        if isinstance(email_res, dict) and ("statusCode" in email_res or "error" in email_res):
            logger.error(f"[EMAIL RESEND SDK RIFIUTATO] Errore API Resend: {email_res}")
        return email_res
    except ImportError:
        logger.info("[EMAIL INFO] Pacchetto resend non installato, uso fallback HTTP REST nativo.")
    except Exception as err:
        logger.error(f"[EMAIL SDK ERROR] resend.Emails.send ha sollevato eccezione: {type(err).__name__}: {err}", exc_info=True)

    # Tentativo 2: Fallback a richiesta HTTP REST nativa con logging corpo di risposta
    try:
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
            resp_body = resp.read().decode("utf-8", errors="ignore")
            body = json.loads(resp_body)
            logger.info(f"[EMAIL REST SUCCESS] Notifica Resend inviata via REST con successo (HTTP {resp.status}): {body}")
            return body
    except urllib.error.HTTPError as http_err:
        err_msg = http_err.read().decode("utf-8", errors="ignore")
        logger.error(
            f"[EMAIL HTTP ERROR {http_err.code}] Resend API ha rifiutato la richiesta: {err_msg} "
            f"| Mittente: '{from_addr}' | Destinatari: {to_addrs} | Oggetto: '{subject}'"
        )
        return {"error": "http_error", "code": http_err.code, "detail": err_msg}
    except Exception as rest_err:
        logger.error(f"[EMAIL NETWORK ERROR] Connessione a api.resend.com non riuscita: {type(rest_err).__name__}: {rest_err}", exc_info=True)
        return {"error": "network_error", "detail": str(rest_err)}

import html

def _esc(val: Any) -> str:
    """Sanifica stringhe utente per prevenire HTML injection nelle email."""
    return html.escape(str(val or "").strip())

def send_admin_new_order_alert(order: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Invia notifica istantanea all'amministratore (STORE_OWNER_EMAIL)."""
    try:
        order_id = _esc(order.get("order_number") or order.get("id", "N/D"))
        total = f"{float(order.get('total_amount', 0)):.2f}"
        cfg = get_notification_config()
        from_email = cfg["from_email"]
        store_owner = cfg["store_owner"]

        delivery_method = order.get("delivery_method", "shipping")
        is_pickup = delivery_method == "pickup"
        payment_method = order.get("payment_method", "paypal")
        is_cash = payment_method == "cash_on_pickup"

        items_summary = "".join([
            f"<li><strong>{_esc(it.get('product_title'))}</strong>: '{_esc(it.get('custom_text_line1'))}' "
            f"(Base: {_esc(it.get('base_color_name'))} | Testo: {_esc(it.get('text_color_name'))} | Font: {_esc(it.get('font_id'))})</li>"
            for it in items
        ])

        coupon_line = ""
        if order.get("coupon_code"):
            coupon_line = f"<p><strong>🎟️ Coupon Applicato:</strong> {_esc(order.get('coupon_code'))}</p>"

        if is_cash:
            payment_line = f"<p><strong>💵 Metodo Pagamento:</strong> <span style='color: #f59e0b; font-weight: bold;'>CONTANTI AL RITIRO</span> (Da incassare: {total} €)</p>"
        else:
            tx_id = _esc(order.get('paypal_capture_id') or order.get('paypal_order_id', 'N/D'))
            payment_line = f"<p><strong>💳 Metodo Pagamento:</strong> PayPal (ID Transazione: {tx_id})</p>"

        if is_pickup:
            delivery_line = "<p><strong>🤝 Modalità Consegna:</strong> Ritiro a mano di persona (0,00 €)</p>"
        else:
            delivery_line = f"""
            <p><strong>🚚 Spedizione Corriere:</strong> BRT / SDA</p>
            <p><strong>Indirizzo:</strong> {_esc(order.get('shipping_address', 'N/D'))}, {_esc(order.get('shipping_zip', ''))} {_esc(order.get('shipping_city', ''))} ({_esc(order.get('shipping_province', ''))})</p>
            """

        cust_notes = _esc(order.get('order_notes'))

        html_body = f"""
        <div style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 8px;">
            <h2 style="color: #38bdf8;">Nuovo Ordine Ricevuto! #{order_id}</h2>
            <p><strong>Codice Ordine:</strong> #{order_id}<br>Totale: <strong>{total} €</strong></p>
            <div style="background: #1e293b; padding: 14px; border-radius: 6px; margin: 16px 0;">
                <p><strong>Cliente:</strong> {_esc(order.get('customer_name', 'N/D'))}</p>
                <p><strong>Email:</strong> {_esc(order.get('customer_email', 'N/D'))}</p>
                <p><strong>Cellulare:</strong> {_esc(order.get('customer_phone', 'N/D'))}</p>
                {delivery_line}
                {payment_line}
                {coupon_line}
                {f"<p><strong>Note Ordine:</strong> {cust_notes}</p>" if cust_notes else ""}
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
            html_content=html_body
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
        order_id = _esc(order.get("order_number") or order.get("id", "N/D"))
        total = f"{float(order.get('total_amount', 0)):.2f}"
        cfg = get_notification_config()
        from_email = cfg["from_email"]

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
                delivery_desc = f"<p><strong>Consegna:</strong> Corriere Espresso BRT / SDA.<br>Destinazione: {_esc(order.get('shipping_address'))}, {_esc(order.get('shipping_city'))}</p>"
            subject = f"Conferma Ricezione Ordine #{order_id} - GadgetPoint.it"

        coupon_line = ""
        if order.get("coupon_code"):
            coupon_line = f"<p><strong>Codice Sconto Applicato:</strong> {_esc(order.get('coupon_code'))}</p>"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; background: #ffffff; color: #1e293b; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h2 style="color: #0284c7;">Conferma Ricezione Ordine #{order_id}</h2>
            <p>Gentile <strong>{_esc(order.get('customer_name', 'Cliente'))}</strong>,<br>
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
            html_content=html_body
        )
    except Exception as e:
        logger.warning(f"Invio email al cliente non riuscito: {str(e)}")
        return None
