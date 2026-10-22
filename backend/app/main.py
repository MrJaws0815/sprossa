"""FastAPI-Hauptanwendung"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown-Events (z.B. DB-Verbindung prüfen)."""
    # Startup
    yield
    # Shutdown
    # await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # Next.js Dev
        "http://localhost:3001",     # Next.js Dev (Test)
        "http://192.168.178.188:3001",  # Test-Instanz
        "http://192.168.178.188:3100",  # Test-Instanz Proxy
        "https://sprossa.de",        # Produktion
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Root Health ──────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


# ─── Routen ────────────────────────────────────────────────────────────────

from app.routes.auth import router as auth_router
from app.routes.households import router as household_router
from app.routes.family import router as family_router
from app.routes.waitlist import router as waitlist_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(household_router, prefix="/api/v1")
app.include_router(family_router, prefix="/api/v1")
app.include_router(waitlist_router, prefix="/api/v1")