from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserCreate
# --- CHANGE IS HERE ---
from services.auth_service import create_user, authenticate_user
from api.deps import get_db # Make sure deps is imported correctly
from core.security import create_access_token

router = APIRouter()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # --- CHANGE IS HERE ---
    db_user = create_user(db, user.email, user.password)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    # If successful, we can just return the user object (without password)
    # or a success message. Let's return a message.
    return {"message": "User registered successfully", "email": db_user.email}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(user.id)})

    return {"access_token": token, "token_type": "bearer"}