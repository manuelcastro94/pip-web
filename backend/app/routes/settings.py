"""
Settings API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from ..database import get_db

router = APIRouter()

class SettingsModel(BaseModel):
    appName: str = "CEPIP"
    recordsPerPage: int = 20
    theme: str = "light"
    language: str = "es"
    notifications: bool = True

# Mock settings storage (in real implementation, this would be in database)
current_settings = {
    "appName": "CEPIP",
    "recordsPerPage": 20,
    "theme": "light",
    "language": "es",
    "notifications": True,
    "lastUpdated": "2024-01-20T10:30:00"
}

@router.get("/")
@router.get("")
async def get_settings():
    """
    Get application settings
    """
    return current_settings

@router.put("/")
async def update_settings(settings: SettingsModel):
    """
    Update application settings
    """
    try:
        # Update settings (in real implementation, save to database)
        current_settings.update(settings.dict())
        current_settings["lastUpdated"] = "2024-01-20T10:30:00"  # Would use datetime.now()
        
        return {
            "message": "Settings updated successfully",
            "settings": current_settings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))