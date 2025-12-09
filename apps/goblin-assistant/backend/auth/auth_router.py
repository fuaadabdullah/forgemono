from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt

from database import get_db
from auth_service import JWTAuthService
from auth.secrets_manager import get_secrets_manager
from models_base import User
from auth.policies import UserRole

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class RegisterResponse(BaseModel):
    message: str
    user_id: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_auth_service() -> JWTAuthService:
    """Dependency to get JWT auth service instance."""
    secrets_manager = get_secrets_manager()
    jwt_secret = secrets_manager.get_secret("JWT_SECRET_KEY")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable",
        )
    return JWTAuthService(jwt_secret)


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Hash the password
    password_hash = hash_password(request.password)

    # Create new user
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        name=request.name,
        role=UserRole.USER.value,  # Default role
        token_version=0,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RegisterResponse(
        message="User registered successfully", user_id=str(new_user.id)
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: JWTAuthService = Depends(get_auth_service),
):
    """Authenticate user and return JWT tokens."""
    # Look up user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Verify password
    if not user.password_hash or not verify_password(
        request.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Create tokens
    access_token = auth_service.create_access_token(
        user.id, user.email, UserRole(user.role)
    )
    refresh_token = auth_service.create_refresh_token(user.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900,  # 15 minutes
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db),
    auth_service: JWTAuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    access_token = auth_service.refresh_access_token(request.refresh_token, db)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return RefreshResponse(
        access_token=access_token,
        expires_in=900,  # 15 minutes
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: JWTAuthService = Depends(get_auth_service),
):
    """Logout user (client should discard tokens)."""
    # In a stateless JWT system, logout is handled client-side
    # For enhanced security, you could implement token blacklisting
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: JWTAuthService = Depends(get_auth_service),
):
    """Get current user information."""
    payload = auth_service.validate_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }
