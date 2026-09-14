import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), _ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$")
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), _ITERATIONS
    ).hex()
    return hmac.compare_digest(candidate, digest)


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None