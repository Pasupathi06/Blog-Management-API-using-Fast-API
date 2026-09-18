from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine
from app import models

from app.routers.auth import router as auth_router
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router
from app.routers.likes import router as likes_router
from app.routers.subscriptions import router as subscriptions_router


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Blog Management API",
    description="A mini blogging system built with FastAPI",
    version="1.0.0"
)


# =========================================================
# SERVE MEDIA FILES
# =========================================================

app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media"
)


# =========================================================
# INCLUDE ROUTERS
# =========================================================

# Authentication
app.include_router(auth_router)

# Posts
app.include_router(posts_router)

# Comments
app.include_router(comments_router)

# Likes
app.include_router(likes_router)

# Subscriptions
app.include_router(subscriptions_router)


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Blog Management API is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================================================
# CUSTOM OPENAPI SCHEMA
# =========================================================
#
# This makes Swagger UI understand the images field
# as a binary file upload instead of a normal string.
#
# Actual backend UploadFile logic remains unchanged.
# =========================================================

def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )

    components = openapi_schema.get(
        "components",
        {}
    )

    schemas = components.get(
        "schemas",
        {}
    )

    for schema in schemas.values():

        properties = schema.get(
            "properties",
            {}
        )

        for field_name, field_schema in properties.items():

            if field_name != "images":
                continue

            # -------------------------------------------------
            # Case 1: images is directly an array
            # -------------------------------------------------

            if field_schema.get("type") == "array":

                items = field_schema.get(
                    "items",
                    {}
                )

                if items.get("type") == "string":

                    items["format"] = "binary"

                    items["contentMediaType"] = (
                        "application/octet-stream"
                    )

            # -------------------------------------------------
            # Case 2: images is inside anyOf
            # -------------------------------------------------

            if "anyOf" in field_schema:

                for option in field_schema["anyOf"]:

                    if option.get("type") == "array":

                        items = option.get(
                            "items",
                            {}
                        )

                        if items.get("type") == "string":

                            items["format"] = "binary"

                            items["contentMediaType"] = (
                                "application/octet-stream"
                            )

    app.openapi_schema = openapi_schema

    return app.openapi_schema


# Tell FastAPI to use our custom OpenAPI schema
app.openapi = custom_openapi