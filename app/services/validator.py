"""
Pre-flight validation (sketch).

These are the rules that *also* live downstream — we run them here so
bad inputs fail fast and never enter the outbox.
"""
from typing import Optional


def validate(payload) -> Optional[str]:
    if not payload.kind:
        return "missing kind"
    if payload.amount is None:
        return "missing amount"
    if payload.amount <= 0:
        return "amount must be > 0"
    if len(payload.actor) > 64:
        return "actor too long"
    return None
