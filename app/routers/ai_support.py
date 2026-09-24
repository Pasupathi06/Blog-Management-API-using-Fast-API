from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models import User
from app.services.ai_support_service import generate_ai_response


router = APIRouter(
    prefix="/api/ai-support",
    tags=["AI Support"]
)


class AISupportRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's support question"
    )


class AISupportResponse(BaseModel):
    message: str
    response: str


@router.post(
    "/",
    response_model=AISupportResponse
)
def ai_support(
    request: AISupportRequest,
    current_user: User = Depends(get_current_user)
):
    ai_response = generate_ai_response(
        request.message
    )

    return {
        "message": request.message,
        "response": ai_response
    }