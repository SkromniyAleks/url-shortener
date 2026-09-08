from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_cached_url, set_cached_url
from app.services import link_service

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
async def redirect(short_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Проверяем кэш
    cached_url = await get_cached_url(short_code)

    if cached_url:
        # Если есть в кэше — всё равно пишем клик
        link = await link_service.get_link_by_code(db, short_code)
        if link:
            await link_service.record_click(
                db,
                link,
                ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", ""),
                referer=request.headers.get("referer", ""),
            )
        return RedirectResponse(url=cached_url)

    # 2. Если нет в кэше — идём в БД
    link = await link_service.get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # 3. Записываем в кэш
    await set_cached_url(short_code, link.original_url)

    # 4. Логируем клик
    await link_service.record_click(
        db,
        link,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        referer=request.headers.get("referer", ""),
    )

    return RedirectResponse(url=link.original_url)