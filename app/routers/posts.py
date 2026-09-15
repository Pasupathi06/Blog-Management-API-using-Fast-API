import math
import os
import uuid

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
from app.models import Post, User
from app.schemas import (
    PostResponse,
    PaginatedPostResponse
)
from app.dependencies import get_current_user


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


async def save_image(image: UploadFile | None):
    if image is None:
        return None

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG and WEBP images are allowed"
        )

    extension = os.path.splitext(image.filename or "")[1].lower()

    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = os.path.join(
        MEDIA_DIR,
        filename
    )

    contents = await image.read()

    with open(file_path, "wb") as file:
        file.write(contents)

    return f"/media/posts/{filename}"


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_url = await save_image(image)

    new_post = Post(
        title=title,
        content=content,
        image=image_url,
        author_id=current_user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


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

    total_pages = math.ceil(total / limit) if total > 0 else 0

    posts = query.order_by(
        Post.created_at.desc()
    ).offset(
        (page - 1) * limit
    ).limit(
        limit
    ).all()

    return {
        "items": posts,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.get(
    "/{post_id}",
    response_model=PostResponse
)
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return post


@router.put(
    "/{post_id}",
    response_model=PostResponse
)
async def update_post(
    post_id: int,
    title: str | None = Form(default=None),
    content: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own post"
        )

    if title is not None:
        post.title = title

    if content is not None:
        post.content = content

    if image is not None:
        image_url = await save_image(image)
        post.image = image_url

    db.commit()
    db.refresh(post)

    return post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own post"
        )

    db.delete(post)
    db.commit()

    return None