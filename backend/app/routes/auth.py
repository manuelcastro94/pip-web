"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta

from ..database import get_db
from ..auth import AuthService, get_current_user

router = APIRouter()

class GoogleTokenRequest(BaseModel):
    token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/google", response_model=LoginResponse)
async def google_auth(token_request: GoogleTokenRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth token
    """
    try:
        # Verify Google token
        user_info = AuthService.verify_google_token(token_request.token)
        
        # Get or create user in database
        user = AuthService.get_or_create_user(db, user_info)
        
        # Create access token
        access_token_expires = timedelta(minutes=60*24)  # 24 hours
        access_token = AuthService.create_access_token(
            data={"sub": user["email"]}, 
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user

@router.post("/logout")
async def logout():
    """
    Logout endpoint (mainly for frontend to clear tokens)
    """
    return {"message": "Successfully logged out"}

@router.get("/status")
async def auth_status():
    """
    Check if authentication is properly configured
    """
    import os
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    return {
        "google_client_configured": bool(client_id),
        "google_client_id": client_id if client_id else None,  # Safe to expose
        "secret_key_configured": bool(os.getenv("SECRET_KEY")),
    }

@router.get("/config")
async def auth_config():
    """
    Get public authentication configuration
    """
    import os
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured"
        )
    
    return {
        "google_client_id": client_id
    }