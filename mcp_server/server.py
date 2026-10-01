"""GrowthOS social MCP server for Claude Code.

Flow (generate != publish):
  1. social_preview  -> validates the post for each platform, stores an immutable draft
  2. you review the draft
  3. social_publish  -> publishes exactly that draft; real publishing only when
                         GROWTHOS_ALLOW_PUBLISH=1, otherwise a dry run

Run:  python -m growthos.mcp_server.server   (stdio transport)
"""

from __future__ import annotations

import hashlib
import json
import os
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


def _load_env_file() -> None:
    """Load KEY=VALUE pairs from GROWTHOS_ENV_FILE (default ./.env.social) without overriding the environment."""
    path = Path(os.getenv("GROWTHOS_ENV_FILE", ".env.social")).expanduser()
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _drafts() -> dict[str, Any]:
    return json.loads(DRAFTS.read_text()) if DRAFTS.exists() else {}


def _save_drafts(d: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DRAFTS.write_text(json.dumps(d, ensure_ascii=False, indent=2))


def _log(entry: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
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
    Returns draft_id plus per-platform problems. Nothing is published.
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
    drafts = _drafts()
    drafts[draft_id] = {"platforms": platforms, "draft": json.loads(body), "checks": checks,
                        "created_at": time.time(), "results": {}}
    _save_drafts(drafts)
    ready = [n for n, c in checks.items() if c["configured"] and not c["problems"]]
    return {"draft_id": draft_id, "ready": ready, "checks": checks, "draft": json.loads(body),
            "publishing_enabled": os.getenv("GROWTHOS_ALLOW_PUBLISH") == "1"}


@mcp.tool()
async def social_publish(draft_id: str, platforms: list[str] | None = None) -> dict[str, Any]:
    """Publish a previously previewed draft. Only call after the user explicitly approved it.

    Publishes for real only when GROWTHOS_ALLOW_PUBLISH=1; otherwise returns a dry run.
    Platforms already published for this draft are skipped (idempotent).
    """
    drafts = _drafts()
    if draft_id not in drafts:
        raise ProviderError(f"unknown draft_id {draft_id}; call social_preview first")
    record = drafts[draft_id]
    draft = PostDraft.model_validate(record["draft"])
    live = os.getenv("GROWTHOS_ALLOW_PUBLISH") == "1"
    results: dict[str, Any] = {}
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
def social_history(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recent publish log entries."""
    if not LOG.exists():
        return []
    lines = LOG.read_text().splitlines()[-limit:]
    return [json.loads(x) for x in lines]


def main() -> None:
    _load_env_file()
    mcp.run()


if __name__ == "__main__":
    main()
