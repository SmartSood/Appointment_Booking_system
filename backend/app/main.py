"""FastAPI app: auth (register/login), agent, optional MCP."""
import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.db import connect_prisma, disconnect_prisma
from app.agent import chat
from app import auth as auth_module

logger = logging.getLogger("uvicorn.error")

# Optional MCP server (install fastmcp separately to enable)
try:
    from app.mcp_server import mcp
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    mcp = None

# In-memory session store for multi-turn 
sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    role: str = "patient"  # patient | doctor
    patient_name: str | None = None  # logged-in patient; agent uses this for booking without asking
    patient_email: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_prisma()
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning(
            "Prisma connect failed (server will start; /api/chat may fail): %s", e
        )
    yield
    await disconnect_prisma()


app = FastAPI(title="Dobble AI", description="Agentic AI + MCP", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP server only if fastmcp is installed
if _MCP_AVAILABLE and mcp is not None:
    try:
        _mcp_app = getattr(mcp, "get_asgi_app", None) or getattr(mcp, "sse_app", None)
        if _mcp_app and callable(_mcp_app):
            app.mount("/mcp", _mcp_app())
    except Exception:
        pass


@app.get("/health")
async def health():
    return {"status": "ok"}


# ----- Auth (register / login) -----
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str  # PATIENT | DOCTOR
    specialization: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str  # PATIENT | DOCTOR


@app.post("/api/auth/register")
async def api_register(req: RegisterRequest):
    """Register as Doctor or Patient. Creates record in doctors or patients table."""
    if req.role == "DOCTOR":
        out = await auth_module.register_doctor(req.name, req.email, req.password, req.specialization)
    elif req.role == "PATIENT":
        out = await auth_module.register_patient(req.name, req.email, req.password)
    else:
        raise HTTPException(status_code=400, detail="role must be PATIENT or DOCTOR")
    if "error" in out:
        raise HTTPException(status_code=400, detail=out["error"])
    token = auth_module.create_access_token(out["id"], out["email"], out["name"], out["role"])
    return {"user": out, "access_token": token}


@app.post("/api/auth/login")
async def api_login(req: LoginRequest):
    """Login as Doctor or Patient. Returns JWT."""
    if req.role == "DOCTOR":
        user = await auth_module.login_doctor(req.email, req.password)
    elif req.role == "PATIENT":
        user = await auth_module.login_patient(req.email, req.password)
    else:
        raise HTTPException(status_code=400, detail="role must be PATIENT or DOCTOR")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email, password, or role")
    token = auth_module.create_access_token(user["id"], user["email"], user["name"], user["role"])
    return {"user": user, "access_token": token}


@app.get("/api/me")
async def api_me(user: dict = Depends(auth_module.get_current_user)):
    """Return current user from JWT (for Next.js session)."""
    return user


@app.get("/api/profile")
async def api_get_profile(user: dict = Depends(auth_module.get_current_user)):
    """Return current user profile including specialization for doctors."""
    from app.db import get_prisma
    prisma = get_prisma()
    uid = int(user["id"])
    if user["role"] == "DOCTOR":
        doc = await prisma.doctor.find_unique(where={"id": uid})
        if not doc:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return {
            "id": str(doc.id),
            "name": doc.name,
            "email": doc.email,
            "role": "DOCTOR",
            "specialization": getattr(doc, "specialization", None),
        }
    patient = await prisma.patient.find_unique(where={"id": uid})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {
        "id": str(patient.id),
        "name": patient.name,
        "email": patient.email,
        "role": "PATIENT",
        "specialization": None,
    }


@app.get("/api/doctors")
async def api_list_doctors(user: dict = Depends(auth_module.get_current_user)):
    """List doctors for patient dropdown (id, name)."""
    from app.db import get_prisma
    prisma = get_prisma()
    doctors = await prisma.doctor.find_many(
        take=100,
        order={"name": "asc"},
    )
    return [{"id": str(d.id), "name": d.name} for d in doctors]


# ----- Appointments (dashboard: list / create) -----
@app.get("/api/appointments")
async def api_list_appointments(user: dict = Depends(auth_module.get_current_user)):
    """List appointments for current user (patient or doctor)."""
    from app.db import get_prisma
    prisma = get_prisma()
    uid = int(user["id"])
    if user["role"] == "PATIENT":
        bookings = await prisma.booking.find_many(
            where={"patientId": uid},
            include={"doctor": True, "patient": True},
            order={"scheduledAt": "desc"},
            take=50,
        )
    else:
        bookings = await prisma.booking.find_many(
            where={"doctorId": uid},
            include={"doctor": True, "patient": True},
            order={"scheduledAt": "desc"},
            take=50,
        )
    return [
        {
            "id": str(b.id),
            "doctorId": str(b.doctorId),
            "patientId": str(b.patientId),
            "dateTime": b.scheduledAt.isoformat(),
            "status": b.status,
            "notes": b.notes,
            "doctor": {"id": str(b.doctor.id), "name": b.doctor.name, "email": b.doctor.email},
            "patient": {"id": str(b.patient.id), "name": b.patient.name, "email": b.patient.email},
        }
        for b in bookings
    ]


class CreateAppointmentRequest(BaseModel):
    doctorId: str
    dateTime: str  # ISO datetime
    notes: str | None = None


@app.post("/api/appointments")
async def api_create_appointment(req: CreateAppointmentRequest, user: dict = Depends(auth_module.get_current_user)):
    """Create appointment (patient books with doctor)."""
    from datetime import datetime
    from app.db import get_prisma
    if user["role"] != "PATIENT":
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    prisma = get_prisma()
    try:
        scheduled_at = datetime.fromisoformat(req.dateTime.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dateTime")
    doctor_id = int(req.doctorId)
    patient_id = int(user["id"])
    doctor = await prisma.doctor.find_unique(where={"id": doctor_id})
    if not doctor:
        raise HTTPException(status_code=400, detail="Doctor not found")
    booking = await prisma.booking.create(
        data={
            "doctorId": doctor_id,
            "patientId": patient_id,
            "scheduledAt": scheduled_at,
            "status": "SCHEDULED",
            "notes": req.notes,
        }
    )
    return {"id": str(booking.id), "doctorId": str(booking.doctorId), "patientId": str(booking.patientId), "dateTime": booking.scheduledAt.isoformat(), "status": booking.status}


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    specialization: str | None = None


@app.patch("/api/profile")
async def api_update_profile(req: UpdateProfileRequest, user: dict = Depends(auth_module.get_current_user)):
    """Update current user name or (doctor) specialization."""
    from app.db import get_prisma
    prisma = get_prisma()
    uid = int(user["id"])
    if user["role"] == "DOCTOR":
        data = {}
        if req.name is not None:
            data["name"] = req.name
        if req.specialization is not None:
            data["specialization"] = req.specialization
        if data:
            await prisma.doctor.update(where={"id": uid}, data=data)
    else:
        if req.name is not None:
            await prisma.patient.update(where={"id": uid}, data={"name": req.name})
    return {"ok": True}


class UpdateAppointmentRequest(BaseModel):
    status: str  # SCHEDULED | COMPLETED | CANCELLED


@app.patch("/api/appointments/{booking_id}")
async def api_update_appointment(
    booking_id: int,
    req: UpdateAppointmentRequest,
    user: dict = Depends(auth_module.get_current_user),
):
    """Update booking status (current user must be patient or doctor for this booking)."""
    from app.db import get_prisma
    prisma = get_prisma()
    uid = int(user["id"])
    booking = await prisma.booking.find_unique(where={"id": booking_id}, include={"doctor": True, "patient": True})
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if booking.patientId != uid and booking.doctorId != uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    await prisma.booking.update(where={"id": booking_id}, data={"status": req.status})
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest):
    """Patient or doctor natural language prompt; returns agent reply. Multi-turn via session_id."""
    sid = req.session_id or "default"
    if req.role == "patient":
        logger.info(
            "api_chat patient: prompt=%r patient_email=%r patient_name=%r",
            (req.prompt or "")[:80],
            getattr(req, "patient_email", None),
            getattr(req, "patient_name", None),
        )
    if sid not in sessions:
        sessions[sid] = []
    sessions[sid].append({"role": "user", "content": req.prompt})
    try:
        reply = await chat(
            sessions[sid],
            role_type=req.role,
            patient_name=req.patient_name,
            patient_email=req.patient_email,
        )
    except Exception as e:
        logger.exception("Chat error")
        return JSONResponse(
            status_code=200,
            content={"reply": f"Sorry, something went wrong: {str(e)}", "session_id": sid},
        )
    sessions[sid].append({"role": "assistant", "content": reply})
    return ChatResponse(reply=reply, session_id=sid)


class DoctorReportRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    doctor_name: str | None = None  # logged-in doctor; agent uses this without asking
    doctor_email: str | None = None


@app.post("/api/doctor-report")
async def api_doctor_report(req: DoctorReportRequest):
    """Doctor asks for summary (e.g. how many patients yesterday); agent uses tools and sends notification."""
    sid = req.session_id or "doctor_default"
    if sid not in sessions:
        sessions[sid] = []
    sessions[sid].append({"role": "user", "content": req.prompt})
    try:
        reply = await chat(
            sessions[sid],
            role_type="doctor",
            doctor_name=req.doctor_name,
            doctor_email=req.doctor_email,
        )
    except Exception as e:
        logger.exception("Doctor report error")
        return JSONResponse(
            status_code=200,
            content={"reply": f"Sorry, something went wrong: {str(e)}", "session_id": sid},
        )
    sessions[sid].append({"role": "assistant", "content": reply})
    return {"reply": reply, "session_id": sid}
