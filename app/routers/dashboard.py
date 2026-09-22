from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Post, Comment, Like
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/user",
    tags=["Dashboard"]
)


@router.get("/dashboard")
def get_user_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # =========================================================
    # TOTAL POSTS CREATED BY CURRENT USER
    # =========================================================

    total_posts = db.query(Post).filter(
        Post.author_id == current_user.id
    ).count()


    # =========================================================
    # TOTAL COMMENTS MADE BY CURRENT USER
    # =========================================================

    total_comments = db.query(Comment).filter(
        Comment.user_id == current_user.id
    ).count()


    # =========================================================
    # GET CURRENT USER'S POSTS
    # =========================================================

    posts = db.query(Post).filter(
        Post.author_id == current_user.id
    ).order_by(
        Post.created_at.asc()
    ).all()


    # =========================================================
    # BUILD POST-WISE ANALYTICS
    # =========================================================

    post_analytics = []

    total_likes_received = 0

    for post in posts:

        likes_count = db.query(Like).filter(
            Like.post_id == post.id
        ).count()

        comments_count = db.query(Comment).filter(
            Comment.post_id == post.id
        ).count()

        total_likes_received += likes_count

        post_analytics.append({
            "post_id": post.id,
            "title": post.title,
            "likes": likes_count,
            "comments": comments_count,
            "created_at": post.created_at
        })


    # =========================================================
    # FINAL DASHBOARD RESPONSE
    # =========================================================

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "summary": {
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_likes_received": total_likes_received,
            "total_post_views": 0
        },
        "posts": post_analytics
    }