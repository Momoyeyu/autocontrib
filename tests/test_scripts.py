"""Parser/aggregation tests for landable scripts — no network, no gh."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "landable" / "scripts"))

import acceptance  # noqa: E402
import probe  # noqa: E402
import trending  # noqa: E402

_SAMPLE_ROW = """
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/Owner/some-repo" data-hydro-click="{}">Owner / some-repo</a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">A useful description here.</p>
  <div class="f6 color-fg-muted mt-2">
    <span itemprop="programmingLanguage">Python</span>
    <a href="/Owner/some-repo/stargazers">4,563</a>
    <a href="/Owner/some-repo/forks">210</a>
    <span>359 stars today</span>
  </div>
</article>
"""


def test_parse_trending_extracts_repo_fields():
    rows = trending.parse_trending(f"<html><body>{_SAMPLE_ROW}</body></html>")
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "Owner/some-repo"
    assert r["lang"] == "Python"
    assert r["stars"] == 4563
    assert "useful description" in r["desc"]


def test_parse_trending_skips_non_repo_blocks():
    rows = trending.parse_trending("<article><h2><a href='/sponsors'>x</a></h2></article>")
    assert rows == []


def test_num_handles_commas_and_k_suffix():
    assert trending._num("1,234") == 1234
    assert trending._num("1.2k") == 1200
    assert trending._num("") is None
    assert trending._num("stars") is None


def test_classify_external_share():
    prs = [
        {"authorAssociation": "NONE", "title": "ext1"},
        {"authorAssociation": "CONTRIBUTOR", "title": "ext2"},
        {"authorAssociation": "MEMBER", "title": "int1"},
        {"authorAssociation": "OWNER", "title": "int2"},
    ]
    stats = acceptance.classify(prs)
    assert stats["total"] == 4
    assert stats["external"] == 2
    assert stats["insider"] == 2
    assert stats["external_share"] == 0.5
    assert stats["external_titles"] == ["ext1", "ext2"]


def test_verdict_thresholds():
    assert "open" in acceptance.verdict({"total": 10, "external": 3, "external_share": 0.3})
    assert "conditional" in acceptance.verdict({"total": 10, "external": 1, "external_share": 0.1})
    assert "closed" in acceptance.verdict({"total": 10, "external": 0, "external_share": 0.0})
    assert "no merged" in acceptance.verdict({"total": 0, "external": 0, "external_share": 0.0})


def test_in_star_range():
    assert trending.in_star_range(0, 0, 10000)
    assert trending.in_star_range(5000, 1000, 5000)
    assert not trending.in_star_range(5001, 1000, 5000)
    assert not trending.in_star_range(999, 1000, 5000)
    assert trending.in_star_range(None, 0, 10000)


def _issue(assignees=(), timeline=(), comments=()):
    return {
        "assignees": {"nodes": [{"login": a} for a in assignees]},
        "timelineItems": {"nodes": list(timeline)},
        "lastComments": {"nodes": list(comments)},
    }


def test_issue_signals_free():
    flags, verdict = probe.issue_signals(_issue(), "o/r")
    assert verdict == "free"
    assert flags == []


def test_issue_signals_taken_by_assignee_or_linked_pr():
    _, v = probe.issue_signals(_issue(assignees=["alice"]), "o/r")
    assert v == "taken"
    ev = {"source": {"__typename": "PullRequest", "number": 5, "state": "OPEN"}}
    flags, v = probe.issue_signals(_issue(timeline=[ev]), "o/r")
    assert v == "taken"
    assert any("linked-pr:#5:open" in f for f in flags)


def test_issue_signals_soft_claim_comment():
    c = {"author": {"login": "bob"}, "authorAssociation": "NONE",
         "bodyText": "I'll work on a fix this week"}
    flags, v = probe.issue_signals(_issue(comments=[c]), "o/r")
    assert v == "taken"
    assert any(f.startswith("soft-claim:bob") for f in flags)


def test_issue_signals_fork_ref_is_check():
    ev = {"commitRepository": {"nameWithOwner": "someone/r-fork", "isFork": True}}
    flags, v = probe.issue_signals(_issue(timeline=[ev]), "o/r")
    assert v == "check"
    assert any(f.startswith("ref-commit:") for f in flags)


def test_maintainer_response_share():
    closed = [
        {"comments": {"nodes": [{"authorAssociation": "MEMBER"}]}},
        {"comments": {"nodes": [{"authorAssociation": "NONE"}]}},
        {"comments": {"nodes": []}},
    ]
    assert probe.maintainer_response_share(closed) == (1, 3)


def test_rules_signals_extracts_hints_and_lines():
    text = ("# Contributing\nSign-off required via DCO.\n"
            "Run `uv run pytest tests/` before pushing.\n"
            "Open PRs against `develop`, not main.\n")
    hints, lines = probe.rules_signals(text)
    assert "DCO sign-off" in hints
    assert any("develop" in ln for ln in lines)
    assert any("pytest" in ln for ln in lines)
