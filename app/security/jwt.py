import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.exceptions import RAGXException

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise RAGXException(code="TOKEN_EXPIRED", message="Token has expired", status_code=401)
    except jwt.InvalidTokenError:
        raise RAGXException(code="TOKEN_INVALID", message="Invalid token", status_code=401)
