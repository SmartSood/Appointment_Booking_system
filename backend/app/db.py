"""Prisma client for database. Connect at startup, disconnect at shutdown."""
from prisma import Prisma

_prisma: Prisma | None = None


def get_prisma() -> Prisma:
    if _prisma is None:
        raise RuntimeError("Prisma not connected. Call connect_prisma() at startup.")
    return _prisma


async def connect_prisma() -> None:
    global _prisma
    _prisma = Prisma()
    await _prisma.connect()


async def disconnect_prisma() -> None:
    global _prisma
    if _prisma is not None:
        await _prisma.disconnect()
        _prisma = None


async def init_db() -> None:
    """No-op for Prisma (tables created via prisma db push or migrate)."""
    pass
