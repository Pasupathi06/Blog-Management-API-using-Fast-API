import math
import os
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, User, PostImage
from app.schemas import (
    PostResponse,
    PaginatedPostResponse
)
from app.dependencies import get_current_user
from app.subscription_service import (
    check_post_limit,
    check_image_limit
)


router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


MEDIA_DIR = "media/posts"
os.makedirs(MEDIA_DIR, exist_ok=True)


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024


async def save_image(image: UploadFile):
    extension = os.path.splitext(
        image.filename or ""
    )[1].lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed"
        )

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed"
        )

    contents = await image.read()

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size must be less than 5 MB"
        )

    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = os.path.join(
        MEDIA_DIR,
        filename
    )

    with open(file_path, "wb") as file:
        file.write(contents)

    return f"/media/posts/{filename}"


# =========================================================
# POST RESPONSE HELPER
# =========================================================

def post_to_response(post: Post):
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "image": post.image,
        "images": [
            post_image.image
            for post_image in post.images
        ],
        "author_id": post.author_id,
        "created_at": post.created_at
    }


# =========================================================
# CREATE POST
# =========================================================

@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
    title: Annotated[str, Form(...)],
    content: Annotated[str, Form(...)],

    # Multiple image upload
    images: Annotated[
        list[UploadFile],
        File()
    ] = [],

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check subscription post limit
    check_post_limit(
        current_user,
        db
    )

    # Create post first
    new_post = Post(
        title=title,
        content=content,
        image=None,
        author_id=current_user.id
    )

    db.add(new_post)
    db.flush()

    uploaded_images = images or []

    # Add images
    for image in uploaded_images:

        # Check subscription image limit
        check_image_limit(
            current_user,
            db,
            new_post
        )

        image_url = await save_image(image)

        # Store first image in old Post.image field
        if new_post.image is None:
            new_post.image = image_url

        # Store every image in post_images table
        post_image = PostImage(
            post_id=new_post.id,
            image=image_url
        )

        db.add(post_image)

        # Make newly added image visible
        # to next limit check
        db.flush()

    db.commit()
    db.refresh(new_post)

    return post_to_response(new_post)


# =========================================================
# GET ALL POSTS
# =========================================================

@router.get(
    "/",
    response_model=PaginatedPostResponse
)
def get_posts(
    page: int = Query(
        default=1,
        ge=1
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    search: str | None = Query(
        default=None
    ),
    db: Session = Depends(get_db)
):
    query = db.query(Post)

    if search:
        search_pattern = f"%{search}%"

        query = query.filter(
            (Post.title.ilike(search_pattern)) |
            (Post.content.ilike(search_pattern))
        )

    total = query.count()

    total_pages = (
        math.ceil(total / limit)
        if total > 0
        else 0
    )

    posts = (
        query
        .order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [
            post_to_response(post)
            for post in posts
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# =========================================================
# GET SINGLE POST
# =========================================================

@router.get(
    "/{post_id}",
    response_model=PostResponse
)
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return post_to_response(post)


# =========================================================
# UPDATE POST
# =========================================================

@router.put(
    "/{post_id}",
    response_model=PostResponse
)
async def update_post(
    post_id: int,

    title: Annotated[
        str | None,
        Form()
    ] = None,

    content: Annotated[
        str | None,
        Form()
    ] = None,

    # Multiple image upload
    images: Annotated[
        list[UploadFile],
        File()
    ] = [],

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Only owner can update
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own post"
        )

    if title is not None:
        post.title = title

    if content is not None:
        post.content = content

    uploaded_images = images or []

    # Add new images
    for image in uploaded_images:

        # Check subscription image limit
        check_image_limit(
            current_user,
            db,
            post
        )

        image_url = await save_image(image)

        # Keep old image field updated
        if post.image is None:
            post.image = image_url

        # Store image in post_images table
        post_image = PostImage(
            post_id=post.id,
            image=image_url
        )

        db.add(post_image)

        # Make newly added image visible
        # to next limit check
        db.flush()

    db.commit()
    db.refresh(post)

    return post_to_response(post)


# =========================================================
# DELETE POST
# =========================================================

@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Only owner can delete
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own post"
        )

    db.delete(post)
    db.commit()

    return None