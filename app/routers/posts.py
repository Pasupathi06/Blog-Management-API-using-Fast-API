from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, User
from app.schemas import PostCreate, PostUpdate, PostResponse
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


# ---------- Create Post ----------

@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_post = Post(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


# ---------- Get All Posts ----------

@router.get(
    "/",
    response_model=list[PostResponse]
)
def get_posts(
    db: Session = Depends(get_db)
):
    posts = db.query(Post).order_by(
        Post.created_at.desc()
    ).all()

    return posts


# ---------- Get Single Post ----------

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


# ---------- Update Own Post ----------

@router.put(
    "/{post_id}",
    response_model=PostResponse
)
def update_post(
    post_id: int,
    post_data: PostUpdate,
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

    # Only the owner can update the post
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own post"
        )

    if post_data.title is not None:
        post.title = post_data.title

    if post_data.content is not None:
        post.content = post_data.content

    db.commit()
    db.refresh(post)

    return post


# ---------- Delete Own Post ----------

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

    # Only the owner can delete the post
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own post"
        )

    db.delete(post)
    db.commit()

    return None