import asyncio
import json

import httpx
import pytest

from growthos.providers.social import (
    MediaItem,
    MediaKind,
    NotConfiguredError,
    PostDraft,
    PublishStatus,
)
from growthos.providers.social.meta import InstagramProvider, ThreadsProvider
from growthos.providers.social.reddit import RedditAssistedProvider
from growthos.providers.social.telegram import TelegramProvider
from growthos.providers.social.tiktok import TikTokProvider
from growthos.providers.social.x import XProvider
from growthos.providers.social.youtube import YouTubeProvider


def run(coro):
    return asyncio.run(coro)


def mock_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_telegram_text_and_photo():
    calls = []

    def handler(req):
        calls.append((req.url.path, json.loads(req.content)))
        return httpx.Response(200, json={"ok": True, "result": {
            "message_id": 7, "chat": {"id": -100, "username": "mychan"}}})

    p = TelegramProvider("T", "@mychan", client=mock_client(handler))
    r = run(p.publish(PostDraft(text="hi", link="https://a.b")))
    assert r.status is PublishStatus.PUBLISHED and r.url == "https://t.me/mychan/7"
    assert calls[0][0].endswith("/sendMessage") and "https://a.b" in calls[0][1]["text"]
    run(p.publish(PostDraft(text="cap", media=[MediaItem(kind=MediaKind.IMAGE, url="https://i/1.jpg")])))
    assert calls[1][0].endswith("/sendPhoto") and calls[1][1]["photo"] == "https://i/1.jpg"


def test_telegram_caption_limit_and_unconfigured():
    p = TelegramProvider(None, None)
    long = PostDraft(text="x" * 1100, media=[MediaItem(kind=MediaKind.IMAGE, url="https://i")])
    assert any("caption" in s for s in TelegramProvider("t", "c").validate(long))
    with pytest.raises(NotConfiguredError):
        run(p.publish(PostDraft(text="hi")))


def test_instagram_image_flow(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_USER_ID", "42")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "tok")
    seen = []

    def handler(req):
        seen.append((req.method, req.url.path))
        if req.url.path.endswith("/42/media"):
            return httpx.Response(200, json={"id": "c1"})
        if req.url.path.endswith("/42/media_publish"):
            return httpx.Response(200, json={"id": "m1"})
        return httpx.Response(200, json={"permalink": "https://instagram.com/p/x"})

    p = InstagramProvider(client=mock_client(handler))
    r = run(p.publish(PostDraft(text="hello", media=[MediaItem(kind=MediaKind.IMAGE, url="https://i")])))
    assert r.post_id == "m1" and r.url == "https://instagram.com/p/x"
    assert [s[1] for s in seen] == ["/42/media", "/42/media_publish", "/m1"]
    assert p.validate(PostDraft(text="no media")) == ["this platform requires an image or video"]


def test_threads_text(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ID", "9")
    monkeypatch.setenv("THREADS_ACCESS_TOKEN", "tok")

    def handler(req):
        if req.url.path.endswith("/threads"):
            assert b"media_type=TEXT" in req.content
            return httpx.Response(200, json={"id": "c"})
        if req.url.path.endswith("/threads_publish"):
            return httpx.Response(200, json={"id": "t1"})
        return httpx.Response(200, json={"permalink": "https://threads.net/t1"})

    r = run(ThreadsProvider(client=mock_client(handler)).publish(PostDraft(text="hey")))
    assert r.post_id == "t1"


def test_x_refresh_rotates_token(monkeypatch, tmp_path):
    monkeypatch.setenv("X_CLIENT_ID", "cid")
    monkeypatch.setenv("X_REFRESH_TOKEN", "r0")
    monkeypatch.setenv("X_TOKEN_FILE", str(tmp_path / "x.json"))

    def handler(req):
        if req.url.path.endswith("/oauth2/token"):
            return httpx.Response(200, json={"access_token": "a1", "refresh_token": "r1", "expires_in": 7200})
        assert req.headers["Authorization"] == "Bearer a1"
        return httpx.Response(201, json={"data": {"id": "123", "text": "hi"}})

    r = run(XProvider(client=mock_client(handler)).publish(PostDraft(text="hi")))
    assert r.url == "https://x.com/i/web/status/123"
    assert json.loads((tmp_path / "x.json").read_text())["refresh_token"] == "r1"


def test_reddit_assisted_link():
    p = RedditAssistedProvider()
    d = PostDraft(text="body", title="My title", target="r/LocalLLaMA")
    assert p.validate(d) == []
    r = run(p.publish(d))
    assert r.status is PublishStatus.MANUAL_REQUIRED
    assert r.url.startswith("https://www.reddit.com/r/LocalLLaMA/submit?title=My+title")


def test_youtube_unaudited_is_private_only(monkeypatch):
    for k, v in {"YOUTUBE_CLIENT_ID": "c", "YOUTUBE_CLIENT_SECRET": "s", "YOUTUBE_REFRESH_TOKEN": "r"}.items():
        monkeypatch.setenv(k, v)

    def handler(req):
        if req.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "a"})
        if req.url.host == "media.example":
            return httpx.Response(200, content=b"video-bytes")
        if req.method == "POST":
            return httpx.Response(200, headers={"Location": "https://upload.example/session"})
        return httpx.Response(200, json={"id": "vid1"})

    d = PostDraft(text="desc", title="Demo", media=[MediaItem(kind=MediaKind.VIDEO, url="https://media.example/v.mp4")])
    r = run(YouTubeProvider(client=mock_client(handler)).publish(d))
    assert r.status is PublishStatus.PRIVATE_ONLY and r.url == "https://youtu.be/vid1"


def test_tiktok_inbox(monkeypatch):
    monkeypatch.setenv("TIKTOK_ACCESS_TOKEN", "t")

    def handler(req):
        assert req.url.path == "/v2/post/publish/inbox/video/init/"
        return httpx.Response(200, json={"data": {"publish_id": "p1"}, "error": {"code": "ok"}})

    d = PostDraft(text="c", media=[MediaItem(kind=MediaKind.VIDEO, url="https://m/v.mp4")])
    r = run(TikTokProvider(client=mock_client(handler)).publish(d))
    assert r.status is PublishStatus.MANUAL_REQUIRED and r.post_id == "p1"


def test_mcp_preview_then_dry_run_then_live(monkeypatch, tmp_path):
    monkeypatch.setenv("GROWTHOS_STATE_DIR", str(tmp_path))
    import importlib

    import growthos.mcp_server.server as srv
    srv = importlib.reload(srv)

    sent = []

    def handler(req):
        sent.append(req)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1, "chat": {"id": -1}}})

    monkeypatch.setattr(srv, "get_provider", lambda name: TelegramProvider("T", "-1", client=mock_client(handler)))
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    assert prev["ready"] == ["telegram"]
    dry = run(srv.social_publish(prev["draft_id"]))
    assert dry["results"]["telegram"]["status"] == "dry_run" and not sent

    monkeypatch.setenv("GROWTHOS_ALLOW_PUBLISH", "1")
    live = run(srv.social_publish(prev["draft_id"]))
    assert live["results"]["telegram"]["status"] == "published" and len(sent) == 1
    again = run(srv.social_publish(prev["draft_id"]))
    assert "skipped" in again["results"]["telegram"]["detail"] and len(sent) == 1
    assert len(srv.social_history()) == 1
