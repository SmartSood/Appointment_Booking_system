"""Auth: register (Doctor/Patient), login (JWT)."""
from datetime import datetime, timedelta
from typing import Literal

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.db import get_prisma

# Use bcrypt directly to avoid passlib/bcrypt compatibility issues (e.g. Python 3.14)
try:
    from bcrypt import hashpw, gensalt, checkpw

    def hash_password(password: str) -> str:
        return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

    def verify_password(plain: str, hashed: str) -> bool:
        if not hashed:
            return False
        try:
            return checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
except ImportError:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

security = HTTPBearer(auto_error=False)


def create_access_token(sub: str, email: str, name: str, role: Literal["DOCTOR", "PATIENT"]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": sub, "email": email, "name": name, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


async def register_doctor(name: str, email: str, password: str, specialization: str | None = None) -> dict:
    prisma = get_prisma()
    existing = await prisma.doctor.find_unique(where={"email": email})
    if existing:
        return {"error": "An account with this email already exists."}
    doc = await prisma.doctor.create(
        data={
            "name": name,
            "email": email,
            "passwordHash": hash_password(password),
            "specialization": specialization,
        }
    )
    return {"id": str(doc.id), "email": doc.email, "name": doc.name, "role": "DOCTOR"}


async def register_patient(name: str, email: str, password: str) -> dict:
    prisma = get_prisma()
    existing = await prisma.patient.find_unique(where={"email": email})
    if existing:
        return {"error": "An account with this email already exists."}
    patient = await prisma.patient.create(
        data={
            "name": name,
            "email": email,
            "passwordHash": hash_password(password),
        }
    )
    return {"id": str(patient.id), "email": patient.email, "name": patient.name, "role": "PATIENT"}


async def login_doctor(email: str, password: str) -> dict | None:
    prisma = get_prisma()
    doc = await prisma.doctor.find_unique(where={"email": email})
    pw = getattr(doc, "passwordHash", None) or getattr(doc, "password_hash", None)
    if not doc or not pw or not verify_password(password, pw):
        return None
    return {"id": str(doc.id), "email": doc.email, "name": doc.name, "role": "DOCTOR"}


async def login_patient(email: str, password: str) -> dict | None:
    prisma = get_prisma()
    patient = await prisma.patient.find_unique(where={"email": email})
    pw = getattr(patient, "passwordHash", None) or getattr(patient, "password_hash", None)
    if not patient or not pw or not verify_password(password, pw):
        return None
    return {"id": str(patient.id), "email": patient.email, "name": patient.name, "role": "PATIENT"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return {
        "id": payload["sub"],
        "email": payload["email"],
        "name": payload["name"],
        "role": payload["role"],
    }
