"""Shared tool implementations used by MCP server and LLM agent. Uses Prisma Python."""
import logging
import re
from datetime import datetime, timedelta

from app.db import get_prisma
from app.services import calendar, email, notification

logger = logging.getLogger(__name__)


def _parse_slot_time(slot_time: str) -> datetime.time | None:
    """Parse slot_time to time. Accepts HH:MM, 2pm, 2 pm, 2opm, 14:00, 2:00 PM, etc."""
    s = (slot_time or "").strip()
    if not s:
        return None
    # Try standard formats first
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            try:
                return datetime.strptime(s.replace(" ", ""), fmt.replace(" ", "")).time()
            except ValueError:
                continue
    # Flexible: "2pm", "2opm", "10am", "12pm"
    m = re.match(r"^(\d{1,2})\s*[o:]?\s*(am|pm)$", s.lower())
    if m:
        hour = int(m.group(1))
        if m.group(2) == "pm" and hour != 12:
            hour += 12
        elif m.group(2) == "am" and hour == 12:
            hour = 0
        if 0 <= hour <= 23:
            return datetime.strptime(f"{hour:02d}:00", "%H:%M").time()
    return None


async def list_doctors_impl() -> list[dict]:
    """Return list of all doctors from the database (name, email, specialization)."""
    try:
        prisma = get_prisma()
        doctors = await prisma.doctor.find_many()
        result = [
            {"name": d.name, "email": d.email, "specialization": d.specialization or ""}
            for d in doctors
        ]
        result.sort(key=lambda x: (x["name"] or "").lower())
        return result
    except RuntimeError as e:
        if "not connected" in str(e).lower():
            logger.warning("Prisma not connected: %s", e)
            return []
        raise
    except Exception as e:
        logger.exception("list_doctors_impl failed: %s", e)
        return []


async def get_doctor_availability_impl(doctor_name: str, date_str: str) -> list[str]:
    """Return list of available time slots for doctor on date (e.g. ['09:00', '10:00', '14:00'])."""
    try:
        # Normalize date: accept "tomorrow", relative dates, or ISO
        date_str = (date_str or "").strip()
        if date_str.lower() == "tomorrow":
            day = (datetime.utcnow() + timedelta(days=1)).date()
        elif date_str.lower() == "today":
            day = datetime.utcnow().date()
        else:
            day = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return []
    day_of_week = day.weekday()  # 0=Monday
    try:
        prisma = get_prisma()
        doctor = await prisma.doctor.find_first(
            where={"name": {"contains": doctor_name, "mode": "insensitive"}}
        )
        if not doctor:
            return []
        slots = await prisma.availabilityslot.find_many(
            where={
                "doctorId": doctor.id,
                "dayOfWeek": day_of_week,
                "isAvailable": True,
            }
        )
        if not slots:
            out = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        else:
            out = []
            for s in slots:
                start = datetime.strptime(s.startTime, "%H:%M").time()
                end = datetime.strptime(s.endTime, "%H:%M").time()
                current = datetime.combine(day, start)
                end_dt = datetime.combine(day, end)
                while current < end_dt:
                    out.append(current.strftime("%H:%M"))
                    current += timedelta(hours=1)
        start_of_day = datetime.combine(day, datetime.min.time())
        end_of_day = datetime.combine(day, datetime.max.time().replace(microsecond=0))
        booked = await prisma.booking.find_many(
            where={
                "doctorId": doctor.id,
                "scheduledAt": {"gte": start_of_day, "lte": end_of_day},
                "status": "SCHEDULED",
            }
        )
        booked_times = {dt.scheduledAt.strftime("%H:%M") for dt in booked}
        busy = await calendar.get_busy_slots(doctor.name, datetime.combine(day, datetime.min.time()))
        for start_b, end_b in busy:
            for h in range(start_b.hour, end_b.hour):
                booked_times.add(f"{h:02d}:00")
        return [t for t in sorted(set(out)) if t not in booked_times]
    except Exception as e:
        logger.exception("get_doctor_availability_impl failed: %s", e)
        return []


