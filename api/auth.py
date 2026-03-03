from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from schemas.user import UserCreate
from services.auth_service import create_user, authenticate_user
from api.deps import get_db
from core.security import create_access_token

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user.email, user.password)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    return {"access_token": token, "token_type": "bearer"}