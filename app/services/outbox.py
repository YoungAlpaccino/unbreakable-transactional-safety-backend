"""
Transactional outbox (sketch).

`enqueue` inserts an OutboxEntry inside the caller's transaction, so the
ack-to-client and the queue-for-dispatch commit atomically.

`OutboxWorker` polls the table, claims rows with SKIP LOCKED, and
dispatches them. Failures land in the replay log with the original payload
intact — never dropped.
"""
import asyncio
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

from app.database import SessionFactory
from app.models import OutboxEntry, ReplayLog
from app.services.breaker import downstream_breaker
from app.config import settings

logger = logging.getLogger(__name__)


async def enqueue(db: AsyncSession, *, submission_id: int, payload):
    db.add(OutboxEntry(
        submission_id=submission_id,
        payload_json=payload.json(),
        state="pending",
    ))


class OutboxWorker:
    async def run(self):
        async with aiohttp.ClientSession() as http:
            while True:
                try:
                    await self._tick(http)
                except asyncio.CancelledError:
                    return
                except Exception:
                    logger.exception("outbox tick failed")
                await asyncio.sleep(settings.outbox_poll_interval)

    async def _tick(self, http: aiohttp.ClientSession):
        async with SessionFactory() as db:
            async with db.begin():
                rows = (await db.execute(
                    select(OutboxEntry)
                    .where(OutboxEntry.state == "pending")
                    .order_by(OutboxEntry.id)
                    .limit(settings.outbox_batch_size)
                    .with_for_update(skip_locked=True)
                )).scalars().all()

                for row in rows:
                    row.state = "claimed"

            for row in rows:
                await self._dispatch(http, db, row)

    async def _dispatch(self, http, db, row: OutboxEntry):
        try:
            async with http.post(settings.downstream_url, data=row.payload_json,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status >= 500:
                    raise RuntimeError(f"downstream {r.status}")
            async with db.begin():
                await db.execute(
                    update(OutboxEntry)
                    .where(OutboxEntry.id == row.id)
                    .values(state="dispatched")
                )
            downstream_breaker.record_success()
        except Exception as e:
            logger.warning("dispatch %s failed: %s", row.id, e)
            downstream_breaker.record_failure()
            async with db.begin():
                db.add(ReplayLog(
                    outbox_id=row.id,
                    payload_json=row.payload_json,
                    error=str(e)[:1024],
                ))
                await db.execute(
                    update(OutboxEntry)
                    .where(OutboxEntry.id == row.id)
                    .values(state="failed")
                )
