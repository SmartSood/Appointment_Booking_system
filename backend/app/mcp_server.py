"""MCP server exposing tools for LLM agent (FastMCP). Uses Prisma Python for DB."""
import json
import logging
from fastmcp import FastMCP
from app import tools_impl

logger = logging.getLogger(__name__)
mcp = FastMCP(
    "Dobble MCP",
    dependencies=["fastapi"],
)


@mcp.tool()
async def list_doctors() -> str:
    """List all doctors in the system (name, email, specialization). Use this when the user asks who is available or what doctors are available."""
    doctors = await tools_impl.list_doctors_impl()
    return json.dumps({"doctors": doctors})


@mcp.tool()
async def get_doctor_availability(doctor_name: str, date_str: str) -> str:
    """Get available time slots for a doctor on a given date. date_str format: YYYY-MM-DD."""
    slots = await tools_impl.get_doctor_availability_impl(doctor_name, date_str)
    return json.dumps({"available_slots": slots, "doctor": doctor_name, "date": date_str})


@mcp.tool()
async def book_appointment(
    doctor_name: str,
    slot_time: str,
    date_str: str,
    patient_name: str,
    patient_email: str,
    notes: str = "",
    condition: str = "",
) -> str:
    """Book an appointment: creates in DB, Google Calendar, and sends email confirmation.
    slot_time: HH:MM (e.g. 14:00) or 2pm, 2 PM. date_str: today, tomorrow, or YYYY-MM-DD.
    patient_name and patient_email must be the logged-in user's (from system prompt)."""
    logger.info(
        "MCP book_appointment: doctor_name=%r slot_time=%r date_str=%r patient_email=%r",
        doctor_name, slot_time, date_str, patient_email,
    )
    try:
        result = await tools_impl.book_appointment_impl(
            doctor_name,
            slot_time,
            date_str,
            patient_name,
            patient_email,
            notes or None,
            condition or None,
        )
        out = json.dumps(result)
        if not result.get("success"):
            logger.warning("book_appointment failed: %s", result.get("message", "unknown"))
        return out
    except Exception as e:
        logger.exception("book_appointment exception: %s", e)
        return json.dumps({"success": False, "message": str(e)})


@mcp.tool()
async def list_my_appointments(patient_email: str) -> str:
    """List the patient's upcoming appointments. patient_email must be the logged-in user's email."""
    logger.info("list_my_appointments called with patient_email=%r", patient_email)
    appts = await tools_impl.list_my_appointments_impl(patient_email)
    logger.info("list_my_appointments returned %d appointments for %r", len(appts), patient_email)
    return json.dumps({"appointments": appts})


@mcp.tool()
async def send_email_confirmation(to: str, subject: str, body: str) -> str:
    """Send an email to the patient (e.g. booking confirmation)."""
    result = await tools_impl.send_email_confirmation_impl(to, subject, body)
    return json.dumps(result)


@mcp.tool()
async def get_doctor_stats(
    doctor_name: str,
    query_type: str,
    condition_filter: str = "",
) -> str:
    """Get stats for a doctor. query_type: visits_yesterday, appointments_today,
    appointments_tomorrow, or patients_with_condition. For patients_with_condition,
    set condition_filter (e.g. fever)."""
    result = await tools_impl.get_doctor_stats_impl(
        doctor_name, query_type, condition_filter or None
    )
    return json.dumps(result)


@mcp.tool()
async def send_doctor_report(channel: str, report_text: str) -> str:
    """Send a summary report to the doctor. channel: 'slack' or 'in_app'."""
    result = await tools_impl.send_doctor_report_impl(channel, report_text)
    return json.dumps(result)
