import secrets
import string

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Click, Link
from app.schemas import LinkCreate


def generate_short_code(length: int = settings.SHORT_CODE_LENGTH) -> str:
    """Генерирует случайный короткий код (62^6 ≈ 56 млрд комбинаций)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def create_link(db: AsyncSession, data: LinkCreate) -> Link:
    """Создаёт ссылку с уникальным коротким кодом."""
    while True:
        short_code = generate_short_code()
        existing = await db.execute(select(Link).where(Link.short_code == short_code))
        if existing.scalar_one_or_none() is None:
            break

    link = Link(
        short_code=short_code,
        original_url=str(data.original_url),
        expires_at=data.expires_at,
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


async def record_click(db: AsyncSession, link: Link, ip: str, user_agent: str, referer: str) -> None:
    """Записывает клик и увеличивает счётчик."""
    click = Click(link_id=link.id, ip_address=ip, user_agent=user_agent, referer=referer)
    db.add(click)
    link.click_count += 1
    await db.commit()


async def get_total_clicks(db: AsyncSession, link_id: int) -> int:
    result = await db.execute(select(func.count(Click.id)).where(Click.link_id == link_id))
    return result.scalar() or 0