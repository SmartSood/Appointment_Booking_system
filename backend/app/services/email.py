"""Email confirmation via SendGrid. Stub when not configured."""
import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_confirmation_email(to: str, subject: str, body: str) -> bool:
    """Send email to patient (e.g. booking confirmation). Uses SendGrid when API key is set."""
    api_key = (settings.sendgrid_api_key or "").strip()
    if not api_key:
        logger.info("[EMAIL STUB] To: %s, Subject: %s", to, subject)
        return True

    from_email = (settings.sendgrid_from_email or "noreply@example.com").strip()

    def _send():
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            plain_text_content=body,
        )
        client = SendGridAPIClient(api_key)
        client.send(message)
        return True

    try:
        await asyncio.to_thread(_send)
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.exception("SendGrid send_confirmation_email failed: %s", e)
        return False
