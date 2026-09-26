# Assess

Read when judging whether a candidate repository actually accepts external work, and which issues are worth claiming. Assess ends with the human picking issues — not with implementations.

## Read the rules files first

Before touching code, read `CONTRIBUTING.md`, `AGENTS.md`, the PR template, and the README. Extract and record:

- **Base branch** for PRs (e.g. `develop`, not always `main`).
- **Commit requirements** — DCO sign-off (`-s`), cryptographic signing (`-S`), conventional-commit style.
- **Ship bar** — the documented test/lint gate (`make all`, `uv run pytest`, pre-commit).
- **Changelog** — whether the repo maintains one and expects entries.
- **Plugin/extension contracts** — documented interfaces beat reading tea leaves.

## Probe acceptance odds

A project's merge history tells you whether PRs from strangers land:

```bash
python3 autocontrib/scripts/acceptance.py --repo OWNER/NAME
```

It samples recent merged PRs and reports the share by `authorAssociation`. Read it as:

- **NONE / CONTRIBUTOR merges present** → genuinely open to outsiders.
- **All MEMBER / OWNER** → closed or de-facto single-author; deprioritize.
- **Very few PRs at all** → look at issue responsiveness instead.

Also check whether external contributors' issues/comments get maintainer replies, and whether anyone outside the org has claimed issues recently (fast claiming means good issues disappear quickly — note it).

## Triage issues

Prefer issues that are:

- **Unclaimed** and labeled `bug` / `feature` / `good first issue`;
- **Root-caused already** — a maintainer comment naming the faulty file/line converts research risk into implementation work;
- **Contract-specified** — the maintainer wrote the expected interface or test shape;
- **Sized for one PR** — under a few hundred changed lines.

Avoid:

- **Already-claimed** issues — comment races waste everyone's time;
- **Security-model redesigns** spanning unclear boundaries — write a proposal comment for maintainer direction instead of implementing blind;
- **Issues whose fix lives in another repository** without checking — follow imports and dependency declarations; the PR may belong upstream of the reported repo;
- **Bugs you cannot reproduce** and features you cannot test.

## Deliverable

End Assess with a shortlist per repo: issue link, what it is, effort (small/medium), your confidence you can finish it end-to-end (fork → code → tests), and the repo's acceptance signal. The human picks; only then enter Implement.
