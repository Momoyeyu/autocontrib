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
python3 landable/scripts/acceptance.py --repo OWNER/NAME
```

It samples recent merged PRs and reports the share by `authorAssociation`. Read it as:

- **NONE / CONTRIBUTOR merges present** → genuinely open to outsiders.
- **All MEMBER / OWNER** → closed or de-facto single-author; deprioritize.
- **Very few PRs at all** → look at issue responsiveness instead.

Also check whether external contributors' issues/comments get maintainer replies, and whether anyone outside the org has claimed issues recently (fast claiming means good issues disappear quickly — note it).

## Triage issues — three hard filters

An issue only enters the shortlist if it passes **all three**. These are gates, not preferences — drop it the moment one fails.

### 1. Worth doing

- A real defect or missing feature that users actually hit; labeled `bug` / `feature` / `good first issue` helps but isn't required.
- Sized for one PR — under a few hundred changed lines.
- Skip: Q&A threads, usage questions, meta tasks (verify-list, docs wishes), and feature requests that read as self-promotion for the author's own tool/spec — these close as "thanks" or rot, not merge.
- Bonus signals: **root-caused already** (a maintainer comment naming the faulty file/line turns research risk into implementation work); **contract-specified** (the maintainer wrote the expected interface or test shape).

### 2. Unclaimed — check all three channels

Silent threads lie. Before calling an issue free:

- **Timeline cross-references**: `gh api repos/{owner}/{repo}/issues/{n}/timeline` — a cross-referenced PR counts as claimed **whether open or closed** (closed-unmerged still tells you someone tried and how it went). People open PRs without ever commenting on the issue.
- **Search**: `gh pr list -R owner/repo --search "#N" --state all` as backup.
- **Soft claims in the body/comments**: an issue author saying "we have a fix on a fork, checking the approach before PR" is a claim — don't race it. Likewise a maintainer assigning it to themselves or naming who'll do it.

### 3. Feasible on *this* user's setup

- **Ask for resource constraints up front** if not already stated: GPU? CUDA or Apple Silicon only? SSH boxes? Budget for paid runners? A perfect issue needing an NVIDIA GPU is not feasible for a Mac-only contributor.
- **Honest confidence check**: can *you* implement AND verify this end-to-end — write the patch, reproduce the bug/behavior, run it — on the available hardware? A fix you cannot test is a fix you cannot ship; record confidence (high/med/low) per shortlisted issue.
- The fix may live in another repository — follow imports/dependency declarations; the PR may belong upstream of the reported repo.
- Bugs you cannot reproduce and features you cannot test are out.

Avoid regardless:

- **Security-model redesigns** spanning unclear boundaries — write a proposal comment for maintainer direction instead of implementing blind.

## Verify feasibility before claiming

Do not post the claim comment until the local groundwork is done: clone the
repo, locate the code path named in the issue, and confirm the environment can
build/test the change (or a faithful harness exists — e.g. a fake-boundary test
when the real dependency needs hardware you lack). Claiming first and
discovering a blocker later leaves a dead claim on someone else's tracker.

## Deliverable

End Assess with a shortlist per repo: issue link, what it is, effort (small/medium), confidence you can finish it end-to-end on the user's hardware (fork → code → tests), and the repo's acceptance signal. Issues that failed a hard filter may be listed in a "rejected" section with the reason — useful context, clearly marked. Then present the shortlist as a **blocking choice** ("pursue: which?") and stop. Only after the human picks, enter Implement.
