# Assess

Read when judging whether a candidate repository actually accepts external work, and which issues are worth claiming. Assess ends with the human picking issues — not with implementations.

## Collect the digest first

```bash
python3 landable/scripts/probe.py --repo OWNER/NAME
```

One GraphQL call returns the mechanical half of assessment: repo meta (stars, default branch, archived, last push), rules-file presence with extracted hint lines (DCO, signing, test gates), the merged-PR author mix, insider-reply share on recent closed issues, and a triage row per open issue — labels, age, comment count, assignee, timeline-linked PRs, soft-claim phrases — each with a `free`/`check`/`taken` verdict plus a body excerpt for the survivors.

Read the digest, not the raw tracker. Fetch more only where the digest is thin: `--dump-rules` for the full CONTRIBUTING text, `gh issue view` for a finalist's full body, a deeper timeline page if a hot issue has more events than the probe sampled. `--json` for programmatic reading.

From it, record:

- **Base branch** for PRs (default branch plus any hint line — e.g. `develop`, not always `main`).
- **Commit requirements** — DCO sign-off (`-s`), cryptographic signing (`-S`), conventional-commit style.
- **Ship bar** — the documented test/lint gate (`make all`, `uv run pytest`, pre-commit).
- **Changelog** — whether the repo maintains one and expects entries.
- **Plugin/extension contracts** — documented interfaces beat reading tea leaves.

Acceptance reads as:

- **NONE / CONTRIBUTOR merges present** → genuinely open to outsiders.
- **All MEMBER / OWNER** → closed or de-facto single-author; deprioritize.
- **Very few PRs at all** → lean on the responsiveness line instead.

Fast claiming (many `taken` rows, quick turnover) means good issues disappear quickly — note it for the user.

## Triage issues — three hard filters

An issue only enters the shortlist if it passes **all three**. These are gates, not preferences — drop it the moment one fails.

### 1. Worth doing

- A real defect or missing feature that users actually hit; labeled `bug` / `feature` / `good first issue` helps but isn't required.
- Sized for one PR — under a few hundred changed lines.
- Skip: Q&A threads, usage questions, meta tasks (verify-list, docs wishes), and feature requests that read as self-promotion for the author's own tool/spec — these close as "thanks" or rot, not merge.
- Bonus signals: **root-caused already** (a maintainer comment naming the faulty file/line turns research risk into implementation work); **contract-specified** (the maintainer wrote the expected interface or test shape).

### 2. Unclaimed — the digest checks the channels

`probe.py` already pulls the three signals: assignees, timeline cross-references (a linked PR counts as claimed **whether open or closed** — closed-unmerged still tells you someone tried and how it went), and claim phrasing in recent comments (`soft-claim:<user>`). Fork commit references surface as `check`.

Trust but verify on the shortlist: the probe samples the latest timeline events, so a busy issue can have older cross-references it didn't see. Before claiming a `free` finalist, one `gh api repos/{owner}/{repo}/issues/{n}/timeline` pass confirms it. An issue author saying "we have a fix on a fork, checking the approach before PR" is a claim — don't race it. Likewise a maintainer assigning it to themselves or naming who'll do it.

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