async def list_my_appointments_impl(patient_email: str) -> list[dict]:
    """Return the patient's upcoming SCHEDULED appointments (doctor name, date, time, notes)."""
    try:
        prisma = get_prisma()
        patient_email = (patient_email or "").strip()
        if not patient_email:
            logger.warning("list_my_appointments_impl called with empty patient_email")
            return []
        patient = await prisma.patient.find_unique(where={"email": patient_email})
        if not patient:
            logger.info("list_my_appointments_impl: no patient found for email=%r", patient_email)
            return []
        now = datetime.utcnow()
        # Include appointments from the last hour onward (avoids excluding same-day slots due to timezone/server time)
        cutoff = now - timedelta(hours=1)
        bookings = await prisma.booking.find_many(
            where={
                "patientId": patient.id,
                "status": "SCHEDULED",
                "scheduledAt": {"gte": cutoff},
            },
            include={"doctor": True},
            order={"scheduledAt": "asc"},
            take=20,
        )
        return [
            {
                "doctor": b.doctor.name,
                "date": b.scheduledAt.strftime("%Y-%m-%d"),
                "time": b.scheduledAt.strftime("%H:%M"),
                "notes": b.notes or "",
                "condition": getattr(b, "condition", None) or "",
            }
            for b in bookings
        ]
    except Exception as e:
        logger.exception("list_my_appointments_impl failed: %s", e)
        return []


async def book_appointment_impl(
    doctor_name: str,
    slot_time: str,
    date_str: str,
    patient_name: str,
    patient_email: str,
    notes: str | None = None,
    condition: str | None = None,
) -> dict:
    """Book appointment: DB + Calendar + send email. Returns {success, message, appointment_id}."""
    logger.info(
        "book_appointment_impl called: doctor_name=%r slot_time=%r date_str=%r patient_email=%r",
        doctor_name, slot_time, date_str, patient_email,
    )
    if not (patient_name and patient_email):
        return {"success": False, "message": "Patient name and email are required. Please sign in and try again."}
    try:
        # Normalize date_str: "tomorrow", "today", or ISO
        date_str = (date_str or "").strip()
        if date_str.lower() == "tomorrow":
            day = (datetime.utcnow() + timedelta(days=1)).date()
        elif date_str.lower() == "today":
            day = datetime.utcnow().date()
        else:
            day = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        dt = _parse_slot_time(slot_time)
        if dt is None:
            return {"success": False, "message": "Invalid time format. Use HH:MM (e.g. 14:00), 2pm, or 2:00 PM."}
        scheduled_at = datetime.combine(day, dt)
    except (ValueError, TypeError):
        return {"success": False, "message": "Invalid date or time format."}
    prisma = get_prisma()
    doctor = await prisma.doctor.find_first(
        where={"name": {"contains": doctor_name, "mode": "insensitive"}}
    )
    if not doctor:
        return {"success": False, "message": f"Doctor '{doctor_name}' not found."}
    available = await get_doctor_availability_impl(doctor_name, date_str)
    slot_hhmm = dt.strftime("%H:%M")
    if slot_hhmm not in available:
        return {"success": False, "message": f"Slot {slot_hhmm} is not available. Available: {available}."}
    end_at = scheduled_at + timedelta(hours=1)
    # Find patient by email (must already exist / be logged in; we do not create patients from agent)
    patient = await prisma.patient.find_unique(where={"email": patient_email})
    if not patient:
        return {"success": False, "message": "No account found with that email. Please sign up or log in first."}
    # Avoid duplicate: already have SCHEDULED booking for same doctor/slot
    existing = await prisma.booking.find_first(
        where={
            "doctorId": doctor.id,
            "patientId": patient.id,
            "scheduledAt": scheduled_at,
            "status": "SCHEDULED",
        }
    )
    if existing:
        return {"success": False, "message": "You already have an appointment with this doctor at this date and time."}
    try:
        calendar_event_id = await calendar.create_calendar_event(
            doctor.name, patient_name, patient_email, scheduled_at, end_at,
            summary=f"Appointment: {patient_name} with {doctor.name}",
        )
        appointment = await prisma.booking.create(
            data={
                "doctorId": doctor.id,
                "patientId": patient.id,
                "scheduledAt": scheduled_at,
                "status": "SCHEDULED",
                "notes": notes,
                "condition": condition,
                "calendarEventId": calendar_event_id,
            }
        )
        body = f"Your appointment with {doctor.name} is confirmed for {scheduled_at.isoformat()}."
        await email.send_confirmation_email(
            patient_email,
            f"Appointment confirmed with {doctor.name}",
            body,
        )
        return {
            "success": True,
            "message": f"Booked {scheduled_at.isoformat()} with {doctor.name}.",
            "appointment_id": appointment.id,
        }
    except Exception as e:
        logger.exception("book_appointment_impl failed: %s", e)
        return {"success": False, "message": f"Booking failed: {str(e)}. Please try again."}


