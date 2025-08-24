"""
Authentication system using Google OAuth
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

from .database import get_db
from .models.user import User

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

security = HTTPBearer()

class AuthService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return email
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def verify_google_token(token: str):
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo['name'],
                'picture': idinfo.get('picture'),
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )

    @staticmethod
    def get_or_create_user(db: Session, user_info: dict):
        # Check if this is the first user (should be admin)
        user_count_result = db.execute(text("SELECT COUNT(*) FROM users"))
        is_first_user = user_count_result.scalar() == 0
        
        # Try to find existing user
        result = db.execute(
            text("SELECT * FROM users WHERE google_id = :google_id OR email = :email"),
            {"google_id": user_info["google_id"], "email": user_info["email"]}
        )
        existing_user = result.fetchone()
        
        if existing_user:
            # Update last login
            db.execute(
                text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": existing_user[0]}
            )
            db.commit()
            return {
                "id": existing_user[0],
                "google_id": existing_user[1],
                "email": existing_user[2],
                "name": existing_user[3],
                "picture": existing_user[4],
                "is_active": existing_user[5],
                "is_admin": existing_user[6],
            }
        else:
            # Create new user (first user becomes admin)
            user_data = {**user_info, "is_admin": is_first_user}
            db.execute(
                text("""
                    INSERT INTO users (google_id, email, name, picture, is_active, is_admin, created_at, last_login)
                    VALUES (:google_id, :email, :name, :picture, true, :is_admin, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                user_data
            )
            db.commit()
            
            # Get the newly created user
            result = db.execute(
                text("SELECT * FROM users WHERE google_id = :google_id"),
                {"google_id": user_info["google_id"]}
            )
            new_user = result.fetchone()
            return {
                "id": new_user[0],
                "google_id": new_user[1],
                "email": new_user[2],
                "name": new_user[3],
                "picture": new_user[4],
                "is_active": new_user[5],
                "is_admin": new_user[6],
            }

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = AuthService.verify_token(token)
    
    result = db.execute(
        text("SELECT * FROM users WHERE email = :email AND is_active = true"),
        {"email": email}
    )
    user = result.fetchone()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "id": user[0],
        "google_id": user[1],
        "email": user[2],
        "name": user[3],
        "picture": user[4],
        "is_active": user[5],
        "is_admin": user[6],
    }

def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user