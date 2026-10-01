#!/usr/bin/env python3
"""Collect an assessment digest for a repository in one shot.

A single `gh api graphql` call gathers the mechanical half of Assess:
repo meta, rules-file presence and hint lines, the merged-PR author mix
(the acceptance probe), maintainer responsiveness on closed issues, and
an open-issue triage table — labels, age, assignees, timeline-linked PRs,
soft-claim phrases — with a free/check/taken verdict per issue plus a
short body excerpt for the surviving ones.

The agent reads the digest instead of fetching every issue by hand.
Requires the GitHub CLI (`gh`) authenticated. Stdlib otherwise.

Usage:
    probe.py --repo OWNER/NAME [--issues 30] [--closed 10] [--prs 40]
             [--excerpt-chars 220] [--json] [--dump-rules]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys

import acceptance

_INSIDER = acceptance._INSIDER

_QUERY = """
query($owner: String!, $name: String!, $nIssues: Int!, $nClosed: Int!, $nPRs: Int!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    stargazerCount
    pushedAt
    isArchived
    primaryLanguage { name }
    defaultBranchRef { name }
    contributing:   object(expression: "HEAD:CONTRIBUTING.md")              { ... on Blob { byteSize text } }
    contributingGh: object(expression: "HEAD:.github/CONTRIBUTING.md")      { ... on Blob { byteSize text } }
    agents:         object(expression: "HEAD:AGENTS.md")                    { ... on Blob { byteSize } }
    prTemplate:     object(expression: "HEAD:.github/PULL_REQUEST_TEMPLATE.md") { ... on Blob { byteSize } }
    mergedPRs: pullRequests(first: $nPRs, states: MERGED,
                            orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { authorAssociation title }
    }
    closedIssues: issues(last: $nClosed, states: CLOSED) {
      nodes {
        number
        comments(last: 15) { nodes { authorAssociation } }
      }
    }
    openIssues: issues(first: $nIssues, states: OPEN,
                       orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number title createdAt updatedAt bodyText
        authorAssociation
        labels(first: 8) { nodes { name } }
        comments { totalCount }
        assignees(first: 3) { nodes { login } }
        timelineItems(first: 25,
                      itemTypes: [CROSS_REFERENCED_EVENT, CONNECTED_EVENT, REFERENCED_EVENT]) {
          nodes {
            __typename
            ... on CrossReferencedEvent { source { __typename ... on PullRequest { number state } } }
            ... on ConnectedEvent       { subject { __typename ... on PullRequest { number state } } }
            ... on ReferencedEvent      { commitRepository { nameWithOwner isFork } }
          }
        }
        lastComments: comments(last: 5) {
          nodes { author { login } authorAssociation bodyText }
        }
      }
    }
  }
}
"""

_CLAIM_RE = re.compile(
    r"(i'?ll\b.{0,30}(fix|work|take|handle|look)|i'?m (on it|working)|"
    r"working on (this|it)|on it\b|pr (coming|soon|shortly)|"
    r"will (open|submit|send|make|file) a pr|assign (me|this to me)|"
    r"i'?d like to (work|take|fix)|let me (take|fix|handle)|"
    r"我来|认领|我来修|我在修|交给我|已在.*修复|fix.*已在)",
    re.I,
)

_RULE_HINTS = [
    (re.compile(r"signed-off-by|sign[- ]?off|\bDCO\b", re.I), "DCO sign-off"),
    (re.compile(r"\bgpg\b|signed commits?|cryptographic", re.I), "commit signing"),
    (re.compile(r"conventional commits?", re.I), "conventional-commit style"),
]
_RULE_LINE_RE = re.compile(
    r"(base branch|target branch|against `?(develop|dev|main|master)|"
    r"pytest|make |npm (test|run)|uv run|cargo test|go test|pre-commit|ruff|tox)",
    re.I,
)


def rules_signals(text: str) -> tuple[list[str], list[str]]:
    """Extract compliance hints and the raw lines worth quoting."""
    hints = [label for pat, label in _RULE_HINTS if pat.search(text)]
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln and _RULE_LINE_RE.search(ln) and ln not in lines:
            lines.append(ln[:140])
    return hints, lines[:6]


def maintainer_response_share(closed_nodes: list[dict]) -> tuple[int, int]:
    """Closed issues that got at least one insider comment."""
    replied = 0
    for n in closed_nodes:
        comments = (n.get("comments") or {}).get("nodes") or []
        if any(c.get("authorAssociation") in _INSIDER for c in comments):
            replied += 1
    return replied, len(closed_nodes)


def issue_signals(node: dict, repo_full: str) -> tuple[list[str], str]:
    """Claim signals and a free/check/taken verdict for one open issue."""
    flags: list[str] = []
    taken = False
    weak = False

    assignees = (node.get("assignees") or {}).get("nodes") or []
    if assignees:
        flags.append("assigned:" + ",".join(a["login"] for a in assignees))
        taken = True

    for ev in (node.get("timelineItems") or {}).get("nodes") or []:
        src = ev.get("source") or ev.get("subject") or {}
        if src.get("__typename") == "PullRequest" and src.get("number"):
            flags.append(f"linked-pr:#{src['number']}:{(src.get('state') or '').lower()}")
            taken = True
        cr = ev.get("commitRepository")
        if cr and (cr.get("isFork") or cr.get("nameWithOwner") != repo_full):
            flags.append("ref-commit:" + (cr.get("nameWithOwner") or "?"))
            weak = True

    for c in (node.get("lastComments") or {}).get("nodes") or []:
        if _CLAIM_RE.search(c.get("bodyText") or ""):
            who = (c.get("author") or {}).get("login") or "?"
            flags.append("soft-claim:" + who)
            taken = True
            break
        if c.get("authorAssociation") in _INSIDER and "maintainer-active" not in flags:
            flags.append("maintainer-active")

    verdict = "taken" if taken else ("check" if weak else "free")
    return flags, verdict


def _age_days(iso: str | None) -> str:
    if not iso:
        return "?"
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return "?"
    d = (dt.datetime.now(dt.timezone.utc) - t).days
    return f"{d}d" if d else "today"


def digest(repo: dict, excerpt_chars: int) -> dict:
    """Turn the GraphQL repository payload into a digest dict."""
    merged = [
        {"authorAssociation": pr.get("authorAssociation"), "title": pr.get("title")}
        for pr in (repo.get("mergedPRs") or {}).get("nodes") or []
    ]
    stats = acceptance.classify(merged)
    closed = (repo.get("closedIssues") or {}).get("nodes") or []
    replied, closed_total = maintainer_response_share(closed)

    rules = {}
    hints, lines = [], []
    for key in ("contributing", "contributingGh", "agents", "prTemplate"):
        blob = repo.get(key)
        rules[key] = bool(blob)
        if blob and blob.get("text"):
            h, ls = rules_signals(blob["text"])
            hints += h
            lines += ls
    hints = sorted(set(hints))

    issues = []
    for n in (repo.get("openIssues") or {}).get("nodes") or []:
        flags, verdict = issue_signals(n, repo.get("nameWithOwner") or "")
        labels = [l["name"] for l in (n.get("labels") or {}).get("nodes") or []]
        issues.append({
            "number": n.get("number"),
            "title": (n.get("title") or "")[:80],
            "labels": labels,
            "age": _age_days(n.get("createdAt")),
            "comments": (n.get("comments") or {}).get("totalCount", 0),
            "flags": flags,
            "verdict": verdict,
            "excerpt": " ".join((n.get("bodyText") or "").split())[:excerpt_chars]
                       if verdict != "taken" else "",
        })
    order = {"free": 0, "check": 1, "taken": 2}
    issues.sort(key=lambda i: order[i["verdict"]])

    return {
        "repo": repo.get("nameWithOwner"),
        "stars": repo.get("stargazerCount"),
        "language": (repo.get("primaryLanguage") or {}).get("name"),
        "default_branch": (repo.get("defaultBranchRef") or {}).get("name"),
        "archived": repo.get("isArchived"),
        "pushed": _age_days(repo.get("pushedAt")),
        "rules_files": rules,
        "rules_hints": hints,
        "rules_lines": lines[:8],
        "acceptance": {"external": stats["external"], "total": stats["total"],
                       "verdict": acceptance.verdict(stats)},
        "responsiveness": {"replied": replied, "closed_sampled": closed_total},
        "issues": issues,
    }


def print_digest(d: dict) -> None:
    rf = d["rules_files"]
    files = ", ".join(
        f"{label} {'✓' if rf[k] else '✗'}"
        for k, label in (("contributing", "CONTRIBUTING.md"),
                         ("contributingGh", ".github/CONTRIBUTING.md"),
                         ("agents", "AGENTS.md"),
                         ("prTemplate", "PR template"))
    )
    acc = d["acceptance"]
    resp = d["responsiveness"]
    pushed = d["pushed"] if d["pushed"] == "today" else f"{d['pushed']} ago"
    print(f"repo:      {d['repo']} · {d['stars']} ★ · {d['language'] or '-'} "
          f"· pushed {pushed} · archived:{d['archived']} · default:{d['default_branch']}")
    print(f"rules:     {files}")
    for h in d["rules_hints"]:
        print(f"  hint:    {h}")
    for ln in d["rules_lines"]:
        print(f"  line:    {ln}")
    print(f"accept:    {acc['external']}/{acc['total']} external merges — {acc['verdict']}")
    print(f"responses: {resp['replied']}/{resp['closed_sampled']} closed issues got insider replies")
    print("open issues (free first):")
    print(f"  {'#':<7} {'verdict':<7} {'age':<6} {'cmts':<4} {'labels':<24} flags")
    for i in d["issues"]:
        labels = ",".join(i["labels"])[:24]
        flags = "; ".join(i["flags"])[:70]
        print(f"  #{i['number']:<6} {i['verdict']:<7} {i['age']:<6} "
              f"{i['comments']:<4} {labels:<24} {flags}")
        print(f"          {i['title']}")
        if i["excerpt"]:
            print(f"          {i['excerpt']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, help="OWNER/NAME")
    ap.add_argument("--issues", type=int, default=30)
    ap.add_argument("--closed", type=int, default=10)
    ap.add_argument("--prs", type=int, default=40)
    ap.add_argument("--excerpt-chars", type=int, default=220)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dump-rules", action="store_true",
                    help="print the full CONTRIBUTING text instead of hints")
    args = ap.parse_args(argv)

    if "/" not in args.repo:
        print("--repo must be OWNER/NAME", file=sys.stderr)
        return 1
    owner, name = args.repo.split("/", 1)

    out = subprocess.run(
        ["gh", "api", "graphql",
         "-f", f"query={_QUERY}",
         "-F", f"owner={owner}", "-F", f"name={name}",
         "-F", f"nIssues={args.issues}",
         "-F", f"nClosed={args.closed}", "-F", f"nPRs={args.prs}"],
        capture_output=True, text=True, timeout=120,
    )
    if out.returncode != 0:
        print(f"gh api failed: {out.stderr.strip()}", file=sys.stderr)
        return 1
    try:
        payload = json.loads(out.stdout)
    except json.JSONDecodeError as e:
        print(f"bad graphql response: {e}", file=sys.stderr)
        return 1
    if payload.get("errors"):
        print(f"graphql errors: {payload['errors'][:2]}", file=sys.stderr)
        return 1
    repo = (payload.get("data") or {}).get("repository")
    if not repo:
        print(f"repo {args.repo} not found", file=sys.stderr)
        return 1

    if args.dump_rules:
        blob = repo.get("contributing") or repo.get("contributingGh") or {}
        print(blob.get("text") or "(no CONTRIBUTING.md)")
        return 0

    d = digest(repo, args.excerpt_chars)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print_digest(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
