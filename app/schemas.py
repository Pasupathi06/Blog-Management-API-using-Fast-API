from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# =========================================================
# USER SCHEMAS
# =========================================================

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=100
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


# =========================================================
# LOGIN SCHEMA
# =========================================================

class LoginRequest(BaseModel):
    username: str
    password: str


# =========================================================
# TOKEN SCHEMA
# =========================================================

class Token(BaseModel):
    access_token: str
    token_type: str


# =========================================================
# POST SCHEMAS
# =========================================================

class PostCreate(BaseModel):

    title: str = Field(
        ...,
        min_length=3,
        max_length=200
    )

    content: str = Field(
        ...,
        min_length=1
    )

    # -----------------------------------------------------
    # Publishing option
    #
    # Allowed values:
    # draft
    # scheduled
    # published
    # -----------------------------------------------------

    status: str = Field(
        default="published"
    )

    # -----------------------------------------------------
    # Future publishing date/time
    # -----------------------------------------------------

    scheduled_at: datetime | None = None


class PostUpdate(BaseModel):

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200
    )

    content: str | None = Field(
        default=None,
        min_length=1
    )

    # -----------------------------------------------------
    # Publishing status
    # -----------------------------------------------------

    status: str | None = None

    # -----------------------------------------------------
    # Future publishing date/time
    # -----------------------------------------------------

    scheduled_at: datetime | None = None


class PostResponse(BaseModel):

    id: int

    title: str

    content: str

    # Existing single image
    image: str | None = None

    # Multiple images
    images: list[str] = []

    author_id: int

    created_at: datetime

    # =====================================================
    # SCHEDULED BLOG PUBLISHING
    # =====================================================

    status: str

    scheduled_at: datetime | None = None

    published_at: datetime | None = None

    class Config:
        from_attributes = True


# =========================================================
# PAGINATED POST RESPONSE
# =========================================================

class PaginatedPostResponse(BaseModel):

    items: list[PostResponse]

    total: int

    page: int

    limit: int

    total_pages: int


# =========================================================
# COMMENT SCHEMAS
# =========================================================

class CommentCreate(BaseModel):

    text: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


class CommentResponse(BaseModel):

    id: int

    post_id: int

    user_id: int

    text: str

    created_at: datetime

    class Config:
        from_attributes = True