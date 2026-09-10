import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.routes import prediction
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.limiter import limiter

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Bootstrap sample locations + an initial reading on first run only.
    from app.services import prediction_service

    db = SessionLocal()
    try:
        prediction_service.seed_if_empty(db)
    finally:
        db.close()

    if settings.ENABLE_SCHEDULER:
        from app.core.scheduler import start_scheduler

        start_scheduler()

    yield  # app runs here


app = FastAPI(
    title="SANRAKSHA API",
    description="Landslide early-warning system",
    version="0.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
_allow_all_origins = _cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # Wildcard origin + credentials is invalid per the CORS spec (browsers
    # reject it) and unnecessary here anyway — the frontend never sends
    # cookies. Only allow credentials when specific origins are configured.
    allow_credentials=not _allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "SANRAKSHA API", "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness + basic dependency check. Used by Render's healthCheckPath
    (see render.yaml) — a DB failure here means the deploy is marked
    unhealthy instead of silently serving broken requests."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    return {"status": "healthy" if db_ok else "degraded", "database": "ok" if db_ok else "unreachable"}
