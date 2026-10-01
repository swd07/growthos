"""Meta ecosystem: Instagram, Facebook Page, Threads.

Own-account publishing works with the Meta app in Development mode
(add yourself as a tester); app review is only needed to connect other
people's accounts.

Env:
  META_GRAPH_VERSION          optional, e.g. v23.0 (empty = app default)
  INSTAGRAM_USER_ID           IG professional account id
  INSTAGRAM_ACCESS_TOKEN      long-lived token (Instagram Login or Facebook Login)
  INSTAGRAM_GRAPH_HOST        graph.instagram.com (Instagram Login, default)
                              or graph.facebook.com (Facebook Login)
  FACEBOOK_PAGE_ID, FACEBOOK_PAGE_TOKEN
  THREADS_USER_ID, THREADS_ACCESS_TOKEN
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

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


class _Graph:
    def __init__(self, host: str, token: str | None, version: str | None,
                 client: httpx.AsyncClient | None):
        self.host = host
        self.token = token
        self.version = version
        self._client = client

    def url(self, path: str) -> str:
        prefix = f"/{self.version}" if self.version else ""
        return f"https://{self.host}{prefix}/{path.lstrip('/')}"

    async def request(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        params["access_token"] = self.token
        client = self._client or httpx.AsyncClient(timeout=120)
        try:
            if method == "GET":
                r = await client.get(self.url(path), params=params)
            else:
                r = await client.post(self.url(path), data=params)
            data = r.json()
        finally:
            if self._client is None:
                await client.aclose()
        if r.status_code >= 400 or "error" in data:
            err = data.get("error", {})
            raise ProviderError(f"{self.host} {path}: {err.get('message', r.status_code)}")
        return data


async def _wait_container(graph: _Graph, container_id: str, field: str = "status_code",
                          attempts: int = 30, delay: float = 5.0) -> None:
    """Video containers must finish processing before publish."""
    for _ in range(attempts):
        data = await graph.request("GET", container_id, {"fields": field})
        status = data.get(field)
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise ProviderError(f"media container {container_id} ended with {status}")
        await asyncio.sleep(delay)
    raise ProviderError(f"media container {container_id} still processing; retry publish later")


class InstagramProvider(SocialProvider):
    name = "instagram"

    def __init__(self, client: httpx.AsyncClient | None = None, poll_delay: float = 5.0):
        self.user_id = os.getenv("INSTAGRAM_USER_ID")
        self.graph = _Graph(os.getenv("INSTAGRAM_GRAPH_HOST", "graph.instagram.com"),
                            os.getenv("INSTAGRAM_ACCESS_TOKEN"),
                            os.getenv("META_GRAPH_VERSION") or None, client)
        self.poll_delay = poll_delay

    def capabilities(self) -> Capabilities:
        return Capabilities(image=True, video=True, carousel=True, metrics=True,
                            max_text_len=2200, requires_media=True,
                            notes="Professional (Business/Creator) account only. Media must be a public URL. "
                                  "Video is published as a Reel. ~100 API posts per 24h.")

    def is_configured(self) -> bool:
        return bool(self.user_id and self.graph.token)

    async def _container(self, m, caption: str | None, carousel_item: bool = False) -> str:
        params: dict[str, Any] = {"caption": caption}
        if carousel_item:
            params["is_carousel_item"] = "true"
            params.pop("caption")
        if m.kind is MediaKind.IMAGE:
            params["image_url"] = m.url
            if m.alt_text:
                params["alt_text"] = m.alt_text
        else:
            params["media_type"] = "VIDEO" if carousel_item else "REELS"
            params["video_url"] = m.url
        data = await self.graph.request("POST", f"{self.user_id}/media", params)
        if m.kind is MediaKind.VIDEO:
            await _wait_container(self.graph, data["id"], delay=self.poll_delay)
        return data["id"]

    async def publish(self, draft: PostDraft) -> PublishResult:
        if not self.is_configured():
            raise NotConfiguredError("instagram: set INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN")
        caption = draft.text + (f"\n\n{draft.link}" if draft.link else "")
        if len(draft.media) == 1:
            creation_id = await self._container(draft.media[0], caption)
        else:
            children = [await self._container(m, None, carousel_item=True) for m in draft.media[:10]]
            data = await self.graph.request("POST", f"{self.user_id}/media", {
                "media_type": "CAROUSEL", "children": ",".join(children), "caption": caption})
            creation_id = data["id"]
        published = await self.graph.request("POST", f"{self.user_id}/media_publish",
                                             {"creation_id": creation_id})
        media_id = published["id"]
        info = await self.graph.request("GET", media_id, {"fields": "permalink"})
        return PublishResult(platform=self.name, status=PublishStatus.PUBLISHED,
                             post_id=media_id, url=info.get("permalink"), raw=published)

    async def get_metrics(self, post_id: str) -> dict[str, Any]:
        metrics = os.getenv("INSTAGRAM_METRICS", "reach,likes,comments,shares,saved")
        data = await self.graph.request("GET", f"{post_id}/insights", {"metric": metrics})
        return {row["name"]: row["values"][0]["value"] for row in data.get("data", [])}


class FacebookPageProvider(SocialProvider):
    name = "facebook"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.graph = _Graph("graph.facebook.com", os.getenv("FACEBOOK_PAGE_TOKEN"),
                            os.getenv("META_GRAPH_VERSION") or None, client)

    def capabilities(self) -> Capabilities:
        return Capabilities(image=True, video=True, carousel=False, metrics=False,
                            max_text_len=63206, notes="Posts to a Facebook Page, not a personal profile.")

    def is_configured(self) -> bool:
        return bool(self.page_id and self.graph.token)

    async def publish(self, draft: PostDraft) -> PublishResult:
        if not self.is_configured():
            raise NotConfiguredError("facebook: set FACEBOOK_PAGE_ID and FACEBOOK_PAGE_TOKEN")
        if not draft.media:
            data = await self.graph.request("POST", f"{self.page_id}/feed",
                                            {"message": draft.text, "link": draft.link})
            post_id = data["id"]
        elif draft.media[0].kind is MediaKind.IMAGE:
            data = await self.graph.request("POST", f"{self.page_id}/photos",
                                            {"url": draft.media[0].url, "caption": draft.text})
            post_id = data.get("post_id", data["id"])
        else:
            data = await self.graph.request("POST", f"{self.page_id}/videos",
                                            {"file_url": draft.media[0].url, "description": draft.text})
            post_id = data["id"]
        return PublishResult(platform=self.name, status=PublishStatus.PUBLISHED, post_id=post_id,
                             url=f"https://www.facebook.com/{post_id}", raw=data)


class ThreadsProvider(SocialProvider):
    name = "threads"

    def __init__(self, client: httpx.AsyncClient | None = None, poll_delay: float = 5.0):
        self.user_id = os.getenv("THREADS_USER_ID")
        self.graph = _Graph("graph.threads.net", os.getenv("THREADS_ACCESS_TOKEN"), "v1.0", client)
        self.poll_delay = poll_delay

    def capabilities(self) -> Capabilities:
        return Capabilities(image=True, video=True, carousel=False, metrics=False, max_text_len=500)

    def is_configured(self) -> bool:
        return bool(self.user_id and self.graph.token)

    async def publish(self, draft: PostDraft) -> PublishResult:
        if not self.is_configured():
            raise NotConfiguredError("threads: set THREADS_USER_ID and THREADS_ACCESS_TOKEN")
        params: dict[str, Any] = {"text": draft.text + (f"\n{draft.link}" if draft.link else "")}
        if not draft.media:
            params["media_type"] = "TEXT"
        elif draft.media[0].kind is MediaKind.IMAGE:
            params.update(media_type="IMAGE", image_url=draft.media[0].url)
        else:
            params.update(media_type="VIDEO", video_url=draft.media[0].url)
        container = await self.graph.request("POST", f"{self.user_id}/threads", params)
        if params["media_type"] == "VIDEO":
            await _wait_container(self.graph, container["id"], field="status", delay=self.poll_delay)
        data = await self.graph.request("POST", f"{self.user_id}/threads_publish",
                                        {"creation_id": container["id"]})
        info = await self.graph.request("GET", data["id"], {"fields": "permalink"})
        return PublishResult(platform=self.name, status=PublishStatus.PUBLISHED,
                             post_id=data["id"], url=info.get("permalink"), raw=data)
