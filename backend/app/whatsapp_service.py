import os
import httpx


WHATSAPP_ACCESS_TOKEN = os.getenv(
    "WHATSAPP_ACCESS_TOKEN",
    "",
).strip()

WHATSAPP_PHONE_NUMBER_ID = os.getenv(
    "WHATSAPP_PHONE_NUMBER_ID",
    "",
).strip()

WHATSAPP_API_VERSION = os.getenv(
    "WHATSAPP_API_VERSION",
    "v23.0",
).strip()


def send_whatsapp_message(
    recipient: str,
    message: str,
):
    if not WHATSAPP_ACCESS_TOKEN:
        raise RuntimeError(
            "WHATSAPP_ACCESS_TOKEN is not configured"
        )

    if not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError(
            "WHATSAPP_PHONE_NUMBER_ID is not configured"
        )

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    # WhatsApp messages should stay reasonably sized.
    # We'll improve long-answer handling later.
    message = (message or "").strip()

    if not message:
        return

    response = httpx.post(
        url,
        headers={
            "Authorization":
                f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message[:4000],
            },
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()
