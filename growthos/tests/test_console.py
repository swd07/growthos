import asyncio
import json
import warnings

import httpx
import pytest

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from starlette.testclient import TestClient  # noqa: E402

from growthos import state
from growthos.providers.social import ProviderError
from growthos.providers.social.telegram import TelegramProvider


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def srv(monkeypatch, tmp_path):
    monkeypatch.setenv("GROWTHOS_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("GROWTHOS_ENV_FILE", str(tmp_path / "none.env"))
    import importlib

    import growthos.mcp_server.server as server
    server = importlib.reload(server)
    sent = []

    def handler(req):
        sent.append(req)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1, "chat": {"id": -1}}})

    monkeypatch.setattr(server, "get_provider", lambda name: TelegramProvider(
        "T", "-1", client=httpx.AsyncClient(transport=httpx.MockTransport(handler))))
    server.sent = sent
    return server


@pytest.fixture
def console():
    from growthos.console.app import create_app

    return TestClient(create_app("k3y"))


def test_model_never_receives_a_code(srv):
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    blob = json.dumps(prev)
    assert "approval_code" not in prev and prev["approval_status"] == "pending"
    stored = state.load_drafts()[prev["draft_id"]]
    assert "approval_hash" not in stored          # nothing to guess against until a human approves
    assert "approval_hash" not in blob


def test_console_requires_session_key(srv, console):
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    assert console.get("/api/state").status_code == 401
    assert console.get("/api/state", headers={"X-Console-Key": "wrong"}).status_code == 401
    assert console.post(f"/api/drafts/{prev['draft_id']}/approve").status_code == 401
    assert state.approval_status(state.load_drafts()[prev["draft_id"]]) == "pending"
    assert console.get("/").status_code == 200    # the page itself is public, the data is not


def test_console_approve_then_agent_publishes(srv, console, monkeypatch):
    monkeypatch.setenv("GROWTHOS_ALLOW_PUBLISH", "1")
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    h = {"X-Console-Key": "k3y"}
    page = console.get("/api/state", headers=h).json()
    assert page["drafts"][0]["needs_decision"] is True
    assert "approval_hash" not in json.dumps(page)
    code = console.post(f"/api/drafts/{prev['draft_id']}/approve", headers=h).json()["code"]
    assert "approval_hash" not in json.dumps(console.get("/api/state", headers=h).json())
    out = run(srv.social_publish(prev["draft_id"], code.upper()))   # case does not matter
    assert out["results"]["telegram"]["status"] == "published" and len(srv.sent) == 1
    page = console.get("/api/state", headers=h).json()
    assert page["drafts"][0]["approval_status"] == "used"
    assert page["platforms"][[p["platform"] for p in page["platforms"]].index("telegram")]["verified_live"]


def test_reject_blocks_publish(srv, console):
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    h = {"X-Console-Key": "k3y"}
    code = console.post(f"/api/drafts/{prev['draft_id']}/approve", headers=h).json()["code"]
    console.post(f"/api/drafts/{prev['draft_id']}/reject", headers=h)
    with pytest.raises(ProviderError, match="rejected"):
        run(srv.social_publish(prev["draft_id"], code))
    assert not srv.sent


def test_wrong_codes_lock_the_draft(srv, monkeypatch):
    monkeypatch.setenv("GROWTHOS_ALLOW_PUBLISH", "1")
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    drafts = state.load_drafts()
    code = state.approve(drafts[prev["draft_id"]])
    state.save_drafts(drafts)
    for _ in range(state.MAX_FAILED_ATTEMPTS):
        with pytest.raises(ProviderError):
            run(srv.social_publish(prev["draft_id"], "000000"))
    with pytest.raises(ProviderError, match="locked"):        # even the right code is refused now
        run(srv.social_publish(prev["draft_id"], code))
    assert not srv.sent


def test_new_preview_needs_a_new_decision(srv):
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    drafts = state.load_drafts()
    code = state.approve(drafts[prev["draft_id"]])
    state.save_drafts(drafts)
    srv.social_preview(platforms=["telegram"], text="hello")    # same content, same draft_id
    with pytest.raises(ProviderError, match="waiting for approval"):
        run(srv.social_publish(prev["draft_id"], code))


def test_legacy_draft_with_inline_code_still_publishes(srv, monkeypatch):
    """Drafts written before the console existed carry approval_hash and no status."""
    monkeypatch.setenv("GROWTHOS_ALLOW_PUBLISH", "1")
    prev = srv.social_preview(platforms=["telegram"], text="hello")
    drafts = state.load_drafts()
    rec = drafts[prev["draft_id"]]
    rec.pop("approval_status")
    rec["approval_hash"] = state.code_hash("abc123")
    state.save_drafts(drafts)
    out = run(srv.social_publish(prev["draft_id"], "abc123"))
    assert out["results"]["telegram"]["status"] == "published"
