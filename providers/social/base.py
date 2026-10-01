"""Common contract for every social network adapter.

GrowthOS rule: generate != publish. Adapters only publish what they are given;
the approval decision lives above them (MCP server / approvals module).
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MediaKind(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class MediaItem(BaseModel):
    kind: MediaKind
    # Public HTTPS URL. Meta, Threads and Telegram fetch media by URL;
    # adapters that need bytes (X, YouTube, TikTok) download it themselves.
    url: str
    alt_text: str | None = None


class PostDraft(BaseModel):
    """Platform-neutral post. Platform-specific fields go to `extra`."""

    text: str = ""
    media: list[MediaItem] = Field(default_factory=list)
    link: str | None = None
    title: str | None = None  # YouTube title, Reddit title
    target: str | None = None  # Reddit subreddit, Telegram chat override, etc.
    extra: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class PublishStatus(str, enum.Enum):
    PUBLISHED = "published"
    PROCESSING = "processing"  # accepted, platform still processing media
    PRIVATE_ONLY = "private_only"  # unaudited app: platform forced private visibility
    MANUAL_REQUIRED = "manual_required"  # e.g. Reddit before API approval
    DRY_RUN = "dry_run"
    FAILED = "failed"


class PublishResult(BaseModel):
    platform: str
    status: PublishStatus
    post_id: str | None = None
    url: str | None = None
    detail: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime | None = None


class Capabilities(BaseModel):
    text: bool = True
    image: bool = False
    video: bool = False
    carousel: bool = False
    metrics: bool = False
    max_text_len: int | None = None
    requires_media: bool = False
    notes: str = ""


class ProviderError(Exception):
    """Platform rejected the request or returned an unexpected payload."""


class NotConfiguredError(ProviderError):
    """Credentials for the platform are missing."""


class SocialProvider(ABC):
    name: str = "base"

    @abstractmethod
    def capabilities(self) -> Capabilities: ...

    @abstractmethod
    def is_configured(self) -> bool: ...

    def validate(self, draft: PostDraft) -> list[str]:
        """Return a list of human-readable problems; empty list means OK."""
        caps = self.capabilities()
        problems: list[str] = []
        if caps.max_text_len and len(draft.text) > caps.max_text_len:
            problems.append(f"text is {len(draft.text)} chars, limit is {caps.max_text_len}")
        if caps.requires_media and not draft.media:
            problems.append("this platform requires an image or video")
        for m in draft.media:
            if m.kind is MediaKind.IMAGE and not caps.image:
                problems.append("images are not supported by this adapter yet")
            if m.kind is MediaKind.VIDEO and not caps.video:
                problems.append("video is not supported by this adapter yet")
        if len(draft.media) > 1 and not caps.carousel:
            problems.append("multiple media items are not supported by this adapter yet")
        return problems

    @abstractmethod
    async def publish(self, draft: PostDraft) -> PublishResult: ...

    async def get_metrics(self, post_id: str) -> dict[str, Any]:
        raise ProviderError(f"{self.name}: metrics are not implemented yet")

    async def delete(self, post_id: str) -> None:
        raise ProviderError(f"{self.name}: delete is not implemented yet")
