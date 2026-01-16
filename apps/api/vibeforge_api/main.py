"""FastAPI application entry point for VibeForge Local UI API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vibeforge_api.routers import sessions, control

app = FastAPI(
    title="VibeForge API",
    description="Local UI API for VibeForge session orchestration",
    version="0.1.0",
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(control.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "vibeforge-api"}
