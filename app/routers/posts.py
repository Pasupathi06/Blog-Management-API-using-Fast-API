import math
import os
import uuid
from datetime import datetime

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

os.makedirs(
    MEDIA_DIR,
    exist_ok=True
)


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


# =========================================================
# SAVE IMAGE
# =========================================================

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

    filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = os.path.join(
        MEDIA_DIR,
        filename
    )

    with open(
        file_path,
        "wb"
    ) as file:

        file.write(contents)

    return f"/media/posts/{filename}"


# =========================================================
# VALIDATE PUBLISHING OPTIONS
# =========================================================

def validate_publishing_options(
    publish_status: str,
    scheduled_at: datetime | None
):

    allowed_statuses = {
        "draft",
        "scheduled",
        "published"
    }

    # -----------------------------------------------------
    # Validate status
    # -----------------------------------------------------

    if publish_status not in allowed_statuses:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid status. "
                "Use draft, scheduled or published."
            )
        )

    # -----------------------------------------------------
    # DRAFT
    # -----------------------------------------------------

    if publish_status == "draft":

        if scheduled_at is not None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Draft posts cannot have scheduled_at."
                )
            )

        return

    # -----------------------------------------------------
    # PUBLISHED
    # -----------------------------------------------------

    if publish_status == "published":

        if scheduled_at is not None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Published posts cannot have scheduled_at."
                )
            )

        return

    # -----------------------------------------------------
    # SCHEDULED
    # -----------------------------------------------------

    if publish_status == "scheduled":

        if scheduled_at is None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "scheduled_at is required "
                    "for scheduled posts."
                )
            )

        # Current server time
        now = datetime.utcnow()

        if scheduled_at <= now:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "scheduled_at must be a future datetime."
                )
            )


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

        "created_at": post.created_at,

        "status": post.status,

        "scheduled_at": post.scheduled_at,

        "published_at": post.published_at
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

    title: Annotated[
        str,
        Form(...)
    ],

    content: Annotated[
        str,
        Form(...)
    ],

    # -----------------------------------------------------
    # Publishing status
    # -----------------------------------------------------

    publish_status: Annotated[
        str,
        Form(alias="status")
    ] = "published",

    # -----------------------------------------------------
    # Future publishing date/time
    # -----------------------------------------------------

    scheduled_at: Annotated[
        datetime | None,
        Form()
    ] = None,

    # -----------------------------------------------------
    # Multiple image upload
    # -----------------------------------------------------

    images: Annotated[
        list[UploadFile],
        File()
    ] = [],

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    # =====================================================
    # VALIDATE PUBLISHING OPTIONS
    # =====================================================

    validate_publishing_options(
        publish_status,
        scheduled_at
    )

    # =====================================================
    # CHECK POST LIMIT
    # =====================================================

    check_post_limit(
        current_user,
        db
    )

    # =====================================================
    # SET PUBLISHED TIME
    # =====================================================

    published_at = None

    if publish_status == "published":

        published_at = datetime.utcnow()

    # =====================================================
    # CREATE POST
    # =====================================================

    new_post = Post(

        title=title,

        content=content,

        image=None,

        author_id=current_user.id,

        status=publish_status,

        scheduled_at=scheduled_at,

        published_at=published_at
    )

    db.add(new_post)

    db.flush()

    # =====================================================
    # UPLOAD IMAGES
    # =====================================================

    uploaded_images = images or []

    for image in uploaded_images:

        check_image_limit(
            current_user,
            db,
            new_post
        )

        image_url = await save_image(
            image
        )

        # Keep first image in old field
        if new_post.image is None:

            new_post.image = image_url

        # Store every image
        post_image = PostImage(

            post_id=new_post.id,

            image=image_url
        )

        db.add(post_image)

        db.flush()

    # =====================================================
    # SAVE
    # =====================================================

    db.commit()

    db.refresh(
        new_post
    )

    return post_to_response(
        new_post
    )


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

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    if search:

        search_pattern = (
            f"%{search}%"
        )

        query = query.filter(

            (Post.title.ilike(
                search_pattern
            ))

            |

            (Post.content.ilike(
                search_pattern
            ))
        )

    # -----------------------------------------------------
    # Total
    # -----------------------------------------------------

    total = query.count()

    total_pages = (

        math.ceil(
            total / limit
        )

        if total > 0

        else 0
    )

    # -----------------------------------------------------
    # Posts
    # -----------------------------------------------------

    posts = (

        query

        .order_by(
            Post.created_at.desc()
        )

        .offset(
            (page - 1) * limit
        )

        .limit(
            limit
        )

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

        .filter(
            Post.id == post_id
        )

        .first()
    )

    if not post:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return post_to_response(
        post
    )


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

    publish_status: Annotated[
        str | None,
        Form(alias="status")
    ] = None,

    scheduled_at: Annotated[
        datetime | None,
        Form()
    ] = None,

    images: Annotated[
        list[UploadFile],
        File()
    ] = [],

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    # =====================================================
    # FIND POST
    # =====================================================

    post = (

        db.query(Post)

        .filter(
            Post.id == post_id
        )

        .first()
    )

    if not post:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # =====================================================
    # OWNER CHECK
    # =====================================================

    if post.author_id != current_user.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only update your own post"
            )
        )

    # =====================================================
    # UPDATE TITLE
    # =====================================================

    if title is not None:

        post.title = title

    # =====================================================
    # UPDATE CONTENT
    # =====================================================

    if content is not None:

        post.content = content

    # =====================================================
    # UPDATE PUBLISHING STATUS
    # =====================================================

    if publish_status is not None:

        validate_publishing_options(
            publish_status,
            scheduled_at
        )

        post.status = publish_status

        post.scheduled_at = scheduled_at

        if publish_status == "published":

            post.published_at = (
                datetime.utcnow()
            )

        else:

            post.published_at = None

    elif scheduled_at is not None:

        # -------------------------------------------------
        # If scheduled_at is supplied without changing
        # status, treat it as scheduling request.
        # -------------------------------------------------

        validate_publishing_options(
            "scheduled",
            scheduled_at
        )

        post.status = "scheduled"

        post.scheduled_at = scheduled_at

        post.published_at = None

    # =====================================================
    # ADD NEW IMAGES
    # =====================================================

    uploaded_images = images or []

    for image in uploaded_images:

        check_image_limit(
            current_user,
            db,
            post
        )

        image_url = await save_image(
            image
        )

        # Keep old image field updated
        if post.image is None:

            post.image = image_url

        post_image = PostImage(

            post_id=post.id,

            image=image_url
        )

        db.add(post_image)

        db.flush()

    # =====================================================
    # SAVE
    # =====================================================

    db.commit()

    db.refresh(
        post
    )

    return post_to_response(
        post
    )


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

    current_user: User = Depends(
        get_current_user
    )
):

    post = (

        db.query(Post)

        .filter(
            Post.id == post_id
        )

        .first()
    )

    if not post:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # -----------------------------------------------------
    # Owner check
    # -----------------------------------------------------

    if post.author_id != current_user.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only delete your own post"
            )
        )

    db.delete(
        post
    )

    db.commit()

    return None