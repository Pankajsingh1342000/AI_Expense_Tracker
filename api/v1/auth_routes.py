from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from api.deps import get_db
from core.security import create_access_token, create_refresh_token, validate_refresh_token
from schemas.user import RefreshTokenRequest, TokenResponse, UserCreate
from services.auth_service import authenticate_user, create_user

router = APIRouter()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user.email, user.password)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"message": "User registered successfully", "email": db_user.email}


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    subject = {"sub": str(user.id)}
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest):
    try:
        decoded = validate_refresh_token(payload.refresh_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    subject = {"sub": str(decoded["sub"])}
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
