# Connecting social accounts to Claude Code (GrowthOS social MCP)

Everything below is done once, on your own computer, with your own accounts.
Tokens go into `.env.social` (git-ignored). Start with Telegram — it works in 10 minutes.

## 0. Install and connect to Claude Code

```bash
git clone https://github.com/swd07/growthos && cd growthos
git checkout feat/social-integrations
python3 -m pip install -r growthos/requirements.txt
cp .env.social.example .env.social
python3 -m pytest growthos/tests -q        # should pass
claude                                      # Claude Code picks up .mcp.json, approve "growthos-social"
```

**On Windows:** `.mcp.json` ships with `"command": "python3"`, which works on macOS and
Linux. On Windows `python3` is usually the Microsoft Store stub rather than an interpreter,
and the system Python has none of the dependencies. Create a virtual environment in the
checkout and point the server at it — keep that edit local, do not commit it:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r growthos/requirements.txt
```

Then in `.mcp.json` replace the command with the full path to that interpreter, e.g.
`C:\path\to\repo\.venv\Scripts\python.exe` (JSON needs the backslashes doubled).
epo\.venv\Scripts\python.exe` (JSON needs the backslashes doubled).

Inside Claude Code: `/mcp` shows the server; ask "list social platforms".
Publishing is a dry run until you set `GROWTHOS_ALLOW_PUBLISH=1` in `.env.social`.

Even with that switch on, nothing is published until you send back the **approval code**:
`social_preview` shows a 6-character code, and `social_publish` refuses to run without it.
The code works once — after a real publish it is dead, and a new preview is needed.

## 1. Telegram — ~10 min, free, no review

1. In Telegram open @BotFather → `/newbot` → copy the token → `TELEGRAM_BOT_TOKEN`.
2. Create a channel (or use yours), add the bot as **administrator** with "Post messages".
3. `TELEGRAM_CHANNEL_ID=@channel_username` (for a private channel use the numeric `-100…` id).

## 2. Instagram + Facebook + Threads — ~1 hour, free, no review for your own accounts

1. Switch Instagram to a **Professional** account (Creator or Business). For Facebook you need a **Page**.
2. developers.facebook.com → Create App → use case "Manage messaging & content on Instagram"
   (Instagram Login) and add the "Threads API" use case; add Facebook Login for Pages if you post to a Page.
3. Keep the app in **Development mode**. App roles → add your Instagram / Threads accounts as **testers**,
   accept the invitations in the apps' settings.
4. Generate tokens in the app dashboard (Instagram: "Generate access token"; Threads: User Token Generator;
   Page token via Graph API Explorer with `pages_manage_posts`). Exchange for **long-lived** tokens (60 days).
5. Fill `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN`, `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN`,
   `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_TOKEN`.
6. Media must be public HTTPS URLs (e.g. a public bucket or your GitHub Pages site).
7. Calendar a reminder: long-lived tokens expire after ~60 days.

## 3. X — ~30 min, paid per post

1. developer.x.com → create a Project + App → User authentication settings: OAuth 2.0,
   type "Native App" (public client), callback `http://127.0.0.1:8765/callback`,
   permissions Read and Write.
2. Add credits (pay-per-use: ≈$0.015 per post, ≈$0.20 if the post has a link).
3. `X_CLIENT_ID=…` in `.env.social`, then `python3 -m growthos.scripts.social_auth x` → paste `X_REFRESH_TOKEN`.

## 4. YouTube — ~30 min setup, public uploads after audit

1. console.cloud.google.com → new project → enable "YouTube Data API v3".
2. OAuth consent screen (External, add yourself as test user) → Credentials → OAuth client "Desktop app".
3. Fill `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, run
   `python3 -m growthos.scripts.social_auth youtube` → paste `YOUTUBE_REFRESH_TOKEN`.
4. Until the **YouTube API Services Audit** is approved, every upload is private. Submit the
   "Audit and Quota Extension Form" now; then set `YOUTUBE_PROJECT_AUDITED=1`.

## 5. TikTok — drafts now, public posting after audit

1. developers.tiktok.com → create app → add Content Posting API, scopes `video.upload`
   (and later `video.publish`), verify the domain that hosts your videos (needed for PULL_FROM_URL).
2. Obtain a user access token via Login Kit → `TIKTOK_ACCESS_TOKEN`.
3. Default `TIKTOK_MODE=inbox`: the video lands in your TikTok inbox, you finish the post in the app.
4. Apply for the audit to enable Direct Post with public visibility.

## 6. Reddit — assisted mode

Self-serve API keys are closed. GrowthOS prepares a prefilled submit link; you check the subreddit
rules and publish yourself, then Claude records the URL (`social_record_manual`).
If you want automation later, file a Data Access Request (2–4 weeks, may be refused).

## Typical session in Claude Code

> "Подготовь пост о моём проекте распознавания полок для Telegram, Threads и X, покажи превью."
> → `social_preview` → you read the draft and the approval code, e.g. `a3f9c1`
> → "публикуй в Telegram и Threads, код a3f9c1"
> → `social_publish(draft_id, "a3f9c1", ["telegram","threads"])`

If you do not repeat the code, publishing fails — that is the point. Treat the code as the
moment you take responsibility for the post.
