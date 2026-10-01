# Social Provider Interface

**Status:** implemented (v0, own-account dogfooding)
**Code:** `growthos/providers/social/`, MCP server `growthos/mcp_server/server.py`

## Principle

`generate ≠ publish`. Claude Code (or any MCP client) can draft and validate posts freely.
Publishing a draft needs **two independent locks**:

1. **Approval code.** `social_preview` returns a one-time 6-character code
   (`secrets.token_hex(3)`); only its SHA-256 hash is stored in the draft. `social_publish`
   takes the code as a required argument and publishes nothing without a match. The model
   must not pass a code the user has not repeated back — the code is what proves a human
   saw *this* draft. A real publish burns it; a dry run does not.
2. **Environment switch.** Nothing leaves the machine unless `GROWTHOS_ALLOW_PUBLISH=1`.

The locks are independent on purpose: the switch can be left on for a working session and
the code still forces a human decision per post.

Claude Code also asks the user before every MCP tool call unless the tool is explicitly
allow-listed — keep `social_publish` off the allow-list.

## Contract

```python
class SocialProvider(ABC):
    name: str
    def capabilities(self) -> Capabilities      # text/image/video/carousel/metrics, limits, notes
    def is_configured(self) -> bool             # credentials present
    def validate(self, draft: PostDraft) -> list[str]   # human-readable problems, [] = ok
    async def publish(self, draft: PostDraft) -> PublishResult
    async def get_metrics(self, post_id: str) -> dict
    async def delete(self, post_id: str) -> None
```

`PostDraft`: text, media (public HTTPS URLs, image/video), link, title, target
(subreddit / chat id), extra (platform-specific), idempotency_key.

`PublishStatus`: `published`, `processing`, `private_only` (platform forced private
visibility for an unaudited app), `manual_required` (human finishes the post),
`dry_run`, `failed`.

## Adapters (v0)

| Platform | Mode | Text | Image | Video | Metrics | Blocker for full automation |
|---|---|---|---|---|---|---|
| Telegram | direct (Bot API) | ✓ | ✓ | ✓ | – | none |
| Instagram | direct (Graph API) | caption | ✓ | Reels | ✓ | none for own account (Dev mode); Advanced Access for other accounts |
| Facebook Page | direct (Graph API) | ✓ | ✓ | ✓ | – | same as Instagram |
| Threads | direct (Threads API) | ✓ | ✓ | ✓ | – | same as Instagram |
| X | direct (API v2) | ✓ | – | – | ✓ | paid per post (~$0.015, ~$0.20 with link) |
| YouTube | direct (Data API v3) | – | – | ✓ | – | private-only until YouTube API audit |
| TikTok | inbox draft | – | – | ✓ | – | Direct Post public only after TikTok audit |
| Reddit | assisted (prefilled link) | ✓ | – | – | – | no self-serve API since late 2025; Data Access Request review |

## MCP tools

| Tool | Effect |
|---|---|
| `social_list_platforms` | which platforms are configured + limits |
| `social_preview` | validate a post for N platforms, store immutable draft → `draft_id` + one-time `approval_code` |
| `social_publish` | `(draft_id, approval_code, platforms?)` — publish a stored draft (dry run unless `GROWTHOS_ALLOW_PUBLISH=1`); idempotent per platform; refuses without a matching code |
| `social_record_manual` | store final URL of a hand-published post (Reddit, TikTok inbox) |
| `social_get_metrics` | per-post metrics where supported (Instagram, X) |
| `social_history` | recent publish log |

Re-previewing identical content returns the same `draft_id` (it is a content hash) with a
fresh approval code, and keeps the publish results already recorded for it, so a repeat
preview cannot undo idempotency.

State lives in `~/.growthos/` (`drafts.json`, `publish_log.jsonl`, rotated X token). Only
approval-code hashes are stored, never the codes themselves.
This is a v0 file store; it moves to PostgreSQL with the Publishing Engine (plan §12).

## Known gaps / next steps

1. Media upload from local files (today: public URLs only) — needs object storage (plan §22, S3/MinIO).
2. X media upload, X threads.
3. Metrics for Telegram (no API for views), Facebook, Threads, YouTube Analytics.
4. Scheduling: today Claude Code publishes immediately; durable scheduling arrives with Temporal (plan §12).
5. Long-lived token refresh for Meta (60-day tokens) and TikTok.
6. Optional aggregator adapter (e.g. Postiz self-hosted) as a fallback for platforms whose audits are pending.
7. Start audits early: YouTube API audit, TikTok Content Posting audit, Reddit Data Access Request,
   Meta Advanced Access (only when onboarding external brands).
