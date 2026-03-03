from sqlalchemy.orm import Session
from models.user import User
from core.security import hash_password, verify_password

def create_user(db: Session, email: str, password: str):
    user = User(email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user