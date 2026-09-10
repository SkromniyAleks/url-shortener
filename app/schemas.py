from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LinkCreate(BaseModel):
    original_url: HttpUrl


class LinkResponse(BaseModel):
    id: int
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    click_count: int
    owner_id: int | None = None
    owner_username: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LinkStats(BaseModel):
    id: int
    short_code: str
    original_url: str
    click_count: int
    total_clicks: int
    created_at: datetime


class ClickResponse(BaseModel):
    id: int
    link_id: int
    clicked_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    referer: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PasswordReset(BaseModel):
    new_password: str = Field(min_length=6, max_length=72)


class RoleUpdate(BaseModel):
    is_admin: bool


class AdminUserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)