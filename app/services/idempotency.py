"""
Idempotency key gate (sketch).

The first call inserts a row keyed by (idempotency_key UNIQUE).
A retry with the same key returns the original row instead of duplicating
the side-effect downstream.
"""
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Submission


@dataclass
class ClaimResult:
    id: int
    replayed: bool


async def claim_or_reuse(db: AsyncSession, key: str, payload) -> ClaimResult:
    existing = (await db.execute(
        select(Submission).where(Submission.idempotency_key == key)
    )).scalar_one_or_none()

    if existing is not None:
        return ClaimResult(id=existing.id, replayed=True)

    row = Submission(idempotency_key=key, payload_kind=payload.kind)
    db.add(row)
    await db.flush()
    return ClaimResult(id=row.id, replayed=False)
