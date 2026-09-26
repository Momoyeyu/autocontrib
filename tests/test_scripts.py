"""Parser/aggregation tests for autocontrib scripts — no network, no gh."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autocontrib" / "scripts"))

import acceptance  # noqa: E402
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
