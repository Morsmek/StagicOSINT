"""
StagicOSINT - FastAPI application entry point.

Dev:  py -m uvicorn main:app --reload --port 8000
Prod: launched via launcher.py (bundled exe)
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from database import init_db
from routers import graphs, entities, transforms, api_keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Open Source Link Analysis & OSINT Framework",
    lifespan=lifespan,
)

# CORS - allow local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers (must be registered BEFORE static file mount)
app.include_router(graphs.router,    prefix=settings.API_PREFIX)
app.include_router(entities.router,  prefix=settings.API_PREFIX)
app.include_router(transforms.router, prefix=settings.API_PREFIX)
app.include_router(api_keys.router,  prefix=settings.API_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static file serving (React build)
# In dev mode:  serves from ../../frontend/dist (if it exists)
# In exe mode:  serves from sys._MEIPASS/frontend_dist (bundled by PyInstaller)
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    _frontend_dist = Path(sys._MEIPASS) / "frontend_dist"
else:
    _frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

if _frontend_dist.exists():
    # Mount at "/" as a fallback — API routes above always take priority
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "note": "Run 'npm run build' in the frontend folder to serve the UI from here.",
        }
