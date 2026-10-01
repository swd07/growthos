"""Telegram channel publishing through the Bot API.

Setup: create a bot with @BotFather, add it to the channel as an admin with
"Post messages" permission. Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
(@channelname or -100... numeric id).
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

API = "https://api.telegram.org"
TEXT_LIMIT = 4096
CAPTION_LIMIT = 1024


class TelegramProvider(SocialProvider):
    name = "telegram"

    def __init__(self, token: str | None = None, channel_id: str | None = None,
                 client: httpx.AsyncClient | None = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")
        self._client = client

    def capabilities(self) -> Capabilities:
        return Capabilities(
            image=True, video=True, carousel=True, metrics=False,
            max_text_len=TEXT_LIMIT,
            notes="Caption limit with media is 1024 chars. Bot API does not expose view counts.",
        )

    def is_configured(self) -> bool:
        return bool(self.token and self.channel_id)

    def validate(self, draft: PostDraft) -> list[str]:
        problems = super().validate(draft)
        if draft.media and len(draft.text) > CAPTION_LIMIT:
            problems.append(f"caption is {len(draft.text)} chars, limit with media is {CAPTION_LIMIT}")
        return problems

    async def _call(self, method: str, payload: dict) -> dict:
        if not self.is_configured():
            raise NotConfiguredError("telegram: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID")
        client = self._client or httpx.AsyncClient(timeout=60)
        try:
            r = await client.post(f"{API}/bot{self.token}/{method}", json=payload)
            data = r.json()
        finally:
            if self._client is None:
                await client.aclose()
        if not data.get("ok"):
            raise ProviderError(f"telegram {method}: {data.get('description', r.status_code)}")
        return data["result"]

    def _url(self, message: dict) -> str | None:
        chat = message.get("chat", {})
        username = chat.get("username")
        return f"https://t.me/{username}/{message['message_id']}" if username else None

    async def publish(self, draft: PostDraft) -> PublishResult:
        chat_id = draft.target or self.channel_id
        text = draft.text + (f"\n\n{draft.link}" if draft.link else "")
        if not draft.media:
            result = await self._call("sendMessage", {"chat_id": chat_id, "text": text})
            messages = [result]
        elif len(draft.media) == 1:
            m = draft.media[0]
            method, field = ("sendPhoto", "photo") if m.kind is MediaKind.IMAGE else ("sendVideo", "video")
            result = await self._call(method, {"chat_id": chat_id, field: m.url, "caption": text})
            messages = [result]
        else:
            items = [
                {"type": "photo" if m.kind is MediaKind.IMAGE else "video", "media": m.url}
                for m in draft.media[:10]
            ]
            items[0]["caption"] = text
            messages = await self._call("sendMediaGroup", {"chat_id": chat_id, "media": items})
        first = messages[0]
        return PublishResult(
            platform=self.name,
            status=PublishStatus.PUBLISHED,
            post_id=f"{first['chat']['id']}:{first['message_id']}",
            url=self._url(first),
            raw={"message_ids": [m["message_id"] for m in messages]},
        )

    async def delete(self, post_id: str) -> None:
        chat_id, message_id = post_id.split(":", 1)
        await self._call("deleteMessage", {"chat_id": chat_id, "message_id": int(message_id)})
