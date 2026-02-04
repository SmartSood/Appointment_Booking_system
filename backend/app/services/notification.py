"""Doctor report notification via Slack or in-app. Stub when not configured."""
import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_doctor_report(channel: str, report_text: str) -> bool:
    """Send report to doctor via Slack or in-app. channel: 'slack' | 'in_app'."""
    if channel == "slack":
        token = (settings.slack_bot_token or "").strip()
        channel_id = (settings.slack_channel_id or "").strip()
        # Log token prefix so you can confirm .env is being used (e.g. xoxb- or xoxe.xoxb-)
        if token:
            logger.info("Slack token in use starts with: %s...", token[:18] if len(token) > 18 else token[:8])
        if not token or not channel_id:
            logger.info("[NOTIFICATION STUB] Slack not configured (missing token or channel); report: %s...", report_text[:100])
            return True

        def _post():
            from slack_sdk import WebClient

            client = WebClient(token=token)
            client.chat_postMessage(channel=channel_id, text=report_text)
            return True

        try:
            await asyncio.to_thread(_post)
            logger.info("Slack report sent to channel %s", channel_id)
            return True
        except Exception as e:
            logger.exception("Slack send_doctor_report failed: %s", e)
            # If missing scope, log clear fix steps (must be done in Slack dashboard, not in code)
            err_str = str(e).lower()
            if "missing_scope" in err_str or "chat:write" in err_str:
                logger.error(
                    "Slack fix: 1) Go to https://api.slack.com/apps → your app → OAuth & Permissions. "
                    "2) Under Bot Token Scopes click 'Add an OAuth Scope' and add: chat:write. "
                    "3) Reinstall app to workspace. 4) Copy the new 'Bot User OAuth Token' (xoxb-...) into backend/.env as SLACK_BOT_TOKEN. 5) Restart backend."
                )
            return False

    # in_app or any other channel: stub (log only)
    logger.info("[NOTIFICATION STUB] channel=%s\n%s...", channel, report_text[:200])
    return True
