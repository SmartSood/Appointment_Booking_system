"""Seed doctors and patients (with passwordHash for login). Run after prisma db push."""
import asyncio
from app.db import connect_prisma, get_prisma, disconnect_prisma

try:
    from bcrypt import hashpw, gensalt
    def _hash_password(password: str) -> str:
        return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")
except ImportError:
    from app.auth import hash_password as _hash_password


async def seed():
    await connect_prisma()
    try:
        prisma = get_prisma()
        # Default password for seeded users (change after first login in production)
        default_pw = _hash_password("password123")
        doctors_to_seed = [
            ("Dr. Ahuja", "ahuja@clinic.com", "General Practice"),
            ("Dr. Smith", "smith@clinic.com", "Cardiology"),
            ("Dr. Lee", "lee@clinic.com", "Pediatrics"),
        ]
        for name, email, spec in doctors_to_seed:
            existing = await prisma.doctor.find_first(where={"email": email})
            if not existing:
                dr = await prisma.doctor.create(
                    data={
                        "name": name,
                        "email": email,
                        "passwordHash": default_pw,
                        "specialization": spec,
                    }
                )
                for day in range(5):  # Mon-Fri
                    await prisma.availabilityslot.create(
                        data={
                            "doctorId": dr.id,
                            "dayOfWeek": day,
                            "startTime": "09:00",
                            "endTime": "17:00",
                            "isAvailable": True,
                        }
                    )
                print(f"Seeded {name} and availability.")
            else:
                print(f"{name} already exists.")
        # Sample patient for testing bookings (always ensure one exists)
        existing_patient = await prisma.patient.find_first(where={"email": "patient@example.com"})
        if not existing_patient:
            await prisma.patient.create(
                data={"name": "Jane Patient", "email": "patient@example.com", "passwordHash": default_pw}
            )
            print("Seeded sample patient (Jane Patient, patient@example.com).")
    finally:
        await disconnect_prisma()


if __name__ == "__main__":
    asyncio.run(seed())
