def generate_ai_response(message: str) -> str:
    """
    Generate a support response based on predefined FAQs.

    This is a mock AI service for the initial implementation.
    It can later be replaced with OpenAI, HuggingFace,
    or another LLM provider.
    """

    text = message.lower().strip()

    if (
        "create post" in text
        or "create a post" in text
        or "new post" in text
        or "how to post" in text
    ):
        return (
            "To create a post, log in to your account and use the "
            "Create Post option. Enter the title and content, then "
            "submit the post. Your post will be created if your "
            "subscription plan allows it."
        )

    if (
        "edit post" in text
        or "update post" in text
        or "modify post" in text
    ):
        return (
            "To edit a post, open your own post and use the update/edit "
            "option. You can update the title and content. You can "
            "only edit posts that belong to your account."
        )

    if (
        "delete post" in text
        or "remove post" in text
    ):
        return (
            "To delete a post, open one of your own posts and use the "
            "delete option. Only the post owner can delete the post."
        )

    if (
        "subscription" in text
        or "plan" in text
        or "upgrade" in text
    ):
        return (
            "The platform provides Basic, Premium, and Pro subscription "
            "plans. Each plan has different limits for posts, images, "
            "likes, and comments. You can view available plans from "
            "the subscription section."
        )

    if (
        "billing" in text
        or "invoice" in text
        or "payment" in text
    ):
        return (
            "You can check your billing history from the subscription "
            "section. Billing records include the selected plan, amount, "
            "transaction ID, invoice information, and subscription dates."
        )

    if (
        "profile" in text
        or "account" in text
        or "username" in text
    ):
        return (
            "Your account information is associated with your authenticated "
            "user account. Use the profile or account section to manage "
            "your account details."
        )

    if (
        "dashboard" in text
        or "analytics" in text
        or "statistics" in text
        or "stats" in text
    ):
        return (
            "The User Dashboard displays your personal activity analytics, "
            "including total posts, total comments, total likes received, "
            "and post-level likes and comments. Post views are shown as "
            "zero when view tracking is not enabled."
        )

    if (
        "comment" in text
        or "comments" in text
    ):
        return (
            "You can add comments to blog posts while authenticated. "
            "Comments are associated with the post and your user account. "
            "The post owner can receive a notification when someone comments."
        )

    if (
        "like" in text
        or "likes" in text
    ):
        return (
            "You can like a blog post while authenticated. The post owner "
            "receives an in-app notification when their post is liked."
        )

    if (
        "notification" in text
        or "notifications" in text
    ):
        return (
            "The Notification Center is available from the dashboard. "
            "It shows alerts for likes, comments, and subscription activity. "
            "You can mark individual notifications as read or unread, "
            "or mark all notifications as read."
        )

    if (
        "help" in text
        or "support" in text
        or "hello" in text
        or "hi" in text
        or "hey" in text
    ):
        return (
            "Hello! I'm your Blog Management support assistant. "
            "I can help you with posts, comments, likes, subscriptions, "
            "billing, profile management, notifications, and dashboard analytics."
        )

    return (
        "I'm currently able to help with posts, comments, likes, "
        "subscriptions, billing, profile management, notifications, "
        "and dashboard analytics. Please ask me about one of these topics."
    )