"""GrowthOS social MCP server for Claude Code.

Flow (generate != publish):
  1. social_preview  -> validates the post for each platform, stores an immutable draft
                        and returns a one-time approval code
  2. you review the draft and send the code back yourself
  3. social_publish  -> requires that code and publishes exactly that draft; real
                        publishing only when GROWTHOS_ALLOW_PUBLISH=1, otherwise a dry run

Two independent locks: the approval code proves a human saw this exact draft, the
GROWTHOS_ALLOW_PUBLISH switch decides whether anything can leave the machine at all.

Run:  python -m growthos.mcp_server.server   (stdio transport)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from growthos.providers.social import (
    PROVIDERS,
    MediaItem,
    MediaKind,
    PostDraft,
    ProviderError,
    PublishResult,
    PublishStatus,
    get_provider,
)

STATE_DIR = Path(os.getenv("GROWTHOS_STATE_DIR", "~/.growthos")).expanduser()
DRAFTS = STATE_DIR / "drafts.json"
LOG = STATE_DIR / "publish_log.jsonl"

mcp = FastMCP("growthos-social")

# httpx logs every request URL at INFO and the Telegram Bot API carries the bot token in the
# URL path, so an INFO-level log writes the token into the MCP server log. Keep it at WARNING.
logging.getLogger("httpx").setLevel(logging.WARNING)


def _load_env_file() -> None:
    """Load KEY=VALUE pairs from GROWTHOS_ENV_FILE (default ./.env.social) without overriding the environment."""
    path = Path(os.getenv("GROWTHOS_ENV_FILE", ".env.social")).expanduser()
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _drafts() -> dict[str, Any]:
    return json.loads(DRAFTS.read_text(encoding="utf-8")) if DRAFTS.exists() else {}


def _save_drafts(d: dict[str, Any]) -> None:
    """Write the draft store atomically: a failed write must not truncate what is there."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DRAFTS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DRAFTS)


def _code_hash(code: str) -> str:
    """Hash an approval code; only the hash is ever stored on disk."""
    return hashlib.sha256(code.strip().encode()).hexdigest()


def _log(entry: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **entry}, ensure_ascii=False) + "\n")


@mcp.tool()
def social_list_platforms() -> list[dict[str, Any]]:
    """List supported platforms, whether credentials are configured, and their limits."""
    out = []
    for name in PROVIDERS:
        p = get_provider(name)
        out.append({"platform": name, "configured": p.is_configured(),
                    "capabilities": p.capabilities().model_dump()})
    return out


