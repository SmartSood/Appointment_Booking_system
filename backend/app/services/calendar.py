"""Google Calendar integration. Creates events and returns busy slots when credentials are set."""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Cached only for service account (OAuth we build each time to refresh token)
_calendar_service = None
_using_oauth = False


_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _get_calendar_service():
    """Build Google Calendar API service. Uses (1) service account JSON or (2) OAuth refresh token. Returns None if not configured."""
    global _calendar_service, _using_oauth
    creds = None
    # (1) Service account (requires JSON key file)
    path = (settings.google_credentials_file or "").strip()
    if path and Path(path).is_file():
        try:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(path, scopes=_CALENDAR_SCOPES)
            _using_oauth = False
        except Exception as e:
            logger.warning("Failed to load service account: %s", e)
    # (2) OAuth 2.0 (no key file – use when org blocks service account keys)
    if creds is None:
        cid = (settings.google_oauth_client_id or "").strip()
        csec = (settings.google_oauth_client_secret or "").strip()
        ref = (settings.google_oauth_refresh_token or "").strip()
        if cid and csec and ref:
            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials(
                    token=None,
                    refresh_token=ref,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=cid,
                    client_secret=csec,
                    scopes=_CALENDAR_SCOPES,
                )
                req = Request()
                creds.refresh(req)
                _using_oauth = True
            except Exception as e:
                logger.warning("Failed to build OAuth credentials (check GOOGLE_OAUTH_* and refresh token): %s", e)
                creds = None
        else:
            if not path:
                logger.debug("Google Calendar not configured: set GOOGLE_CREDENTIALS_FILE or GOOGLE_OAUTH_* in backend/.env")
    if creds is None:
        return None
    # For OAuth, refresh if expired and don't cache service (access token expires ~1h)
    if _using_oauth:
        try:
            from google.auth.transport.requests import Request
            if getattr(creds, "expired", True) or not getattr(creds, "valid", True):
                creds.refresh(Request())
            from googleapiclient.discovery import build
            return build("calendar", "v3", credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.warning("Calendar OAuth refresh or build failed: %s", e)
            return None
    if _calendar_service is not None:
        return _calendar_service
    try:
        from googleapiclient.discovery import build
        _calendar_service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return _calendar_service
    except Exception as e:
        logger.warning("Failed to build Calendar service: %s", e)
        return None


async def create_calendar_event(
    doctor_name: str,
    patient_name: str,
    patient_email: str,
    start: datetime,
    end: datetime | None = None,
    summary: str | None = None,
) -> str | None:
    """Create event in Google Calendar. Returns event_id or stub id if not configured."""
    service = _get_calendar_service()
    if not service:
        logger.info(
            "Google Calendar not configured or auth failed: set GOOGLE_CREDENTIALS_FILE or "
            "GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REFRESH_TOKEN in backend/.env"
        )
        return f"stub_{doctor_name}_{start.isoformat()}"

    end_dt = end or start.replace(hour=start.hour + 1, minute=0, second=0, microsecond=0)
    summary_text = summary or f"Appointment: {patient_name} with {doctor_name}"
    # RFC3339 for Google Calendar: use Z for UTC if naive
    start_str = start.isoformat() + "Z" if start.tzinfo is None else start.isoformat()
    end_str = end_dt.isoformat() + "Z" if end_dt.tzinfo is None else end_dt.isoformat()
    body = {
        "summary": summary_text,
        "description": f"Patient: {patient_name} ({patient_email})",
        "start": {"dateTime": start_str, "timeZone": "UTC"},
        "end": {"dateTime": end_str, "timeZone": "UTC"},
        "attendees": [{"email": patient_email, "displayName": patient_name}],
    }
    calendar_id = (settings.google_calendar_id or "primary").strip()

    def _insert():
        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        return event.get("id")

    try:
        event_id = await asyncio.to_thread(_insert)
        return event_id
    except Exception as e:
        logger.exception("Calendar create_calendar_event failed: %s", e)
        return None


async def get_busy_slots(doctor_name: str, date: datetime) -> list[tuple[datetime, datetime]]:
    """Return busy time ranges for the configured calendar on the given date (UTC)."""
    service = _get_calendar_service()
    if not service:
        return []

    calendar_id = (settings.google_calendar_id or "primary").strip()
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    tz_suffix = "Z" if start_of_day.tzinfo is None else ""
    body = {
        "timeMin": start_of_day.isoformat() + tz_suffix,
        "timeMax": end_of_day.isoformat() + tz_suffix,
        "items": [{"id": calendar_id}],
    }

    def _query():
        resp = service.freebusy().query(body=body).execute()
        cal = resp.get("calendars", {}).get(calendar_id, {})
        busy = cal.get("busy", [])
        out = []
        for b in busy:
            start_s, end_s = b.get("start"), b.get("end")
            if start_s and end_s:
                try:
                    start_dt = datetime.fromisoformat(start_s.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_s.replace("Z", "+00:00"))
                    out.append((start_dt, end_dt))
                except (ValueError, TypeError):
                    pass
        return out

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        logger.exception("Calendar get_busy_slots failed: %s", e)
        return []
