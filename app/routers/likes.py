from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Like, Post, User
from app.dependencies import get_current_user
from app.email_service import send_email
from app.subscription_service import check_like_limit


router = APIRouter(
    prefix="/posts",
    tags=["Likes"]
)


@router.post(
    "/{post_id}/like",
    status_code=status.HTTP_201_CREATED
)
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check whether post exists
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check whether user already liked this post
    existing_like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already liked this post"
        )

    # Check subscription like limit
    check_like_limit(current_user, db)

    new_like = Like(
        post_id=post_id,
        user_id=current_user.id
    )

    db.add(new_like)
    db.commit()
    db.refresh(new_like)

    # Send email notification to post author
    send_email(
        recipient=post.author.email,
        subject="New Like on Your Blog Post",
        body=(
            f"Hello {post.author.username},\n\n"
            f"Someone liked your post: '{post.title}'\n\n"
            "Regards,\n"
            "Blog Management API"
        )
    )

    return {
        "message": "Post liked successfully",
        "post_id": post_id,
        "user_id": current_user.id
    }


@router.delete(
    "/{post_id}/like",
    status_code=status.HTTP_200_OK
)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check whether post exists
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Find user's like
    existing_like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()

    if not existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not liked this post"
        )

    db.delete(existing_like)
    db.commit()

    return {
        "message": "Post unliked successfully",
        "post_id": post_id,
        "user_id": current_user.id
    }