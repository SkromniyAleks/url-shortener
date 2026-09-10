from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, get_db
from app.routers import admin, auth, links, redirect
from app.services import user_service


STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async for db in get_db():
        await user_service.ensure_admin(db)
    yield


app = FastAPI(title="URL Shortener", version="1.2.0", lifespan=lifespan)


# Фикс-пути строго ДО шаблонного /{short_code},
# иначе редирект-роутер перехватит /health
@app.get("/health", tags=["service"])
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(links.router, prefix="/api/v1/links")
app.include_router(redirect.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")