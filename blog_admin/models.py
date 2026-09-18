from django.db import models


class SubscriptionPlan(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    price = models.IntegerField()
    post_limit = models.IntegerField(null=True, blank=True)
    image_limit = models.IntegerField(null=True, blank=True)
    like_limit = models.IntegerField(null=True, blank=True)
    comment_limit = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "subscription_plans"
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return self.name


class BillingHistory(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    plan_id = models.IntegerField()
    amount = models.IntegerField()
    transaction_id = models.CharField(max_length=100)
    invoice_path = models.CharField(max_length=500, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "billing_history"
        verbose_name = "Billing History"
        verbose_name_plural = "Billing History"

    def __str__(self):
        return self.transaction_id