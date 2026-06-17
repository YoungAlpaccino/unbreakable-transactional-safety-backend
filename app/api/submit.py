"""
The single inbound endpoint (sketch).

Every accepted call:
  1. passes validation, OR is rejected with 422 before any write
  2. is recorded as a Submission (unique idempotency key)
  3. enqueues an OutboxEntry inside the SAME transaction

If the circuit breaker is open we 503 immediately so the client can back off.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import SubmissionRequest, SubmissionAck
from app.services.validator import validate
from app.services.idempotency import claim_or_reuse
from app.services.outbox import enqueue
from app.services.breaker import downstream_breaker

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SubmissionAck)
async def submit(
    payload: SubmissionRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    if downstream_breaker.is_open():
        raise HTTPException(503, "downstream cooling")

    err = validate(payload)
    if err:
        raise HTTPException(422, err)

    async with db.begin():
        existing = await claim_or_reuse(db, idempotency_key, payload)
        if existing.replayed:
            return SubmissionAck(ok=True, id=existing.id, replayed=True)
        await enqueue(db, submission_id=existing.id, payload=payload)

    return SubmissionAck(ok=True, id=existing.id, replayed=False)
