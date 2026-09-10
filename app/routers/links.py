from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_admin, get_current_user
from app.models import Link, User
from app.redis_client import clear_cache, delete_cached_url
from app.schemas import ClickResponse, LinkCreate, LinkResponse, LinkStats
from app.services import link_service

router = APIRouter(tags=["links"])


def _to_response(link: Link, owner_username: str | None = None) -> LinkResponse:
    return LinkResponse(
        id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        created_at=link.created_at,
        click_count=link.click_count,
        owner_id=link.owner_id,
        owner_username=owner_username,
    )


def _check_access(link: Link, user: User) -> None:
    """Ссылка доступна только её владельцу или админу."""
    if link.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Only owner or admin can access this link")


@router.post("", response_model=LinkResponse, status_code=201)
async def create_link(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Создание ссылки — только для авторизованных."""
    link = await link_service.create_link(db, data, owner_id=user.id)
    return _to_response(link, owner_username=user.username)


@router.get("", response_model=list[LinkResponse])
async def list_links(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Пользователь видит свои ссылки, админ — все."""
    links = await link_service.get_links(db, user)
    return [
        _to_response(link, owner_username=link.owner.username if link.owner else None)
        for link in links
    ]


@router.get("/{link_id}/stats", response_model=LinkStats)
async def get_stats(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await link_service.get_link_by_id(db, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    _check_access(link, user)
    total = await link_service.count_clicks(db, link_id)
    return LinkStats(
        id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        click_count=link.click_count,
        total_clicks=total,
        created_at=link.created_at,
    )


@router.get("/{link_id}/clicks", response_model=list[ClickResponse])
async def list_clicks(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await link_service.get_link_by_id(db, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    _check_access(link, user)
    clicks = await link_service.get_clicks(db, link_id)
    return [ClickResponse.model_validate(click) for click in clicks]


@router.delete("/{link_id}", status_code=204)
async def delete_link(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    link = await link_service.get_link_by_id(db, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    _check_access(link, user)
    await link_service.delete_link(db, link)
    await delete_cached_url(link.short_code)  # редирект не должен жить из кэша
    return Response(status_code=204)


@router.delete("", status_code=204)
async def delete_all_links(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_admin),
):
    """Полная очистка БД: только админ."""
    await link_service.delete_all_links(db)
    await clear_cache()
    return Response(status_code=204)