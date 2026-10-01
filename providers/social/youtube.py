"""YouTube uploads via Data API v3 (resumable upload).

Important: Google Cloud projects created after 28 July 2020 that have not
passed the YouTube API compliance audit can only upload PRIVATE videos,
whatever privacyStatus you send. Submit the "YouTube API Services Audit and
Quota Extension Form" early; set YOUTUBE_PROJECT_AUDITED=1 once approved.

Env:
  YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
  (OAuth client of type "Desktop app", scope youtube.upload)
  YOUTUBE_PROJECT_AUDITED   "1" after the audit is approved
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

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


class YouTubeProvider(SocialProvider):
    name = "youtube"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.audited = os.getenv("YOUTUBE_PROJECT_AUDITED") == "1"
        self._client = client

    def capabilities(self) -> Capabilities:
        return Capabilities(text=False, image=False, video=True, metrics=False, requires_media=True,
                            max_text_len=5000,
                            notes="Needs draft.title. Unaudited projects: uploads are forced private.")

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def validate(self, draft: PostDraft) -> list[str]:
        problems = super().validate(draft)
        if not draft.title:
            problems.append("youtube needs a title")
        elif len(draft.title) > 100:
            problems.append("youtube title is longer than 100 chars")
        return problems

    async def publish(self, draft: PostDraft) -> PublishResult:
        if not self.is_configured():
            raise NotConfiguredError("youtube: set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
        video = next((m for m in draft.media if m.kind is MediaKind.VIDEO), None)
        if video is None:
            raise ProviderError("youtube: a video is required")
        client = self._client or httpx.AsyncClient(timeout=600)
        try:
            tok = (await client.post(TOKEN_URL, data={
                "client_id": self.client_id, "client_secret": self.client_secret,
                "refresh_token": self.refresh_token, "grant_type": "refresh_token"})).json()
            if "access_token" not in tok:
                raise ProviderError(f"youtube token refresh failed: {tok}")
            auth = {"Authorization": f"Bearer {tok['access_token']}"}
            body = (await client.get(video.url, follow_redirects=True)).content
            privacy = draft.extra.get("privacy", "public")
            meta = {
                "snippet": {"title": draft.title, "description": draft.text,
                            "tags": draft.extra.get("tags", []),
                            "categoryId": str(draft.extra.get("category_id", "28"))},
                "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
            }
            init = await client.post(UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"},
                                     headers={**auth, "X-Upload-Content-Type": "video/*",
                                              "X-Upload-Content-Length": str(len(body))},
                                     json=meta)
            if init.status_code >= 400:
                raise ProviderError(f"youtube init: {init.status_code} {init.text}")
            up = await client.put(init.headers["Location"], headers={**auth, "Content-Type": "video/*"},
                                  content=body)
            data = up.json()
        finally:
            if self._client is None:
                await client.aclose()
        if up.status_code >= 400:
            raise ProviderError(f"youtube upload: {up.status_code} {data}")
        vid = data["id"]
        forced_private = not self.audited and privacy != "private"
        return PublishResult(
            platform=self.name,
            status=PublishStatus.PRIVATE_ONLY if forced_private else PublishStatus.PUBLISHED,
            post_id=vid, url=f"https://youtu.be/{vid}", raw=data,
            detail="Project not audited: YouTube keeps this video private." if forced_private else None)
