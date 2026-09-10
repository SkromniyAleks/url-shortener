from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Link, User
from app.security import hash_password


async def ensure_admin(db: AsyncSession) -> None:
    """Создаёт администратора при первом старте, если его ещё нет."""
    result = await db.execute(
        select(User).where(User.username == settings.ADMIN_USERNAME)
    )
    if result.scalar_one_or_none() is None:
        db.add(
            User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            )
        )
        await db.commit()


async def get_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def reset_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    await db.commit()


async def set_role(db: AsyncSession, user: User, is_admin: bool) -> None:
    user.is_admin = is_admin
    await db.commit()


async def delete_user(db: AsyncSession, user: User) -> None:
    """Удаляет пользователя; его ссылки остаются, но становятся без владельца."""
    await db.execute(
        update(Link).where(Link.owner_id == user.id).values(owner_id=None)
    )
    await db.delete(user)
    await db.commit()