@mcp.tool()
def social_preview(platforms: list[str], text: str = "", image_urls: list[str] | None = None,
                   video_urls: list[str] | None = None, title: str | None = None,
                   link: str | None = None, target: str | None = None,
                   extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate a post for the given platforms and save it as a draft awaiting approval.

    Media must be public HTTPS URLs. `target` = subreddit for Reddit or a chat id for Telegram.
    Returns draft_id, per-platform problems and a one-time approval_code. Nothing is published.

    Show the approval code to the user and call social_publish only with the code they
    send back themselves. Never pass a code the user has not repeated.
    """
    media = [MediaItem(kind=MediaKind.IMAGE, url=u) for u in image_urls or []]
    media += [MediaItem(kind=MediaKind.VIDEO, url=u) for u in video_urls or []]
    draft = PostDraft(text=text, media=media, title=title, link=link, target=target, extra=extra or {})
    checks: dict[str, Any] = {}
    for name in platforms:
        p = get_provider(name)
        checks[name] = {"configured": p.is_configured(), "problems": p.validate(draft)}
    body = draft.model_dump_json()
    draft_id = hashlib.sha256((body + ",".join(sorted(platforms))).encode()).hexdigest()[:12]
    approval_code = secrets.token_hex(3)
    drafts = _drafts()
    # draft_id is a hash of the content, so re-previewing the same post lands on the same
    # record: keep what was already published for it, or idempotency would be lost.
    prior = drafts.get(draft_id, {})
    drafts[draft_id] = {"platforms": platforms, "draft": json.loads(body), "checks": checks,
                        "created_at": prior.get("created_at", time.time()),
                        "results": prior.get("results", {}),
                        "approval_hash": _code_hash(approval_code), "approval_used": False}
    _save_drafts(drafts)
    ready = [n for n, c in checks.items() if c["configured"] and not c["problems"]]
    return {"draft_id": draft_id, "approval_code": approval_code,
            "approval_note": ("Show this code to the user. Call social_publish only with the code "
                              "they send back themselves."),
            "ready": ready, "checks": checks, "draft": json.loads(body),
            "publishing_enabled": os.getenv("GROWTHOS_ALLOW_PUBLISH") == "1"}


@mcp.tool()
async def social_publish(draft_id: str, approval_code: str,
                         platforms: list[str] | None = None) -> dict[str, Any]:
    """Publish a previously previewed draft, using the approval code the user sent back.

    `approval_code` is the code social_preview returned. Pass only a code the user has
    repeated to you; without a matching code nothing is published. The code is one-time:
    a real publish burns it, a dry run does not.

    Publishes for real only when GROWTHOS_ALLOW_PUBLISH=1; otherwise returns a dry run.
    Platforms already published for this draft are skipped (idempotent).
    """
    drafts = _drafts()
    if draft_id not in drafts:
        raise ProviderError(f"unknown draft_id {draft_id}; call social_preview first")
    record = drafts[draft_id]
    if record.get("approval_used"):
        raise ProviderError("approval code already used for this draft; run social_preview "
                            "again and ask the user for the new code")
    expected = record.get("approval_hash")
    if not expected:
        raise ProviderError("draft has no approval code; run social_preview again")
    if not approval_code or not hmac.compare_digest(_code_hash(approval_code), expected):
        raise ProviderError("approval_code missing or wrong; nothing was published")
    draft = PostDraft.model_validate(record["draft"])
    live = os.getenv("GROWTHOS_ALLOW_PUBLISH") == "1"
    results: dict[str, Any] = {}
    published_now = False
    for name in platforms or record["platforms"]:
        prev = record["results"].get(name)
        if prev and prev["status"] in {"published", "processing", "private_only"}:
            results[name] = {**prev, "detail": "already published, skipped"}
            continue
        provider = get_provider(name)
        problems = provider.validate(draft)
        if problems:
            res = PublishResult(platform=name, status=PublishStatus.FAILED, detail="; ".join(problems))
        elif not live:
            res = PublishResult(platform=name, status=PublishStatus.DRY_RUN,
                                detail="Set GROWTHOS_ALLOW_PUBLISH=1 to publish for real.")
        else:
            try:
                res = await provider.publish(draft)
            except ProviderError as e:
                res = PublishResult(platform=name, status=PublishStatus.FAILED, detail=str(e))
        data = res.model_dump(mode="json", exclude={"raw"})
        results[name] = data
        if res.status is not PublishStatus.DRY_RUN:
            record["results"][name] = data
            _log({"draft_id": draft_id, **data})
        if res.status not in {PublishStatus.DRY_RUN, PublishStatus.FAILED}:
            published_now = True
    if published_now:
        # one-time code: burn it once something really left the machine
        record["approval_used"] = True
        record.pop("approval_hash", None)
    _save_drafts(drafts)
    return {"draft_id": draft_id, "live": live, "results": results}


@mcp.tool()
def social_record_manual(draft_id: str, platform: str, url: str) -> dict[str, Any]:
    """Record the final URL of a post published by hand (Reddit, TikTok inbox)."""
    drafts = _drafts()
    if draft_id not in drafts:
        raise ProviderError(f"unknown draft_id {draft_id}")
    entry = {"platform": platform, "status": "published", "url": url, "detail": "published manually"}
    drafts[draft_id]["results"][platform] = entry
    _save_drafts(drafts)
    _log({"draft_id": draft_id, **entry})
    return entry


@mcp.tool()
async def social_get_metrics(platform: str, post_id: str) -> dict[str, Any]:
    """Fetch engagement metrics for a published post (where the platform adapter supports it)."""
    return await get_provider(platform).get_metrics(post_id)


@mcp.tool()
async def social_collect_metrics(force: bool = False) -> dict[str, Any]:
    """Take today's metrics snapshot for every configured platform and published post.

    Appends to the dated series in ~/.growthos/metrics.jsonl; running twice in a day is a no-op
    unless force=True. Read-only against the networks: nothing is published.
    """
    from growthos.metrics.collector import collect

    return await collect(force=force)


@mcp.tool()
def social_metrics_history(kind: str | None = None, platform: str | None = None,
                           subject: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Read collected metric snapshots, newest last. kind is "account" or "post"."""
    from growthos.metrics.collector import iter_snapshots

    rows = [r for r in iter_snapshots()
            if (kind is None or r.get("kind") == kind)
            and (platform is None or r.get("platform") == platform)
            and (subject is None or r.get("subject") == subject)]
    return rows[-limit:]


@mcp.tool()
def social_history(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent publish log entries."""
    if not LOG.exists():
        return []
    lines = LOG.read_text(encoding="utf-8").splitlines()[-limit:]
    return [json.loads(x) for x in lines]


def main() -> None:
    _load_env_file()
    mcp.run()


if __name__ == "__main__":
    main()
