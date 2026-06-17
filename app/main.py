"""
Unbreakable transactional safety backend — entrypoint sketch.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import api_router
from app.services.outbox import OutboxWorker

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
worker_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    global worker_task
    worker = OutboxWorker()
    worker_task = asyncio.create_task(worker.run())
    yield
    worker_task.cancel()


app = FastAPI(
    title=settings.app_name,
    description="Sketch: idempotent inbound + outbox + replay backend.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}
