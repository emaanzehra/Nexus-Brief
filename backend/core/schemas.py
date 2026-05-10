"""
NexusBrief — Pydantic Schemas
==============================
Request bodies and response shapes for every endpoint.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


# ─── Category ────────────────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    id:            int
    name:          str
    slug:          str
    icon:          str
    color:         str
    dot_color:     str
    description:   Optional[str]
    article_count: int = 0

    model_config = {"from_attributes": True}


# ─── Article ──────────────────────────────────────────────────────────────────

class CategoryBrief(BaseModel):
    id:        int
    name:      str
    slug:      str
    icon:      str
    dot_color: str

    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id:                  int
    title:               str
    slug:                str
    ai_summary:          str
    key_points:          List[str]
    source_url:          str
    source_name:         Optional[str]
    author:              Optional[str]
    image_url:           Optional[str]
    sentiment:           str
    sentiment_color:     str
    reading_time:        int
    reading_time_label:  str
    is_featured:         bool
    time_ago:            str
    published_at:        Optional[datetime]
    category:            Optional[CategoryBrief]
    created_at:          datetime

    model_config = {"from_attributes": True}


class ArticleListOut(BaseModel):
    items:      List[ArticleOut]
    total:      int
    page:       int
    per_page:   int
    pages:      int


# ─── Stats ────────────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    total_articles:    int
    today_articles:    int
    positive_articles: int
    negative_articles: int
    neutral_articles:  int
    total_categories:  int
    total_sources:     int
    last_updated:      Optional[datetime]


# ─── Auth ─────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    first_name: str
    last_name:  str
    email:      EmailStr
    password:   str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_name:    str
    user_email:   str
    plan:         str


# ─── Contact ─────────────────────────────────────────────────────────────────

class ContactRequest(BaseModel):
    name:       str
    email:      EmailStr
    department: str
    subject:    str
    message:    str

    @field_validator("message")
    @classmethod
    def message_length(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v
