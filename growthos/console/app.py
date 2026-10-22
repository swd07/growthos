"""GrowthOS approval console: the human side of the publish flow.

Claude Code prepares drafts through the MCP server; this page is where a person reads them and
decides. Approving a draft generates a one-time code that is shown here, in the browser, and
nowhere else: the MCP server never returns it to the model, and only its hash is stored. The
person sends the code to Claude in the chat, and social_publish checks it.

The page also shows which platforms are configured, the publish log and the collected
Instagram/X account metrics.

Run from the repository root (so .env.social is found):

    python -m growthos.console            # http://127.0.0.1:8765, opens the browser

Access: the server binds to 127.0.0.1 only, and every API call must carry a session key that is
generated at start-up and printed once to this terminal (it is part of the URL the browser opens).
The key never touches disk, so the agent cannot read it from the state directory.

Honest limit: on one machine, a process with full shell access to your user account could still
reach this page or your terminal. Real separation needs a second device, e.g. approving on a phone.
"""

from __future__ import annotations

import argparse
import hmac
import os
import secrets
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from growthos import state
from growthos.providers.social import PROVIDERS, get_provider

PAGE = Path(__file__).with_name("index.html")
PUBLISHED = {"published", "processing", "private_only"}


def _load_env_file() -> None:
    """Same rules as the MCP server: KEY=VALUE pairs from GROWTHOS_ENV_FILE, never overriding."""
    path = Path(os.getenv("GROWTHOS_ENV_FILE", ".env.social")).expanduser()
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _public_draft(draft_id: str, record: dict[str, Any]) -> dict[str, Any]:
    """A draft as the page sees it: never the hash."""
    results = record.get("results", {})
    status = state.approval_status(record)
    published = [p for p, r in results.items() if r.get("status") in PUBLISHED]
    return {
        "draft_id": draft_id,
        "platforms": record.get("platforms", []),
        "draft": record.get("draft", {}),
        "checks": record.get("checks", {}),
        "results": results,
        "approval_status": status,
        "failed_attempts": record.get("failed_attempts", 0),
        "created_at": record.get("created_at"),
        "previewed_at": record.get("previewed_at") or record.get("created_at"),
        "approved_at": record.get("approved_at"),
        "published_to": published,
        "needs_decision": status == state.PENDING and not record.get("approval_used")
        and set(published) != set(record.get("platforms", [])),
    }


def _platforms(log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    live = {e.get("platform") for e in log if e.get("status") in PUBLISHED}
    out = []
    for name in PROVIDERS:
        try:
            configured = get_provider(name).is_configured()
        except Exception:  # a broken adapter must not take the page down
            configured = False
        out.append({"platform": name, "configured": configured, "verified_live": name in live})
    return out


def _account_metrics() -> list[dict[str, Any]]:
    try:
        from growthos.metrics.collector import iter_snapshots
    except Exception:
        return []
    rows = [r for r in iter_snapshots() if r.get("kind") == "account"]
    return [{"date": r.get("date"), "platform": r.get("platform"), "metrics": r.get("metrics", {})}
            for r in rows]


def create_app(session_key: str) -> Starlette:
    def authorized(request: Request) -> bool:
        given = request.headers.get("x-console-key", "")
        return bool(given) and hmac.compare_digest(given, session_key)

    def deny() -> JSONResponse:
        return JSONResponse({"error": "missing or wrong console key; open the URL printed in "
                                      "the console terminal"}, status_code=401)

    async def index(request: Request) -> HTMLResponse:
        return HTMLResponse(PAGE.read_text(encoding="utf-8"),
                            headers={"Cache-Control": "no-store",
                                     "Referrer-Policy": "no-referrer"})

    async def api_state(request: Request) -> JSONResponse:
        if not authorized(request):
            return deny()
        drafts = state.load_drafts()
        log = state.read_log()
        items = [_public_draft(k, v) for k, v in drafts.items()]
        items.sort(key=lambda d: d.get("previewed_at") or 0, reverse=True)
        return JSONResponse({
            "now": time.time(),
            "publishing_enabled": os.getenv("GROWTHOS_ALLOW_PUBLISH") == "1",
            "state_dir": str(state.state_dir()),
            "platforms": _platforms(log),
            "drafts": items,
            "log": list(reversed(log[-30:])),
            "account_metrics": _account_metrics(),
        })

    def _change(request: Request, action: str) -> JSONResponse:
        draft_id = request.path_params["draft_id"]
        drafts = state.load_drafts()
        if draft_id not in drafts:
            return JSONResponse({"error": f"unknown draft {draft_id}"}, status_code=404)
        record = drafts[draft_id]
        body: dict[str, Any] = {"draft_id": draft_id}
        if action == "approve":
            body["code"] = state.approve(record)
        else:
            state.reject(record)
        state.save_drafts(drafts)
        body["approval_status"] = state.approval_status(record)
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    async def approve(request: Request) -> JSONResponse:
        return _change(request, "approve") if authorized(request) else deny()

    async def reject(request: Request) -> JSONResponse:
        return _change(request, "reject") if authorized(request) else deny()

    return Starlette(routes=[
        Route("/", index),
        Route("/api/state", api_state),
        Route("/api/drafts/{draft_id}/approve", approve, methods=["POST"]),
        Route("/api/drafts/{draft_id}/reject", reject, methods=["POST"]),
    ])


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="GrowthOS approval console")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    _load_env_file()
    key = secrets.token_urlsafe(18)
    url = f"http://127.0.0.1:{args.port}/#key={key}"
    print("\n  GrowthOS console")
    print(f"  state:   {state.state_dir()}")
    print(f"  publish: {'LIVE' if os.getenv('GROWTHOS_ALLOW_PUBLISH') == '1' else 'dry run'}")
    print(f"  open:    {url}\n")
    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(create_app(key), host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
