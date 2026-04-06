import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from core.config import settings
from core.security import decode_token
from db.database import SessionLocal
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self._user_requests: Dict[int, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, user_id: int) -> Tuple[bool, int]:
        now = time.time()

        with self._lock:
            request_times = self._user_requests[user_id]
            while request_times and now - request_times[0] >= self.window_seconds:
                request_times.popleft()

            if len(request_times) >= self.requests_limit:
                retry_after = max(1, int(self.window_seconds - (now - request_times[0])))
                return False, retry_after

            request_times.append(now)
            return True, 0


ai_rate_limiter = RateLimiter(
    requests_limit=settings.ai_rate_limit_requests,
    window_seconds=settings.ai_rate_limit_window_seconds,
)


def check_rate_limit(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    is_allowed, retry_after = ai_rate_limiter.check(current_user.id)
    if not is_allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    return True
