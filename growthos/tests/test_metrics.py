import asyncio
import json

import pytest

from growthos.metrics.collector import collect, iter_snapshots, published_posts
from growthos.providers.social import Capabilities, ProviderError, SocialProvider


def run(coro):
    return asyncio.run(coro)


class FakeProvider(SocialProvider):
    """Minimal adapter: records how often it was asked, and can be told to fail."""

    def __init__(self, name, *, account=None, post=None, metrics_cap=True, configured=True,
                 account_cap=True):
        self.name = name
        self._account, self._post = account, post
        self._metrics_cap, self._configured = metrics_cap, configured
        self._account_cap = account_cap
        self.account_calls = self.post_calls = 0

    def is_configured(self):
        return self._configured

    def capabilities(self):
        return Capabilities(text=True, image=True, video=False, carousel=False,
                            metrics=self._metrics_cap, account_metrics=self._account_cap,
                            max_text_len=1000)

    async def publish(self, draft):  # pragma: no cover - not used here
        raise NotImplementedError

    async def get_account_metrics(self):
        self.account_calls += 1
        if isinstance(self._account, Exception):
            raise self._account
        return dict(self._account)

    async def get_metrics(self, post_id):
        self.post_calls += 1
        if isinstance(self._post, Exception):
            raise self._post
        return dict(self._post)


def _wire(monkeypatch, tmp_path, providers):
    monkeypatch.setenv("GROWTHOS_STATE_DIR", str(tmp_path))
    import growthos.metrics.collector as c
    monkeypatch.setattr(c, "PROVIDERS", tuple(providers))
    monkeypatch.setattr(c, "get_provider", lambda n: providers[n])
    return c


def _log(tmp_path, entries):
    (tmp_path / "publish_log.jsonl").write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")


def test_collects_account_and_post_snapshots(monkeypatch, tmp_path):
    ig = FakeProvider("instagram", account={"followers_count": 664, "profile_views": 49},
                      post={"reach": 120, "likes": 7})
    _wire(monkeypatch, tmp_path, {"instagram": ig})
    _log(tmp_path, [{"platform": "instagram", "post_id": "p1", "status": "published"}])

    summary = run(collect())
    kinds = {(r["kind"], r["platform"], r["subject"]) for r in summary["taken"]}
    assert kinds == {("account", "instagram", "account"), ("post", "instagram", "p1")}
    account = next(r for r in summary["taken"] if r["kind"] == "account")
    assert account["metrics"]["followers_count"] == 664
    assert account["date"] == summary["date"] and not summary["failed"]


def test_second_run_same_day_does_not_duplicate_but_force_does(monkeypatch, tmp_path):
    ig = FakeProvider("instagram", account={"followers_count": 664}, post={"reach": 1})
    _wire(monkeypatch, tmp_path, {"instagram": ig})
    _log(tmp_path, [{"platform": "instagram", "post_id": "p1", "status": "published"}])

    run(collect())
    again = run(collect())
    assert again["taken"] == [] and len(again["skipped"]) == 2
    assert len(list(iter_snapshots())) == 2

    forced = run(collect(force=True))
    assert len(forced["taken"]) == 2
    assert len(list(iter_snapshots())) == 4      # history is appended, never rewritten


def test_history_survives_across_days(monkeypatch, tmp_path):
    ig = FakeProvider("instagram", account={"followers_count": 664}, post=None, metrics_cap=False)
    _wire(monkeypatch, tmp_path, {"instagram": ig})
    run(collect(day="2026-10-01"))
    ig._account = {"followers_count": 671}
    run(collect(day="2026-10-02"))
    series = [(r["date"], r["metrics"]["followers_count"]) for r in iter_snapshots()]
    assert series == [("2026-10-01", 664), ("2026-10-02", 671)]


def test_one_failure_does_not_stop_the_others(monkeypatch, tmp_path):
    broken = FakeProvider("instagram", account=ProviderError("token expired"),
                          post=ProviderError("media deleted"))
    fine = FakeProvider("x", account={"followers": 10}, post={"impressions": 3})
    _wire(monkeypatch, tmp_path, {"instagram": broken, "x": fine})
    _log(tmp_path, [{"platform": "instagram", "post_id": "gone", "status": "published"},
                    {"platform": "x", "post_id": "ok", "status": "published"}])

    summary = run(collect())
    assert {r["platform"] for r in summary["taken"]} == {"x"}
    assert len(summary["failed"]) == 2
    assert all("token expired" in f["error"] or "media deleted" in f["error"] for f in summary["failed"])


def test_published_posts_ignores_dry_runs_and_duplicates(monkeypatch, tmp_path):
    monkeypatch.setenv("GROWTHOS_STATE_DIR", str(tmp_path))
    _log(tmp_path, [{"platform": "telegram", "post_id": "a", "status": "published"},
                    {"platform": "telegram", "post_id": "a", "status": "published"},
                    {"platform": "telegram", "post_id": "b", "status": "dry_run"},
                    {"platform": "telegram", "post_id": "c", "status": "failed"}])
    assert published_posts() == [("telegram", "a")]


def test_platform_without_post_metrics_is_skipped(monkeypatch, tmp_path):
    tg = FakeProvider("telegram", account={"members": 5}, post=None, metrics_cap=False)
    _wire(monkeypatch, tmp_path, {"telegram": tg})
    _log(tmp_path, [{"platform": "telegram", "post_id": "p1", "status": "published"}])
    summary = run(collect())
    assert [r["kind"] for r in summary["taken"]] == ["account"]
    assert tg.post_calls == 0


def test_platform_without_account_metrics_is_not_a_failure(monkeypatch, tmp_path):
    """Telegram has no account numbers; that is an absence, not an error to report."""
    tg = FakeProvider("telegram", account=None, post=None, metrics_cap=False, account_cap=False)
    _wire(monkeypatch, tmp_path, {"telegram": tg})
    summary = run(collect())
    assert summary["taken"] == [] and summary["failed"] == []
    assert tg.account_calls == 0
