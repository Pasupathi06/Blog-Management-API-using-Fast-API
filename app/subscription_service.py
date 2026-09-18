from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    User,
    SubscriptionPlan,
    Post,
    PostImage,
    Comment,
    Like
)


PLAN_LIMIT_MESSAGE = (
    "You’ve reached your plan limit. "
    "Kindly upgrade your plan to continue."
)


def get_active_plan(
    user: User,
    db: Session
) -> SubscriptionPlan:

    user = (
        db.query(User)
        .filter(User.id == user.id)
        .first()
    )

    if not user or not user.subscription_plan:
        raise HTTPException(
            status_code=403,
            detail="No active subscription found. Kindly subscribe to a plan."
        )

    if (
        user.subscription_end
        and user.subscription_end < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. Kindly renew your plan."
        )

    return user.subscription_plan


def check_post_limit(
    user: User,
    db: Session
):
    plan = get_active_plan(user, db)

    # None means unlimited
    if plan.post_limit is None:
        return

    post_count = (
        db.query(Post)
        .filter(Post.author_id == user.id)
        .count()
    )

    if post_count >= plan.post_limit:
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE
        )


def check_comment_limit(
    user: User,
    db: Session
):
    plan = get_active_plan(user, db)

    # None means unlimited
    if plan.comment_limit is None:
        return

    comment_count = (
        db.query(Comment)
        .filter(Comment.user_id == user.id)
        .count()
    )

    if comment_count >= plan.comment_limit:
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE
        )


def check_like_limit(
    user: User,
    db: Session
):
    plan = get_active_plan(user, db)

    # None means unlimited
    if plan.like_limit is None:
        return

    like_count = (
        db.query(Like)
        .filter(Like.user_id == user.id)
        .count()
    )

    if like_count >= plan.like_limit:
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE
        )


def check_image_limit(
    user: User,
    db: Session,
    post: Post
):
    plan = get_active_plan(user, db)

    # None means unlimited
    if plan.image_limit is None:
        return

    # Count images already stored in post_images
    image_count = (
        db.query(PostImage)
        .filter(PostImage.post_id == post.id)
        .count()
    )

    # Backward compatibility:
    # Existing posts may have an image stored
    # in the old Post.image column.
    if image_count == 0 and post.image:
        image_count = 1

    # Check plan image limit
    if image_count >= plan.image_limit:
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE
        )