"""Pydantic contracts for knowledge APIs."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ArticleType = Literal["SOP", "TROUBLESHOOTING", "FAQ", "BEST_PRACTICE"]
ArticleStatus = Literal["DRAFT", "UNDER_REVIEW", "PUBLISHED", "ARCHIVED"]


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    type: ArticleType
    tags: list[str] | None = None


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    type: ArticleType | None = None
    tags: list[str] | None = None


class ObjectLinks(BaseModel):
    objects: list[UUID] = Field(min_length=1)
    relation_reason: str | None = Field(default=None, max_length=255)
