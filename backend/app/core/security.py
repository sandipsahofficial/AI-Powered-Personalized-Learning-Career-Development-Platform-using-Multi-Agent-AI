import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.db.redis import redis_manager

# Password hashing context using Argon2id
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)

security_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secure_token(nbytes: int = 48) -> str:
    return secrets.token_urlsafe(nbytes)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Embed jti (JWT ID) for Redis revocation capability
    jti = secrets.token_hex(16)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def revoke_token_jti(jti: str, ttl_seconds: int = 1800) -> bool:
    try:
        client = redis_manager.get_client()
        key = f"token_blacklist:{jti}"
        await client.set(key, "revoked", ex=ttl_seconds)
        return True
    except Exception:
        # Fallback if Redis is unavailable: log and return
        return False


async def is_token_jti_revoked(jti: str) -> bool:
    try:
        client = redis_manager.get_client()
        key = f"token_blacklist:{jti}"
        val = await client.get(key)
        return val is not None
    except Exception:
        return False


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    jti = payload.get("jti")
    if jti and await is_token_jti_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query user from DB
    from app.models.user import User
    import uuid
    user_id = uuid.UUID(user_id_str)
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user = Depends(get_current_user)):
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role not in allowed_roles and user_role != "SYS_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
