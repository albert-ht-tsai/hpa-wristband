from fastapi import APIRouter

from src.core.deps import CurrentUser, SessionDep
from src.user.schemas.user_schema import UpdateUserResponse, UserProfileRequest, UserProfileResponse
from src.user.services.user_service import get_profile, update_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: CurrentUser):
    return UserProfileResponse.model_validate(get_profile(current_user))


@router.put("/me", response_model=UpdateUserResponse)
def update_me(body: UserProfileRequest, db: SessionDep, current_user: CurrentUser):
    update_profile(db, current_user, body)
    return UpdateUserResponse(code=200, msg="User information updated successfully")