async def send_email_confirmation_impl(to: str, subject: str, body: str) -> dict:
    """Send email to patient (confirmation)."""
    ok = await email.send_confirmation_email(to, subject, body)
    return {"success": ok, "message": "Email sent." if ok else "Email failed."}


async def get_doctor_stats_impl(
    doctor_name: str,
    query_type: str,
    condition_filter: str | None = None,
) -> dict:
    """Get stats for doctor: visits_yesterday, appointments_today, appointments_tomorrow, patients_with_condition."""
    prisma = get_prisma()
    doctor = await prisma.doctor.find_first(
        where={"name": {"contains": doctor_name, "mode": "insensitive"}}
    )
    if not doctor:
        return {"error": f"Doctor '{doctor_name}' not found."}
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    start_yesterday = datetime.combine(yesterday, datetime.min.time())
    end_yesterday = datetime.combine(yesterday, datetime.max.time().replace(microsecond=0))
    start_today = datetime.combine(today, datetime.min.time())
    end_today = datetime.combine(today, datetime.max.time().replace(microsecond=0))
    start_tomorrow = datetime.combine(tomorrow, datetime.min.time())
    end_tomorrow = datetime.combine(tomorrow, datetime.max.time().replace(microsecond=0))

    if query_type == "visits_yesterday":
        count = await prisma.booking.count(
            where={
                "doctorId": doctor.id,
                "scheduledAt": {"gte": start_yesterday, "lte": end_yesterday},
                "status": "COMPLETED",
            }
        )
        return {"visits_yesterday": count, "doctor": doctor.name}
    if query_type == "appointments_today":
        count = await prisma.booking.count(
            where={
                "doctorId": doctor.id,
                "scheduledAt": {"gte": start_today, "lte": end_today},
                "status": "SCHEDULED",
            }
        )
        return {"appointments_today": count, "doctor": doctor.name}
    if query_type == "appointments_tomorrow":
        count = await prisma.booking.count(
            where={
                "doctorId": doctor.id,
                "scheduledAt": {"gte": start_tomorrow, "lte": end_tomorrow},
                "status": "SCHEDULED",
            }
        )
        return {"appointments_tomorrow": count, "doctor": doctor.name}
    if query_type == "patients_with_condition" and condition_filter:
        count = await prisma.booking.count(
            where={
                "doctorId": doctor.id,
                "condition": {"contains": condition_filter, "mode": "insensitive"},
            }
        )
        return {"patients_with_condition": count, "condition": condition_filter, "doctor": doctor.name}
    return {"error": "Unknown query_type or missing condition_filter."}


async def send_doctor_report_impl(channel: str, report_text: str) -> dict:
    """Send report to doctor via Slack or in_app."""
    ok = await notification.send_doctor_report(channel, report_text)
    return {"success": ok, "channel": channel, "message": "Report sent." if ok else "Failed."}
