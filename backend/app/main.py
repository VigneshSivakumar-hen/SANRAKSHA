from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import prediction

app = FastAPI(
    title="SANRAKSHA API",
    description="Landslide early-warning system - Phase 1 prototype",
    version="0.1.0",
)

# Allow the Vite dev server (and any origin in this prototype phase) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "SANRAKSHA API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
