# GrowthOS Social — status and next tasks

**Date:** 2026-10-01
**Status:** publishing works and is verified live; the analytics half does not exist yet
**Repository:** `swd07/growthos` (moved out of `swd07/ai-marketing-platform` on 2026-10-01)
**Related:** [full project plan](2026-08-25-growthos-project-plan.md) · [provider interface](../specs/social-provider-interface.md) · [account setup](../setup/social-accounts.md)

Read this before adding features. It separates what has been run against a real API from
what has only been run against mocks, because the two are not the same kind of claim.

## 1. Verified against live APIs

| What | Evidence |
|---|---|
| Telegram publishing | Posted to the channel `@GrowthOS07` (`post_id -1003840787313:2`) on 2026-10-01 |
| Instagram publishing | Posted an image with caption to `@applied_ai_engineer` (`post_id 17949190800295960`) on 2026-10-01; the owner deleted it afterwards |
| Instagram account access | `GET /me` → `BUSINESS`, publishing quota 100 posts / 24h |
| Approval code | A publish with no code, a wrong code and a reused code were each refused, and nothing left the machine |
| Dry run | With `GROWTHOS_ALLOW_PUBLISH` unset every publish returns `dry_run`, and the code is not burned |
| Idempotency | Re-publishing a draft skips platforms already published |

13 tests pass (`pytest growthos/tests`). They cover provider logic and the MCP flow against
mocked HTTP; they do not reach a real network.

## 2. Exists in code, never run against a real API

Facebook Page, Threads, X, YouTube, TikTok, Reddit. The adapters are written and unit-tested
against mocks, no credentials have been issued, so treat them as unproven. Reddit is "assisted"
by design: it returns a prefilled submit link for a human to post.

## 3. The loop is half-built

The product idea is `idea → post → publish → measure → learn → next post`. Today only the left
half exists. Specifically:

- `social_get_metrics` returns a **snapshot** and stores nothing. There is no time series, so
  "which post worked" cannot be answered at all.
- Metrics exist only for Instagram (`reach, likes, comments, shares, saved`) and X. Telegram,
  Facebook and Threads expose none through their APIs here.
- Account-level numbers (profile visits, follower change) are a different endpoint and are not
  implemented.
- There is no report, no comparison between posts, no experiment tracking.

Anyone describing this system to a third party should say *publishing with human approval works,
the analytics loop is not built yet*.

## 4. Platform state

| Platform | Publishing | Metrics | Blocking |
|---|---|---|---|
| Telegram | live | none | — |
| Instagram | live | snapshot only | token expires ~2026-11-30 |
| Facebook Page | untested | none | needs `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_TOKEN` |
| Threads | untested | none | needs `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN` |
| X | untested | snapshot | paid tier required |
| YouTube | untested | none | uploads stay private until Google audits the project |
| TikTok | untested | none | public posting needs TikTok review; inbox drafts only |
| Reddit | assisted | none | API keys are granted by manual application |

## 5. Tasks, in the order they should be done

### T1 — Metrics collector *(do first)*

Walk `publish_log.jsonl`, call `get_metrics` for every post that supports it, append a dated
snapshot to a store next to the drafts. Run it daily.

It comes first because it only starts producing data from the day it runs: every day of delay is
a day missing from any future case study.

*Done when:* each published post has a series of dated snapshots; a provider without metrics is
skipped rather than failing the run; a failed platform does not abort the others; tested against
mocked responses.

### T2 — Instagram token refresh

`InstagramProvider` reads `INSTAGRAM_ACCESS_TOKEN` and never refreshes it. Meta's long-lived
tokens last 60 days and are extended by an explicit `ig_refresh_token` call. The current token was
issued 2026-10-01, so publishing breaks around **2026-11-30** — and `is_configured()` will still
report `True`, because it only checks that the variable is set.

Port the logic from `swd07/boomi-ig` → `token_manager.py`: it stores the token with its issue date,
refreshes when older than 24h, writes atomically, and already handles the quirk that a dashboard
token is long-lived and must *not* be exchanged (`ig_exchange_token` → "Session key invalid 452").

*Done when:* a token older than a day is refreshed before use; the stored copy survives a crash
mid-write; an expired token is reported as not configured instead of failing at publish time.

### T3 — Media from a local file

Instagram and the other media platforms download the file themselves, so every post currently
needs a public HTTPS URL and images are placed in `swd07.github.io/assets/` by hand. This is the
practical bottleneck of the whole pipeline.

Two routes already available: publish to the GitHub Pages repository, or MinIO with a public
endpoint (already used by `boomi-ig` for Reels).

*Done when:* `social_preview` accepts a local path, the file is uploaded, and the resulting public
URL is what goes to the platform.

### T4 — Weekly report

A summary over the snapshots from T1: what was published, how each post developed, which formats
differ. Keep it descriptive. On the volume of a personal account these are observations, not
findings, and the report must not imply statistical significance it does not have.

### T5 — Threads and Facebook Page

Same Meta app (`boomi-agent`, Instagram App ID `1315827600044942`). Issue the two token pairs and
run one real post through each.

### T6 — Comment handling behind approval

`swd07/boomi-ig` already exposes `/reply-comment`, and the Meta app holds
`instagram_business_manage_comments`. Replies must go through the same approval code as posts.

### T7 — Scheduling

Only after T1–T4. A scheduler that publishes while nobody is watching needs the approval question
answered differently — a pre-approved window, not a code typed at publish time.

### T8 — mcp 2.x

`requirements.txt` pins `mcp<2`: FastMCP was renamed to `MCPServer` in 2.x and the server does not
import there. Migrate deliberately, not as a side effect of a dependency bump.

## 6. Operating notes

- State lives in `~/.growthos/`: `drafts.json` (drafts, approval-code hashes, publish results) and
  `publish_log.jsonl`. Files are utf-8 and the draft store is written atomically.
- Credentials live in `.env.social` (git-ignored). `.env.social.example` lists every variable.
- `GROWTHOS_ALLOW_PUBLISH=1` is the switch that lets anything leave the machine. Leave it at `0`
  between sessions.
- **Windows:** the committed `.mcp.json` says `python3`, which is the Microsoft Store stub there.
  Point the command at `.venv\Scripts\python.exe` locally and do not commit that edit.

## 7. Rules that are not negotiable

1. **The approval code comes from the human.** `social_preview` returns it so a person can read the
   draft and send it back. An agent filling it in by itself turns the mechanism back into a comment.
2. **Never log the bot token.** The Telegram API carries it in the URL and httpx logs URLs at INFO;
   the `httpx` logger is pinned to WARNING for this reason. Do not raise it.
3. **Content is agreed before a draft is made.** A previewed draft with a code reads as a decision
   already taken. Discuss what goes out first, then preview.
4. **Say which half works.** Publishing with approval is proven; analytics is not built. Do not
   describe the full loop as if it exists.
