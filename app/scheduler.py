import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.models import Post


async def publish_scheduled_posts():
    """
    Automatically publish scheduled posts
    when their scheduled_at time is reached.
    """

    while True:
        db = SessionLocal()

        try:
            now = datetime.utcnow()

            scheduled_posts = (
                db.query(Post)
                .filter(
                    Post.status == "scheduled",
                    Post.scheduled_at.isnot(None),
                    Post.scheduled_at <= now
                )
                .all()
            )

            for post in scheduled_posts:

                post.status = "published"
                post.published_at = now
                post.scheduled_at = None

                print(
                    f"Scheduled post published: "
                    f"id={post.id}, title={post.title}"
                )

            if scheduled_posts:
                db.commit()

        except Exception as error:

            db.rollback()

            print(
                f"Scheduled publishing error: {error}"
            )

        finally:
            db.close()

        # Check every 30 seconds
        await asyncio.sleep(30)