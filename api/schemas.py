"""Pydantic models for API request/response validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    name: str = ""


class AuthResponse(BaseModel):
    token: str
    email: str
    name: str = ""
    user_id: int


class UserInfo(BaseModel):
    user_id: int
    email: str
    name: str = ""


# ── Chat ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: int | None = None
    lang: str = "en"


class SessionSummary(BaseModel):
    id: int
    title: str
    agent_slug: str | None = None
    updated_at: str


class MessageOut(BaseModel):
    role: str
    content: str
    agent_slug: str | None = None


class SessionDetail(BaseModel):
    id: int
    title: str
    agent_slug: str | None = None
    messages: list[MessageOut]


class ShareResponse(BaseModel):
    token: str
    url: str


class SharedSessionOut(BaseModel):
    title: str
    agent_slug: str | None = None
    messages: list[MessageOut]


# ── Agents ────────────────────────────────────────────────────────────

class AgentOut(BaseModel):
    slug: str
    name: str
    category: str
    icon: str
    one_liner: str
    prefix: str
    example_prompts: list[str]


# ── Profile ───────────────────────────────────────────────────────────

class UserProfileOut(BaseModel):
    name: str = ""
    email: str
    phone: str = ""
    country: str = ""
    city: str = ""
    currency: str = "EUR"
    language: str = "en"
    notify_new_listings: bool = True
    notify_weekly_digest: bool = True


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    currency: str | None = None
    language: str | None = None
    notify_new_listings: bool | None = None
    notify_weekly_digest: bool | None = None


# ── Contact ───────────────────────────────────────────────────────────

class ContactRequest(BaseModel):
    name: str
    email: str
    message: str
