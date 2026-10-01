# GrowthOS

An MCP server that lets Claude Code prepare, review and publish social posts — with two
independent locks between the model and your audience.

```text
you ask for a post
  → social_preview   validates it per platform, stores an immutable draft,
                     returns a one-time approval code
  → you read the draft and send the code back yourself
  → social_publish   publishes exactly that draft, and only with a matching code
```

Nothing leaves the machine unless `GROWTHOS_ALLOW_PUBLISH=1`. The approval code is separate from
that switch on purpose: the switch can stay on for a working session while the code still forces a
human decision for each post. A real publish burns the code; a dry run does not.

## Why the locks

An agent that can post is an agent that can post something you did not want, from an account people
associate with you. The usual answer is an instruction in the tool description — "only call this
after the user approves". That is a convention, not a mechanism: the model is free to decide it has
approval.

Here the approval is a value the model does not possess until a human hands it over.
`social_preview` returns a six-character code and stores only its SHA-256 hash with the draft;
`social_publish` takes the code as a required argument and refuses without a match. The MCP schema
shows it:

```text
social_publish   required=['draft_id', 'approval_code']
```

## Platforms

| Platform | Publishing | Metrics | Notes |
|---|---|---|---|
| Telegram | ✅ verified live | — | channel or chat; bot must be an admin |
| Instagram | ✅ verified live | snapshot | Professional account; media must be a public URL; video posts as a Reel |
| Facebook Page | adapter written, untested | — | needs a Page token |
| Threads | adapter written, untested | — | same Meta app as Instagram |
| X | adapter written, untested | snapshot | paid tier |
| YouTube | adapter written, untested | — | uploads stay private until Google audits the project |
| TikTok | adapter written, untested | — | lands in the app's inbox as a draft; public posting needs review |
| Reddit | assisted | — | returns a prefilled submit link for a human to post |

"Verified live" means a real post went out through this code. The rest pass unit tests against
mocked HTTP and have never seen a credential. The difference matters, so it is stated rather than
blurred.

## What is not built

Metrics are fetched as a snapshot and stored nowhere, so "which post worked" has no answer yet.
There is no scheduling, no reporting, and media has to be a public HTTPS URL rather than a local
file. The plan, in order, is in [docs/plans/2026-10-01-growthos-social-status.md](docs/plans/2026-10-01-growthos-social-status.md).

## Quick start

```bash
git clone https://github.com/swd07/growthos && cd growthos
python -m venv .venv && .venv/bin/pip install -r growthos/requirements.txt
cp .env.social.example .env.social     # fill in one platform; Telegram takes ~10 minutes
claude                                  # Claude Code picks up .mcp.json
```

On Windows `python3` in `.mcp.json` is usually the Microsoft Store stub — point the command at
`.venv\Scripts\python.exe` locally. Per-platform credentials are walked through in
[docs/setup/social-accounts.md](docs/setup/social-accounts.md), and the provider contract is in
[docs/specs/social-provider-interface.md](docs/specs/social-provider-interface.md).

```bash
.venv/bin/python -m pytest growthos/tests -q     # 13 tests
```

## State

Secrets live in `.env.social`, which is git-ignored; nothing in this repository holds a credential.
Drafts, approval-code hashes and the publish log live in `~/.growthos/`, written as utf-8 and
replaced atomically so a failed write cannot destroy them.

## License

No license yet — all rights reserved. Open an issue if you want to use it.
