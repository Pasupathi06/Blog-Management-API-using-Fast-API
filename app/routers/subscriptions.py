from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, SubscriptionPlan, BillingHistory
from app.dependencies import get_current_user
from app.invoice_service import generate_invoice


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"]
)


# ---------------------------------------------------------
# GET ALL SUBSCRIPTION PLANS
# ---------------------------------------------------------
@router.get("/plans")
def get_subscription_plans(
    db: Session = Depends(get_db)
):
    plans = (
        db.query(SubscriptionPlan)
        .order_by(SubscriptionPlan.id)
        .all()
    )

    return [
        {
            "id": plan.id,
            "name": plan.name,
            "price": plan.price,
            "post_limit": plan.post_limit,
            "image_limit": plan.image_limit,
            "like_limit": plan.like_limit,
            "comment_limit": plan.comment_limit
        }
        for plan in plans
    ]


# ---------------------------------------------------------
# GET CURRENT USER SUBSCRIPTION
# ---------------------------------------------------------
@router.get("/my")
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .first()
    )

    if not user or not user.subscription_plan:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found."
        )

    # Check subscription expiry
    if user.subscription_end and user.subscription_end < datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. Kindly renew your plan."
        )

    plan = user.subscription_plan

    return {
        "username": user.username,
        "plan": plan.name,
        "price": plan.price,
        "subscription_start": user.subscription_start,
        "subscription_end": user.subscription_end,
        "status": "active",
        "limits": {
            "posts": plan.post_limit,
            "images": plan.image_limit,
            "likes": plan.like_limit,
            "comments": plan.comment_limit
        }
    }


# ---------------------------------------------------------
# SUBSCRIBE / UPGRADE PLAN
# ---------------------------------------------------------
@router.post("/subscribe/{plan_id}")
def subscribe_to_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find selected plan
    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.id == plan_id)
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Subscription plan not found."
        )

    # Subscription period
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)

    # Generate transaction ID
    transaction_id = f"TXN-{uuid4().hex[:12].upper()}"

    # Generate invoice PDF
    invoice_path = generate_invoice(
        username=current_user.username,
        plan_name=plan.name,
        price=plan.price,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id
    )

    # Create billing history
    billing = BillingHistory(
        user_id=current_user.id,
        plan_id=plan.id,
        amount=plan.price,
        transaction_id=transaction_id,
        invoice_path=invoice_path,
        start_date=start_date,
        end_date=end_date
    )

    # Update user's active subscription
    current_user.subscription_plan_id = plan.id
    current_user.subscription_start = start_date
    current_user.subscription_end = end_date

    db.add(billing)
    db.commit()
    db.refresh(billing)

    return {
        "message": "Subscription activated successfully.",
        "username": current_user.username,
        "plan": plan.name,
        "price": plan.price,
        "transaction_id": transaction_id,
        "subscription_start": start_date,
        "subscription_end": end_date,
        "invoice_path": invoice_path
    }


# ---------------------------------------------------------
# GET BILLING HISTORY
# ---------------------------------------------------------
@router.get("/billing")
def get_billing_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = (
        db.query(BillingHistory)
        .filter(BillingHistory.user_id == current_user.id)
        .order_by(BillingHistory.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "plan": item.plan.name,
            "amount": item.amount,
            "transaction_id": item.transaction_id,
            "invoice_path": item.invoice_path,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "created_at": item.created_at
        }
        for item in history
    ]


# ---------------------------------------------------------
# GET SINGLE BILLING / INVOICE DETAILS
# ---------------------------------------------------------
@router.get("/billing/{billing_id}")
def get_billing_details(
    billing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    billing = (
        db.query(BillingHistory)
        .filter(
            BillingHistory.id == billing_id,
            BillingHistory.user_id == current_user.id
        )
        .first()
    )

    if not billing:
        raise HTTPException(
            status_code=404,
            detail="Billing record not found."
        )

    return {
        "id": billing.id,
        "username": billing.user.username,
        "plan": billing.plan.name,
        "amount": billing.amount,
        "transaction_id": billing.transaction_id,
        "invoice_path": billing.invoice_path,
        "start_date": billing.start_date,
        "end_date": billing.end_date,
        "created_at": billing.created_at
    }