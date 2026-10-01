"""One-time OAuth helpers to obtain refresh tokens for X and YouTube.

Run on your own computer (it opens a browser and listens on 127.0.0.1:8765):

  python -m growthos.scripts.social_auth x        # needs X_CLIENT_ID
  python -m growthos.scripts.social_auth youtube  # needs YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET

Register http://127.0.0.1:8765/callback as the redirect / callback URL in the
X developer portal. For YouTube use an OAuth client of type "Desktop app".
The script prints the line to paste into .env.social.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import os
import secrets
import sys
import urllib.parse
import webbrowser

import httpx

REDIRECT = "http://127.0.0.1:8765/callback"


def _wait_for_code(expected_state: str) -> str:
    result: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            result.update(q)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab.")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
    while "code" not in result and "error" not in result:
        server.handle_request()
    if result.get("state") != expected_state:
        sys.exit("state mismatch, aborting")
    if "error" in result:
        sys.exit(f"authorization failed: {result['error']}")
    return result["code"]


def auth_x() -> None:
    client_id = os.environ["X_CLIENT_ID"]
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    url = "https://x.com/i/oauth2/authorize?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id, "redirect_uri": REDIRECT,
        "scope": "tweet.read tweet.write users.read offline.access", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    webbrowser.open(url)
    print("If the browser did not open, visit:\n", url)
    code = _wait_for_code(state)
    data = httpx.post("https://api.x.com/2/oauth2/token", data={
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
        "client_id": client_id, "code_verifier": verifier}).json()
    print(f"\nX_REFRESH_TOKEN={data['refresh_token']}")


def auth_youtube() -> None:
    cid, secret = os.environ["YOUTUBE_CLIENT_ID"], os.environ["YOUTUBE_CLIENT_SECRET"]
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline", "prompt": "consent", "state": state})
    webbrowser.open(url)
    print("If the browser did not open, visit:\n", url)
    code = _wait_for_code(state)
    data = httpx.post("https://oauth2.googleapis.com/token", data={
        "code": code, "client_id": cid, "client_secret": secret,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).json()
    print(f"\nYOUTUBE_REFRESH_TOKEN={data['refresh_token']}")


if __name__ == "__main__":
    from growthos.mcp_server.server import _load_env_file

    _load_env_file()
    {"x": auth_x, "youtube": auth_youtube}[sys.argv[1] if len(sys.argv) > 1 else "x"]()
