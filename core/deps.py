"""
FastAPI dependencies for authentication & authorization.

Usage in endpoints:
    @router.get("/something")
    async def func(current_user: User = Depends(get_current_user)):
        ...
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import decode_token
from crud import users as crud_users
from models.user import User


# OAuth2 scheme — auto-reads "Authorization: Bearer <token>" header
# tokenUrl points to the standard OAuth2 form endpoint used by Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the JWT token and return the current user.
    Raise 401 if token is invalid/expired or user is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await crud_users.get_by_id(db, int(user_id))
    if user is None or user.status != "active":
        raise credentials_exception

    return user


async def verify_sensor_key(x_sensor_key: Optional[str] = Header(None)) -> None:
    """
    Validates X-Sensor-Key header for IoT sensor endpoints.
    Only enforced when SENSOR_API_KEY is configured in settings.
    """
    if settings.SENSOR_API_KEY is None:
        return  # Not configured — open access (dev mode)
    if x_sensor_key != settings.SENSOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing sensor key",
        )


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user