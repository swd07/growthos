"""Shared on-disk state for the MCP server and the approval console.

Both processes read and write the same files under GROWTHOS_STATE_DIR (default ~/.growthos):

* drafts.json        - every previewed draft, its approval state and per-platform results
* publish_log.jsonl  - append-only log of what really left the machine

The directory is resolved on every call, not at import, so tests and a second process can
point at a different store without reloading modules.

Approval model
--------------
A draft is created *pending*. Only the console can approve it: approving generates a one-time
code, shows it to the human in the browser and stores nothing but its SHA-256 hash. The model
never receives the code from any tool; the only way it learns it is the human typing it into the
chat. Wrong codes are counted and the draft locks after MAX_FAILED_ATTEMPTS, so the six-character
code cannot be guessed by retrying.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

MAX_FAILED_ATTEMPTS = 5

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
LOCKED = "locked"
USED = "used"


def state_dir() -> Path:
    return Path(os.getenv("GROWTHOS_STATE_DIR", "~/.growthos")).expanduser()


def drafts_path() -> Path:
    return state_dir() / "drafts.json"


def log_path() -> Path:
    return state_dir() / "publish_log.jsonl"


def load_drafts() -> dict[str, Any]:
    path = drafts_path()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_drafts(drafts: dict[str, Any]) -> None:
    """Write the draft store atomically: a failed write must not truncate what is there."""
    path = drafts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(drafts, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def append_log(entry: dict[str, Any]) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **entry}, ensure_ascii=False) + "\n")


def read_log(limit: int | None = None) -> list[dict[str, Any]]:
    path = log_path()
    if not path.exists():
        return []
    lines = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if limit is not None:
        lines = lines[-limit:]
    return [json.loads(x) for x in lines]


def code_hash(code: str) -> str:
    """Hash an approval code; only the hash is ever stored on disk."""
    return hashlib.sha256(code.strip().lower().encode()).hexdigest()


def approval_status(record: dict[str, Any]) -> str:
    """Status of a draft record, including records written before the console existed."""
    status = record.get("approval_status")
    if status:
        return status
    # legacy record: the code was handed out by social_preview itself
    if record.get("approval_hash") and not record.get("approval_used"):
        return APPROVED
    return PENDING


def mark_pending(record: dict[str, Any]) -> None:
    record.update(approval_status=PENDING, approval_used=False, failed_attempts=0)
    record.pop("approval_hash", None)
    record.pop("approved_at", None)


def approve(record: dict[str, Any]) -> str:
    """Approve a draft and return a fresh one-time code. Called only by the console."""
    code = secrets.token_hex(3)
    record.update(approval_status=APPROVED, approval_hash=code_hash(code), approval_used=False,
                  failed_attempts=0, approved_at=time.time())
    return code


def reject(record: dict[str, Any]) -> None:
    record.update(approval_status=REJECTED, approval_used=False, failed_attempts=0)
    record.pop("approval_hash", None)


def check_code(record: dict[str, Any], code: str) -> str | None:
    """Return None when `code` unlocks the draft, otherwise the reason it does not.

    Mutates the record: a wrong code counts toward the lock-out. The caller saves it.
    """
    status = approval_status(record)
    if status == REJECTED:
        return "the draft was rejected in the console; nothing was published"
    if status == LOCKED:
        return ("too many wrong approval codes; the draft is locked. Ask the user to approve it "
                "again in the GrowthOS console")
    if record.get("approval_used"):
        return ("approval code already used for this draft; ask the user to approve it again "
                "in the GrowthOS console")
    expected = record.get("approval_hash")
    if status != APPROVED or not expected:
        return ("the draft is waiting for approval. Ask the user to open the GrowthOS console "
                "(python -m growthos.console), approve it there and send you the code")
    if code and hmac.compare_digest(code_hash(code), expected):
        return None
    record["failed_attempts"] = int(record.get("failed_attempts", 0)) + 1
    if record["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
        record["approval_status"] = LOCKED
        record.pop("approval_hash", None)
        return "approval_code wrong; the draft is now locked. Nothing was published"
    left = MAX_FAILED_ATTEMPTS - record["failed_attempts"]
    return f"approval_code missing or wrong ({left} attempts left); nothing was published"


def burn(record: dict[str, Any]) -> None:
    """One-time code: burn it once something really left the machine."""
    record["approval_used"] = True
    record["approval_status"] = USED
    record.pop("approval_hash", None)
