"""
Abstract tables (sketch).

Three tables — Submission (the idempotent inbound record),
OutboxEntry (the at-least-once dispatch queue), and ReplayLog (the
forensic safety net).
"""
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, DateTime, Text, Index,
)
from app.database import Base


class Submission(Base):
    __tablename__ = "submissions"
    id              = Column(BigInteger, primary_key=True)
    idempotency_key = Column(String(128), unique=True, index=True)
    payload_kind    = Column(String(32), index=True)
    received_at     = Column(DateTime, default=datetime.utcnow, index=True)


class OutboxEntry(Base):
    __tablename__ = "outbox"
    id            = Column(BigInteger, primary_key=True)
    submission_id = Column(BigInteger, index=True)
    payload_json  = Column(Text)
    state         = Column(String(16), index=True)   # pending|claimed|dispatched|failed
    queued_at     = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_outbox_state_queued", "state", "queued_at"),
    )


class ReplayLog(Base):
    __tablename__ = "replay_log"
    id           = Column(BigInteger, primary_key=True)
    outbox_id    = Column(BigInteger, index=True)
    payload_json = Column(Text)
    error        = Column(String(1024))
    failed_at    = Column(DateTime, default=datetime.utcnow, index=True)
