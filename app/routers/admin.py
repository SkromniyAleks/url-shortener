from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin
from app.models import User
from app.schemas import AdminUserResponse, PasswordReset, RoleUpdate
from app.services import user_service

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin),
):
    """Список всех пользователей: только для админа."""
    return await user_service.get_users(db)


@router.post("/users/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: int,
    data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin),
):
    """Админ задаёт пользователю новый пароль."""
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.reset_password(db, user, data.new_password)
    return Response(status_code=204)


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def update_role(
    user_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin),
):
    """Повысить/понизить роль; себя разжаловать нельзя."""
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id and not data.is_admin:
        raise HTTPException(status_code=409, detail="Cannot remove your own admin rights")
    await user_service.set_role(db, user, data.is_admin)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin),
):
    """Удалить пользователя; себя удалить нельзя."""
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=409, detail="Cannot delete your own account")
    await user_service.delete_user(db, user)
    return Response(status_code=204)