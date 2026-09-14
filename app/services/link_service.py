import random
import string

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Click, Link, User
from app.schemas import LinkCreate


def generate_short_code() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=settings.SHORT_CODE_LENGTH))


async def create_link(
    db: AsyncSession, data: LinkCreate, owner_id: int | None = None
) -> Link:
    code = generate_short_code()
    for _ in range(5):
        existing = await db.execute(select(Link).where(Link.short_code == code))
        if existing.scalar_one_or_none() is None:
            break
        code = generate_short_code()

    link = Link(
        short_code=code,
        original_url=str(data.original_url),
        owner_id=owner_id,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def get_link_by_code(db: AsyncSession, short_code: str) -> Link | None:
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    return result.scalar_one_or_none()


async def get_link_by_id(db: AsyncSession, link_id: int) -> Link | None:
    result = await db.execute(select(Link).where(Link.id == link_id))
    return result.scalar_one_or_none()


async def get_links(db: AsyncSession, user: User) -> list[Link]:
    query = select(Link).options(selectinload(Link.owner))
    if not user.is_admin:
        query = query.where(Link.owner_id == user.id)
    result = await db.execute(query.order_by(Link.id.desc()))
    return list(result.scalars().all())


async def get_clicks(db: AsyncSession, link_id: int) -> list[Click]:
    result = await db.execute(
        select(Click)
        .where(Click.link_id == link_id)
        .order_by(Click.clicked_at.desc())
    )
    return list(result.scalars().all())


async def count_clicks(db: AsyncSession, link_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(Click).where(Click.link_id == link_id)
    )
    return result.scalar_one()


async def record_click(
    db: AsyncSession,
    link: Link,
    ip: str,
    user_agent: str,
    referer: str,
) -> None:
    click = Click(
        link_id=link.id,
        ip_address=ip,
        user_agent=user_agent,
        referer=referer,
    )
    db.add(click)
    link.click_count += 1
    await db.commit()


async def delete_link(db: AsyncSession, link: Link) -> None:
    """Удаляет ссылку вместе с кликами (каскад на уровне приложения)."""
    await db.execute(delete(Click).where(Click.link_id == link.id))
    await db.delete(link)
    await db.commit()


async def delete_all_links(db: AsyncSession) -> int:
    """Полная очистка: все клики, затем все ссылки. Возвращает число удалённых ссылок."""
    total = (
        await db.execute(select(func.count()).select_from(Link))
    ).scalar_one()
    await db.execute(delete(Click))
    await db.execute(delete(Link))
    await db.commit()
    return total