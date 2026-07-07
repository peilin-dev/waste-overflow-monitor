"""Authentication endpoints — login and current user."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import (
    verify_password,
    hash_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from core.deps import get_current_user
from crud import users as crud_users
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest
from schemas.user import UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login (admin or cleaner)",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Find user by username
    user = await crud_users.get_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # 2. Verify password (compare with hashed)
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # 3. Check account status
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # 4. Update last_seen timestamp
    user.last_seen = datetime.now()
    await db.commit()

    # 5. Generate JWT token
    token = create_access_token(
        data={
            "sub": str(user.id),    # 'sub' is JWT standard for "subject" (user ID)
            "role": user.role,
            "username": user.username,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/token",
    include_in_schema=False,  # Hidden from API docs — used only by Swagger UI's Authorize button
)
async def oauth2_token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Standard OAuth2 password flow endpoint for Swagger UI compatibility."""
    user = await crud_users.get_by_username(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    user.last_seen = datetime.now()
    await db.commit()
    token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "username": user.username}
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current logged-in user's info",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return info about the user identified by the JWT token."""
    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = hash_password(payload.new_password)
    await db.commit()