"""X (Twitter) via API v2 with an OAuth 2.0 user-context token.

Billing (2026): pay-per-use, no free tier for new developers. A post costs
about $0.015, a post containing a link about $0.20. Prefer links in replies
or skip links on X.

Env:
  X_CLIENT_ID          OAuth 2.0 client id (public client, PKCE)
  X_REFRESH_TOKEN      initial refresh token (scopes: tweet.read tweet.write users.read offline.access)
  X_TOKEN_FILE         where rotated tokens are stored (default ~/.growthos/x_token.json)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

from .base import (
    Capabilities,
    NotConfiguredError,
    PostDraft,
    ProviderError,
    PublishResult,
    PublishStatus,
    SocialProvider,
)

API = "https://api.x.com/2"


class XProvider(SocialProvider):
    name = "x"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client_id = os.getenv("X_CLIENT_ID")
        self.token_file = Path(os.getenv("X_TOKEN_FILE", "~/.growthos/x_token.json")).expanduser()
        self._client = client

    def capabilities(self) -> Capabilities:
        return Capabilities(image=False, video=False, metrics=True, max_text_len=280,
                            notes="Text posts only for now (media upload not implemented). "
                                  "Pay-per-use: links make a post ~13x more expensive.")

    def _stored(self) -> dict:
        if self.token_file.exists():
            return json.loads(self.token_file.read_text())
        rt = os.getenv("X_REFRESH_TOKEN")
        return {"refresh_token": rt} if rt else {}

    def is_configured(self) -> bool:
        return bool(self.client_id and self._stored().get("refresh_token"))

    async def _http(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=60)

    async def _access_token(self) -> str:
        tok = self._stored()
        if tok.get("access_token") and tok.get("expires_at", 0) > time.time() + 60:
            return tok["access_token"]
        if not self.is_configured():
            raise NotConfiguredError("x: set X_CLIENT_ID and X_REFRESH_TOKEN")
        client = await self._http()
        try:
            r = await client.post(f"{API}/oauth2/token", data={
                "grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
                "client_id": self.client_id})
            data = r.json()
        finally:
            if self._client is None:
                await client.aclose()
        if "access_token" not in data:
            raise ProviderError(f"x token refresh failed: {data}")
        new = {"access_token": data["access_token"],
               "refresh_token": data.get("refresh_token", tok["refresh_token"]),
               "expires_at": time.time() + int(data.get("expires_in", 7200))}
        # X rotates refresh tokens: persist the new one or the next refresh fails.
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(json.dumps(new))
        self.token_file.chmod(0o600)
        return new["access_token"]

    async def _api(self, method: str, path: str, **kwargs) -> dict:
        token = await self._access_token()
        client = await self._http()
        try:
            r = await client.request(method, f"{API}/{path}",
                                     headers={"Authorization": f"Bearer {token}"}, **kwargs)
            data = r.json() if r.content else {}
        finally:
            if self._client is None:
                await client.aclose()
        if r.status_code >= 400:
            raise ProviderError(f"x {path}: {r.status_code} {data}")
        return data

    async def publish(self, draft: PostDraft) -> PublishResult:
        text = draft.text + (f" {draft.link}" if draft.link else "")
        data = await self._api("POST", "tweets", json={"text": text})
        post_id = data["data"]["id"]
        return PublishResult(platform=self.name, status=PublishStatus.PUBLISHED, post_id=post_id,
                             url=f"https://x.com/i/web/status/{post_id}", raw=data)

    async def get_metrics(self, post_id: str) -> dict:
        data = await self._api("GET", f"tweets/{post_id}", params={"tweet.fields": "public_metrics"})
        return data["data"].get("public_metrics", {})

    async def delete(self, post_id: str) -> None:
        await self._api("DELETE", f"tweets/{post_id}")
