from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class LinkCreate(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None


class LinkResponse(BaseModel):
    id: int
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    click_count: int

    model_config = ConfigDict(from_attributes=True)


class LinkStats(BaseModel):
    id: int
    short_code: str
    original_url: str
    click_count: int
    total_clicks: int
    created_at: datetime