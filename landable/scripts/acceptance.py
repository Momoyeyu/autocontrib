#!/usr/bin/env python3
"""Probe a repository's openness to external contributors.

Samples recent merged PRs via `gh` and reports the share by author
association. A repo where NONE/CONTRIBUTOR PRs get merged accepts outsiders;
a repo where only MEMBER/OWNER merge is de-facto closed.

Requires the GitHub CLI (`gh`) authenticated. Stdlib otherwise.

Usage:
    acceptance.py --repo OWNER/NAME [--limit 40]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter

_EXTERNAL = {"NONE", "CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER"}
_INSIDER = {"MEMBER", "OWNER", "COLLABORATOR"}


def merged_prs(repo: str, limit: int) -> list[dict]:
    out = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page={limit}",
        ],
        capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "gh api failed")
    pulls = json.loads(out.stdout or "[]")
    return [
        {
            "authorAssociation": pr.get("author_association"),
            "title": pr.get("title"),
            "mergedAt": pr.get("merged_at"),
        }
        for pr in pulls
        if pr.get("merged_at")
    ]


def classify(prs: list[dict]) -> dict:
    """Tally authorAssociation and compute the external merge share."""
    counts: Counter = Counter()
    external_titles: list[str] = []
    for pr in prs:
        assoc = pr.get("authorAssociation") or "NONE"
        counts[assoc] += 1
        if assoc in _EXTERNAL:
            external_titles.append(pr.get("title", ""))
    total = len(prs)
    external = sum(counts[a] for a in _EXTERNAL)
    insider = sum(counts[a] for a in _INSIDER)
    return {
        "total": total,
        "external": external,
        "insider": insider,
        "external_share": (external / total) if total else 0.0,
        "counts": dict(counts),
        "external_titles": external_titles,
    }


def verdict(stats: dict) -> str:
    if stats["total"] == 0:
        return "no merged PRs sampled — judge by issue responsiveness instead"
    if stats["external_share"] >= 0.2:
        return "open — external PRs merge regularly"
    if stats["external"] > 0:
        return "conditional — rare external merges; prefer maintainer-specified issues"
    return "closed — no external merges in sample; deprioritize"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, help="OWNER/NAME")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args(argv)

    try:
        stats = classify(merged_prs(args.repo, args.limit))
    except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"probe failed: {e}", file=sys.stderr)
        return 1

    print(f"{args.repo}: {stats['external']}/{stats['total']} merged PRs from external authors")
    for assoc, n in sorted(stats["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {assoc:<22} {n}")
    print(f"verdict: {verdict(stats)}")
    if stats["external_titles"]:
        print("recent external merges:")
        for t in stats["external_titles"][:5]:
            print(f"  - {t[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
