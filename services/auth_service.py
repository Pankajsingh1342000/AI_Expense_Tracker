from sqlalchemy.orm import Session
from models.user import User
from core.security import hash_password, verify_password

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str) -> User:
    # First, check if a user with this email already exists
    db_user = get_user_by_email(db, email)
    if db_user:
        # If they exist, we do not proceed. We will handle this in the API layer.
        return None 
    
    # If they don't exist, create the new user
    hashed_password = hash_password(password)
    new_user = User(email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user