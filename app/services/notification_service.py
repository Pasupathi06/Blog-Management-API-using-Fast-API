from datetime import datetime

from app.services.email_service import send_email


def send_comment_notification(
    recipient: str,
    post_title: str,
    actor_name: str,
    timestamp: datetime,
):
    subject = "New Comment on Your Blog Post"

    body = (
        f"Hello,\n\n"
        f"Post Title: {post_title}\n"
        f"User: {actor_name}\n"
        f"Activity: Commented on your post\n"
        f"Timestamp: {timestamp}\n\n"
        f"Regards,\n"
        f"Blog Management API"
    )

    send_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )


def send_like_notification(
    recipient: str,
    post_title: str,
    actor_name: str,
    timestamp: datetime,
):
    subject = "New Like on Your Blog Post"

    body = (
        f"Hello,\n\n"
        f"Post Title: {post_title}\n"
        f"User: {actor_name}\n"
        f"Activity: Liked your post\n"
        f"Timestamp: {timestamp}\n\n"
        f"Regards,\n"
        f"Blog Management API"
    )

    send_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )
