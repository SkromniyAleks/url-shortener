from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.redis_client import set_cached_url
from app.schemas import LinkCreate, LinkResponse, LinkStats
from app.services import link_service

router = APIRouter(prefix="/api/v1/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=201)
async def create_link(data: LinkCreate, db: AsyncSession = Depends(get_db)):
    """Создать короткую ссылку."""
    link = await link_service.create_link(db, data)
    await set_cached_url(link.short_code, link.original_url)
    return LinkResponse(
        id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        created_at=link.created_at,
        click_count=link.click_count,
    )


@router.get("/{link_id}/stats", response_model=LinkStats)
async def get_stats(link_id: int, db: AsyncSession = Depends(get_db)):
    """Получить аналитику по ссылке."""
    link = await link_service.get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    total_clicks = await link_service.get_total_clicks(db, link_id)
    return LinkStats(
        id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        click_count=link.click_count,
        total_clicks=total_clicks,
        created_at=link.created_at,
    )