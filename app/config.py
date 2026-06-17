"""
Settings (sketch).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name:       str  = "unbreakable-safety-sketch"
    db_url:         str  = "postgresql+asyncpg://demo:demo@localhost:5432/safety"
    downstream_url: str  = "http://localhost:9000"
    debug:          bool = False

    breaker_failure_threshold: int   = 5
    breaker_cooldown_seconds:  float = 30.0
    outbox_poll_interval:      float = 1.0
    outbox_batch_size:         int   = 64

    class Config:
        env_file = ".env"


settings = Settings()
