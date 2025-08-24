#!/usr/bin/env python3
"""
CEPIP Web Application - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

from app.database import engine, SessionLocal, Base
from app.routes import api_router

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="CEPIP API",
    description="API para el sistema de gestión CEPIP migrado desde Access",
    version="1.0.0"
)

# CORS middleware
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,http://localhost").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint (must be before static files mount)
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        from app.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "service": "CEPIP API", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "service": "CEPIP API", "error": str(e)}

@app.get("/")
async def root():
    return {"message": "CEPIP API is running", "docs": "/docs"}

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files (frontend) - must be last
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
elif os.path.exists("../frontend"):
    app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
elif os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )