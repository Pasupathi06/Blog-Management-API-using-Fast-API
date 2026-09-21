from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Post, User
from app.schemas import CommentCreate, CommentResponse
from app.dependencies import get_current_user
from app.subscription_service import check_comment_limit
from app.services.notification_service import send_comment_notification


router = APIRouter(
    prefix="/posts",
    tags=["Comments"]
)


# ---------- Add Comment ----------

@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
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

    # Check subscription comment limit
    check_comment_limit(current_user, db)

    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        text=comment_data.text
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Send notification email in the background
    background_tasks.add_task(
        send_comment_notification,
        post.author.email,
        post.title,
        current_user.username,
        new_comment.created_at,
    )

    return new_comment


# ---------- Get Comments ----------

@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
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

    comments = db.query(Comment).filter(
        Comment.post_id == post_id
    ).order_by(
        Comment.created_at.asc()
    ).all()

    return comments