"""Daily metrics collector.

Takes a dated snapshot of two different things and appends them to `~/.growthos/metrics.jsonl`:

* **account** — how the profile is moving (followers, reach, profile views...), one record per
  platform that implements `get_account_metrics`;
* **post** — how each published post is doing, one record per post found in `publish_log.jsonl`
  on a platform whose adapter implements `get_metrics`.

The file is append-only. A snapshot is never rewritten, because the value of this store is the
series: "which post worked" is a question about change over time, and an overwritten history
cannot answer it. Running twice on the same day is a no-op unless `force=True`, so a cron job
that fires twice does not pollute the series with duplicates.

One platform failing must not cost the others their snapshot, so every call is isolated: a
failure is recorded in the run summary and the loop continues.

Run it daily:

    python -m growthos.metrics.collector
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from growthos.providers.social import PROVIDERS, get_provider

PUBLISHED_STATUSES = {"published", "processing", "private_only"}


def _state_dir() -> Path:
    """Resolved per call, not at import, so tests and cron can redirect the store."""
    return Path(os.getenv("GROWTHOS_STATE_DIR", "~/.growthos")).expanduser()


def snapshots_path() -> Path:
    return _state_dir() / "metrics.jsonl"


def _publish_log_path() -> Path:
    return _state_dir() / "publish_log.jsonl"


def iter_snapshots() -> Iterator[dict[str, Any]]:
    path = snapshots_path()
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def _append(record: dict[str, Any]) -> None:
    path = snapshots_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def published_posts() -> list[tuple[str, str]]:
    """Unique (platform, post_id) pairs that actually went out, oldest first."""
    path = _publish_log_path()
    if not path.exists():
        return []
    seen: dict[tuple[str, str], None] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        platform, post_id, status = entry.get("platform"), entry.get("post_id"), entry.get("status")
        if platform and post_id and status in PUBLISHED_STATUSES:
            seen.setdefault((platform, post_id), None)
    return list(seen)


def _taken_today(kind: str, platform: str, subject: str, day: str) -> bool:
    return any(s.get("kind") == kind and s.get("platform") == platform
               and s.get("subject") == subject and s.get("date") == day
               for s in iter_snapshots())


def _record(kind: str, platform: str, subject: str, day: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {"ts": time.time(), "date": day, "kind": kind, "platform": platform,
            "subject": subject, "metrics": metrics}


async def collect(force: bool = False, day: str | None = None) -> dict[str, Any]:
    """Take today's snapshots. Returns a summary; never raises because one platform failed."""
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    taken: list[dict[str, Any]] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []

    for name in PROVIDERS:
        try:
            provider = get_provider(name)
            if not provider.is_configured() or not provider.capabilities().account_metrics:
                continue        # no account-level numbers on this platform: not a failure
            subject = "account"
            if not force and _taken_today("account", name, subject, day):
                skipped.append(f"{name}/account")
                continue
            metrics = await provider.get_account_metrics()
        except Exception as exc:  # noqa: BLE001 - one platform must not stop the rest
            failed.append({"target": f"{name}/account", "error": str(exc)[:200]})
            continue
        record = _record("account", name, subject, day, metrics)
        _append(record)
        taken.append(record)

    for platform, post_id in published_posts():
        try:
            provider = get_provider(platform)
            if not provider.capabilities().metrics or not provider.is_configured():
                continue
            if not force and _taken_today("post", platform, post_id, day):
                skipped.append(f"{platform}/{post_id}")
                continue
            metrics = await provider.get_metrics(post_id)
        except Exception as exc:  # noqa: BLE001 - a deleted post must not stop the run
            failed.append({"target": f"{platform}/{post_id}", "error": str(exc)[:200]})
            continue
        record = _record("post", platform, post_id, day, metrics)
        _append(record)
        taken.append(record)

    return {"date": day, "taken": taken, "skipped": skipped, "failed": failed,
            "store": str(snapshots_path())}


def main() -> None:
    from growthos.mcp_server.server import _load_env_file

    _load_env_file()
    summary = asyncio.run(collect())
    print(f"{summary['date']}: {len(summary['taken'])} snapshots, "
          f"{len(summary['skipped'])} already taken, {len(summary['failed'])} failed")
    for record in summary["taken"]:
        print(f"  {record['kind']:7} {record['platform']:10} {record['subject'][:24]:24} {record['metrics']}")
    for failure in summary["failed"]:
        print(f"  FAILED  {failure['target']}: {failure['error']}")


if __name__ == "__main__":
    main()
