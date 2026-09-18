from django.contrib import admin

from .models import SubscriptionPlan, BillingHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "post_limit",
        "image_limit",
        "like_limit",
        "comment_limit",
    )

    search_fields = ("name",)

    ordering = ("id",)


@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "plan_id",
        "amount",
        "transaction_id",
        "start_date",
        "end_date",
        "created_at",
    )

    search_fields = ("transaction_id",)

    list_filter = ("plan_id", "amount")

    ordering = ("-created_at",)