import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import prediction
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.limiter import limiter

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SANRAKSHA API",
    description="Landslide early-warning system",
    version="0.2.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction.router)


@app.on_event("startup")
def on_startup():
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


@app.get("/")
def root():
    return {"status": "ok", "service": "SANRAKSHA API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
