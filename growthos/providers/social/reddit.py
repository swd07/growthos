"""Reddit in assisted mode.

Since late 2025 Reddit closed self-serve API keys: every external app needs
a manually reviewed Data Access Request (2-4 weeks, may be refused). Until
GrowthOS has an approved app, the adapter prepares a ready-to-submit link and
the human publishes, which also matches Reddit's own rules on automation.
After publishing, record the final URL with `social_record_manual`.
"""

from __future__ import annotations

from urllib.parse import urlencode

from .base import Capabilities, PostDraft, PublishResult, PublishStatus, SocialProvider


class RedditAssistedProvider(SocialProvider):
    name = "reddit"

    def capabilities(self) -> Capabilities:
        return Capabilities(image=False, video=False, metrics=False, max_text_len=40000,
                            notes="Assisted mode: opens a prefilled submit page, you publish manually.")

    def is_configured(self) -> bool:
        return True

    def validate(self, draft: PostDraft) -> list[str]:
        problems = super().validate(draft)
        if not draft.target:
            problems.append("reddit needs target = subreddit name (without r/)")
        if not draft.title:
            problems.append("reddit needs a title")
        return problems

    async def publish(self, draft: PostDraft) -> PublishResult:
        sub = (draft.target or "").removeprefix("r/")
        if draft.link:
            q = {"title": draft.title, "url": draft.link}
        else:
            q = {"title": draft.title, "selftext": "true", "text": draft.text}
        url = f"https://www.reddit.com/r/{sub}/submit?{urlencode(q)}"
        return PublishResult(platform=self.name, status=PublishStatus.MANUAL_REQUIRED, url=url,
                             detail="Open the link, check the subreddit rules, publish, then record the post URL.")
