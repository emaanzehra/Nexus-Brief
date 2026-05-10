"""
NexusBrief — Auth utilities
============================
Simple JWT-based authentication helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import hashlib
import bcrypt
from core.config import settings

# Passwords are SHA-256 pre-hashed before bcrypt to avoid
# bcrypt's 72-byte truncation limit. Both hash and verify
# must use this same pipeline — do not change one without the other.
def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    pwd_hash = hashlib.sha256(pwd_bytes).hexdigest().encode('ascii')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_hash, salt).decode('ascii')

def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode('utf-8')
    pwd_hash = hashlib.sha256(pwd_bytes).hexdigest().encode('ascii')
    hashed_bytes = hashed.encode('ascii')
    try:
        return bcrypt.checkpw(pwd_hash, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
