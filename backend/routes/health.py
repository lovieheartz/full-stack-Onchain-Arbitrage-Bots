from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.get("/status")
async def detailed_status():
    """Detailed system status"""
    return {
        "api": "running",
        "database": "not_required",
        "google_sheets": "configured" if os.path.exists("credentials.json") else "not_configured",
        "strategies": "loaded",
        "timestamp": datetime.now().isoformat()
    }