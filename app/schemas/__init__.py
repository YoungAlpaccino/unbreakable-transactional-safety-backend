"""
Pydantic contracts (sketch).
"""
from pydantic import BaseModel


class SubmissionRequest(BaseModel):
    kind:   str
    actor:  str
    amount: float


class SubmissionAck(BaseModel):
    ok:       bool
    id:       int
    replayed: bool
