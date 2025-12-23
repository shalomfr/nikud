"""
FastAPI Application Entry Point
נקודת כניסה לאפליקציית FastAPI
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, get_db
from app.routers import words, sources, analysis
from app.services.search_engine import search_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    init_db()
    yield
    # Shutdown


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="מערכת מתקדמת לניתוח טקסטים עבריים עם ניקוד",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(words.router)
app.include_router(sources.router)
app.include_router(analysis.router)


# Page routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    דף הבית - חיפוש מילים
    Home page - Word search
    """
    db = next(get_db())
    try:
        stats = search_engine.get_statistics(db)
        sources_list = search_engine.get_sources(db)
        categories = search_engine.get_categories(db)
    finally:
        db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": stats,
            "sources": sources_list,
            "categories": categories,
            "app_name": settings.app_name
        }
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """
    דף טעינת טקסט
    Text upload page
    """
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "app_name": settings.app_name
        }
    )


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """
    דף סטטיסטיקות
    Statistics page
    """
    db = next(get_db())
    try:
        stats = search_engine.get_statistics(db)
        sources_list = search_engine.get_sources(db)
        categories = search_engine.get_categories(db)
    finally:
        db.close()

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "stats": stats,
            "sources": sources_list,
            "categories": categories,
            "app_name": settings.app_name
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "version": settings.app_version}

