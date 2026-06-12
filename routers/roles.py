"""Role HTTP endpoints — CRUD with live user count."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.user import User
from schemas.role import RoleCreate, RoleUpdate, RoleOut
from crud import roles as crud_roles
from models.role import Role

router = APIRouter(prefix="/api/roles", tags=["roles"])


def _to_out(role: Role, user_counts: dict) -> dict:
    """Attach computed assigned_users count to a Role row."""
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "access_level": role.access_level,
        "permissions_count": role.permissions_count,
        "status": role.status,
        "assigned_users": user_counts.get(role.name.lower(), 0),
        "created_at": role.created_at,
    }


@router.get("", response_model=List[RoleOut], summary="List all roles (with user counts)")
async def list_roles(db: AsyncSession = Depends(get_db)):
    roles = await crud_roles.get_all(db)
    counts = await crud_roles.count_users_per_role(db)
    return [_to_out(r, counts) for r in roles]


@router.get("/{role_id}", response_model=RoleOut, summary="Get one role")
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await crud_roles.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    counts = await crud_roles.count_users_per_role(db)
    return _to_out(role, counts)


@router.post(
    "",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a role",
)
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    if await crud_roles.get_by_name(db, payload.name):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Role '{payload.name}' already exists.",
        )
    role = await crud_roles.create(db, payload)
    counts = await crud_roles.count_users_per_role(db)
    return _to_out(role, counts)


@router.patch("/{role_id}", response_model=RoleOut, summary="Update a role")
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    role = await crud_roles.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    if payload.name is not None and payload.name != role.name:
        if await crud_roles.get_by_name(db, payload.name):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Role '{payload.name}' already exists.",
            )
    role = await crud_roles.update(db, role, payload)
    counts = await crud_roles.count_users_per_role(db)
    return _to_out(role, counts)


@router.post(
    "/{role_id}/deactivate",
    response_model=RoleOut,
    summary="Deactivate a role (soft delete)",
)
async def deactivate_role(role_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    role = await crud_roles.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    role = await crud_roles.soft_delete(db, role)
    counts = await crud_roles.count_users_per_role(db)
    return _to_out(role, counts)


@router.post(
    "/{role_id}/restore",
    response_model=RoleOut,
    summary="Restore an inactive role",
)
async def restore_role(role_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    role = await crud_roles.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    role = await crud_roles.restore(db, role)
    counts = await crud_roles.count_users_per_role(db)
    return _to_out(role, counts)