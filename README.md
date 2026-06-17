# Unbreakable Transactional Safety Backend

> ## NOTE
> **The code in this repository is a demonstration of the architecture and is not a working safety service.**
> Entities, table layouts, validation rules, and downstream sinks have been deliberately abstracted.
> The defense-in-depth pattern is the point; the specific rules are placeholders.

---

## What this project demonstrates

A backend whose only job is to make sure no transactional call ever gets lost, double-applied,
or silently corrupted on the way through. It sits in front of whatever business service actually
does the work, and around that service it adds:

1. **Idempotency keys** — every inbound call carries a client-issued key; a Postgres unique
   index makes double submission a no-op rather than a duplicate.
2. **Pre-flight validation** — the same checks that the downstream service does, run *here*
   first, so we fail fast on bad inputs without touching real state.
3. **Outbox pattern** — every accepted call is written to an `outbox` table inside the same
   DB transaction as the business decision. A worker drains the outbox into downstream systems
   with at-least-once semantics.
4. **Replay log** — failed dispatches are kept verbatim for forensic replay, never quietly dropped.
5. **Circuit breaker** — when the downstream is hot, we trip and shed load with explicit 503s
   instead of piling on.

The result is a service that loses *nothing* — every call either lands, idempotently re-lands,
or is parked in the replay log with the original payload intact.

## High-level diagram

```
   client ──► FastAPI ──► validate ──► idempotency key check ──┐
                                                                │
                                                                ▼
                                                ┌───────────────────────────┐
                                                │  TX: write decision +     │
                                                │      outbox row           │
                                                └───────────────────────────┘
                                                                │
                                          ┌─────────────────────┘
                                          ▼
                                    outbox worker
                                          │
                                          ▼
                                  downstream service
                                          │
                                  ┌───────┴────────┐
                                  ▼                ▼
                                 ok             failure
                                  │                │
                                  ▼                ▼
                            mark_dispatched   replay_log
```

## Files in this showcase

| File | What it shows |
|------|---------------|
| `Dockerfile`, `docker-compose.yml` | Local container topology (app + postgres). |
| `app/main.py`              | FastAPI app, lifespan, middleware. |
| `app/config.py`            | Settings. |
| `app/database.py`          | Async SQLAlchemy engine + session factory. |
| `app/api/__init__.py`      | Router aggregator. |
| `app/api/submit.py`        | The single inbound endpoint. |
| `app/services/idempotency.py` | The unique-key gate. |
| `app/services/validator.py`   | Pre-flight checks. |
| `app/services/outbox.py`      | Transactional outbox writer + worker. |
| `app/services/breaker.py`     | In-process circuit breaker. |
| `app/models/__init__.py`      | Submission / outbox / replay tables. |
| `app/schemas/__init__.py`     | Pydantic contracts. |
| `requirements.txt`            | Unpinned dependency surface. |
