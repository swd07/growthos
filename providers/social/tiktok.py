"""TikTok via Content Posting API.

Unaudited apps can only Direct Post with SELF_ONLY visibility, the account
must be private, max 5 users per 24h. Upload-to-inbox (the creator finishes
the post in the TikTok app) needs no audit, so it is the default here.

This adapter uses PULL_FROM_URL, which requires the media domain to be
verified in the TikTok developer portal.

Env:
  TIKTOK_ACCESS_TOKEN   user token with video.upload (inbox) or video.publish (direct)
  TIKTOK_MODE           "inbox" (default) or "direct" (only after audit)
"""

from __future__ import annotations

import os

import httpx

from .base import (
    Capabilities,
    MediaKind,
    NotConfiguredError,
    PostDraft,
    ProviderError,
    PublishResult,
    PublishStatus,
    SocialProvider,
)

API = "https://open.tiktokapis.com/v2"


class TikTokProvider(SocialProvider):
    name = "tiktok"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.token = os.getenv("TIKTOK_ACCESS_TOKEN")
        self.mode = os.getenv("TIKTOK_MODE", "inbox")
        self._client = client

    def capabilities(self) -> Capabilities:
        return Capabilities(text=False, video=True, requires_media=True, max_text_len=2200,
                            notes="Default: sends the video to your TikTok inbox as a draft. "
                                  "Direct public posting requires passing TikTok's audit.")

    def is_configured(self) -> bool:
        return bool(self.token)

    async def publish(self, draft: PostDraft) -> PublishResult:
        if not self.is_configured():
            raise NotConfiguredError("tiktok: set TIKTOK_ACCESS_TOKEN")
        video = next((m for m in draft.media if m.kind is MediaKind.VIDEO), None)
        if video is None:
            raise ProviderError("tiktok: a video is required")
        source = {"source": "PULL_FROM_URL", "video_url": video.url}
        if self.mode == "direct":
            path = "post/publish/video/init/"
            body = {"post_info": {"title": draft.text[:2200],
                                  "privacy_level": draft.extra.get("privacy_level", "SELF_ONLY")},
                    "source_info": source}
        else:
            path = "post/publish/inbox/video/init/"
            body = {"source_info": source}
        client = self._client or httpx.AsyncClient(timeout=60)
        try:
            r = await client.post(f"{API}/{path}", json=body,
                                  headers={"Authorization": f"Bearer {self.token}",
                                           "Content-Type": "application/json; charset=UTF-8"})
            data = r.json()
        finally:
            if self._client is None:
                await client.aclose()
        err = data.get("error", {})
        if r.status_code >= 400 or err.get("code") not in (None, "ok"):
            raise ProviderError(f"tiktok {path}: {err}")
        publish_id = data["data"]["publish_id"]
        if self.mode == "direct":
            status, detail = PublishStatus.PROCESSING, "Poll status; unaudited apps post SELF_ONLY."
        else:
            status, detail = PublishStatus.MANUAL_REQUIRED, "Video sent to TikTok inbox: finish posting in the app."
        return PublishResult(platform=self.name, status=status, post_id=publish_id, detail=detail, raw=data)
