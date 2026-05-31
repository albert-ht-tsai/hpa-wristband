from sqlalchemy.orm import Session

from src.user.models.user_model import User
from src.user.schemas.user_schema import UserProfileRequest


def get_profile(user: User) -> User:
    return user


def update_profile(db: Session, user: User, data: UserProfileRequest) -> None:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
