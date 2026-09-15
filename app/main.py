from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app import models

from app.routers.auth import router as auth_router
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router
from app.routers.likes import router as likes_router


# Create all database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Blog Management API",
    description="A mini blogging system built with FastAPI",
    version="1.0.0"
)

# Serve uploaded images
app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media"
)

# Authentication routes
app.include_router(auth_router)


# Posts routes
app.include_router(posts_router)


# Comments routes
app.include_router(comments_router)
app.include_router(likes_router)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Blog Management API is running"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }