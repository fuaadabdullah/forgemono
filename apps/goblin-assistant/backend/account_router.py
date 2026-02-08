from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, AccountPreference
from .auth_service import get_auth_service, JWTAuthService

router = APIRouter(prefix="/account", tags=["account"])
security = HTTPBearer()


class ProfileRequest(BaseModel):
    name: str


class PreferencesRequest(BaseModel):
    summaries: bool
    notifications: bool
    familyMode: bool


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: JWTAuthService = Depends(get_auth_service),
) -> User:
    claims = auth_service.validate_access_token(credentials.credentials)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = claims.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/profile")
async def save_profile(
    request: ProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    current_user.name = request.name.strip()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"status": "ok", "name": current_user.name}


@router.post("/preferences")
async def save_preferences(
    request: PreferencesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preferences = (
        db.query(AccountPreference)
        .filter(AccountPreference.user_id == current_user.id)
        .first()
    )

    if not preferences:
        preferences = AccountPreference(
            user_id=current_user.id,
            summaries=request.summaries,
            notifications=request.notifications,
            family_mode=request.familyMode,
        )
        db.add(preferences)
    else:
        preferences.summaries = request.summaries
        preferences.notifications = request.notifications
        preferences.family_mode = request.familyMode
        db.add(preferences)

    db.commit()
    db.refresh(preferences)

    return {
        "status": "ok",
        "preferences": {
            "summaries": preferences.summaries,
            "notifications": preferences.notifications,
            "familyMode": preferences.family_mode,
        },
    }
