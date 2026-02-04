"""LLM agent with tool-calling (Gemini). Uses Vertex AI via MCP."""
from contextlib import asynccontextmanager
import logging
from google import genai
from google.genai import types
from app.config import settings

try:
    from mcp import ClientSession as McpClientSession
    from mcp.client.sse import sse_client
except ImportError:
    McpClientSession = None
    sse_client = None

logger = logging.getLogger(__name__)


def _genai_client():
    """Create Gemini client via Vertex AI."""
    if settings.vertexai_project:
        return genai.Client(
            vertexai=True,
            project=settings.vertexai_project,
            location=settings.vertexai_location or "us-central1",
        )
    return None

@asynccontextmanager
async def _mcp_session():
    """Create and initialize an MCP client session (SSE transport)."""
    if not McpClientSession or not sse_client:
        raise RuntimeError(
            "MCP client not installed. Add 'mcp' and 'fastmcp' to requirements and reinstall."
        )
    server_url = settings.mcp_server_url
    streams_ctx = sse_client(server_url)
    streams = await streams_ctx.__aenter__()
    session_ctx = McpClientSession(*streams)
    session = await session_ctx.__aenter__()
    await session.initialize()
    try:
        yield session
    finally:
        await session_ctx.__aexit__(None, None, None)
        await streams_ctx.__aexit__(None, None, None)

SYSTEM_PATIENT_BASE = """You are an appointment booking assistant. The user is a patient.
- Use list_doctors() when the user asks what doctors are available, who can I book with, or similar. Then you can name them and suggest checking availability.
- Use list_my_appointments(patient_email) to see the patient's upcoming appointments. You MUST have the logged-in patient's email to call this; if you were not given the patient's email at the start, say: "I need you to be signed in to see your appointments. Please refresh the page and try again." Call list_my_appointments when the user asks to book so you can say if they already have an appointment with that doctor/date (e.g. "You already have an appointment with Dr. X tomorrow at 10:00. Want to book another slot?").
- Use get_doctor_availability(doctor_name, date_str) to check slots. For date_str use YYYY-MM-DD, or the word "tomorrow" or "today" if the user says that.
- Use book_appointment(doctor_name, slot_time, date_str, patient_name, patient_email, notes, condition) to book. When the user confirms a slot (e.g. "Book the 10:00 slot" or "Yes" or "yes"), call book_appointment immediately. Use empty string for notes and condition if not provided. Do NOT require condition or notes to book. slot_time: use 14:00 for 2pm, 15:00 for 3pm; "2pm", "14:00", "2 PM" all work. date_str: "today", "tomorrow", or YYYY-MM-DD. Do not call book_appointment again for the same doctor/date/slot.
- If book_appointment returns success: false, tell the user the exact "message" from the result (e.g. "No account found with that email. Please sign up or log in first."). Do not say "there was an error" without quoting the message; do not ask for condition or notes again.
- After a successful booking, confirm to the user. Always reply with a short, friendly message after calling tools."""

SYSTEM_PATIENT_WITH_USER = """{base}
- The current logged-in patient is: name="{patient_name}", email="{patient_email}". When the user asks for their appointments, upcoming appointments, or "my appointments", call list_my_appointments with this EXACT email: "{patient_email}". When calling book_appointment, ALWAYS use this patient_name and patient_email; do NOT ask the user for their name or email. Only ask for notes and/or condition (reason for visit) if you need them for the booking."""


def _system_patient(patient_name: str | None, patient_email: str | None) -> str:
    if patient_name and patient_email:
        return SYSTEM_PATIENT_WITH_USER.format(
            base=SYSTEM_PATIENT_BASE,
            patient_name=patient_name,
            patient_email=patient_email,
        )
    return SYSTEM_PATIENT_BASE

SYSTEM_DOCTOR_BASE = """You are a doctor's schedule and stats assistant.
- Use get_doctor_stats(doctor_name, query_type, condition_filter) to get: visits_yesterday, appointments_today, appointments_tomorrow, or patients_with_condition (use condition_filter e.g. fever).
- Use get_doctor_availability(doctor_name, date_str) to see the doctor's free slots on a date (e.g. "tomorrow" or YYYY-MM-DD).
- Use send_doctor_report(channel, report_text) to send the summary. Always use channel "slack" so the report is posted to the doctor's Slack channel (e.g. #dobble-reports). Do NOT ask the user which channel they prefer (slack or in_app); just call send_doctor_report with channel "slack" and confirm in your reply.
- Summarize the stats in a human-readable report, then send it via send_doctor_report(channel="slack", report_text=...).
- Reply with the report summary and confirm that the report was sent to Slack."""

SYSTEM_DOCTOR_WITH_USER = """{base}
- The current logged-in doctor is: name="{doctor_name}", email="{doctor_email}". When calling get_doctor_stats, get_doctor_availability, or send_doctor_report, ALWAYS use this doctor_name; do NOT ask the user for their name or email."""

def _system_doctor(doctor_name: str | None, doctor_email: str | None) -> str:
    if doctor_name:
        return SYSTEM_DOCTOR_WITH_USER.format(
            base=SYSTEM_DOCTOR_BASE,
            doctor_name=doctor_name,
            doctor_email=doctor_email or "",
        )
    return SYSTEM_DOCTOR_BASE


def _messages_to_contents(messages: list[dict]) -> list[types.Content]:
    """Convert [{"role": "user"|"assistant", "content": "..."}] to Gemini Content list."""
    out = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        out.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    return out


def _extract_text(response) -> str:
    """Get reply text from response; fallback to candidates/parts when response.text is empty (e.g. after tool call)."""
    if getattr(response, "text", None) and response.text:
        return response.text.strip()
    try:
        for c in getattr(response, "candidates", []) or []:
            content = getattr(c, "content", None)
            if not content:
                continue
            for p in getattr(content, "parts", []) or []:
                text = getattr(p, "text", None)
                if text and text.strip():
                    return text.strip()
    except Exception:
        pass
    return ""


async def chat(
    messages: list[dict],
    role_type: str = "patient",
    patient_name: str | None = None,
    patient_email: str | None = None,
    doctor_name: str | None = None,
    doctor_email: str | None = None,
) -> str:
    """Run agent: messages include prior conversation; role_type is 'patient' or 'doctor'.
    When role_type is patient, pass patient_name and patient_email. When role_type is doctor, pass doctor_name and doctor_email."""
    client = _genai_client()
    if not client:
        return "Gemini not configured. Set VERTEXAI_PROJECT (and optionally VERTEXAI_LOCATION) in backend/.env. Authenticate with: gcloud auth application-default login"
    system = (
        _system_patient(patient_name, patient_email) if role_type == "patient"
        else _system_doctor(doctor_name, doctor_email)
    )
    contents = _messages_to_contents(messages)
    try:
        async with _mcp_session() as mcp_session:
            config = types.GenerateContentConfig(
                system_instruction=system,
                tools=[mcp_session],
            )
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=config,
            )
    except Exception as exc:
        logger.exception("MCP session failed: %s", exc)
        return "MCP tool server is unavailable. Please ensure /mcp is running and reachable."
    text = _extract_text(response)
    if text:
        return text
    return "Agent did not return a text reply."
