---
name: landable
description: An interest-driven open-source contribution pipeline. Profile the user's technical interests, scout GitHub Trending for under-the-radar repositories, assess real contribution openings and acceptance odds, then claim, implement, review, and ship PRs — with the human deciding what to pursue and what to publish.
---

# landable

Find repositories worth joining early, turn approachable issues into merged PRs, and keep the human in control of the two decisions that matter: **what to work on** and **what to publish**.

Works with agents that load `SKILL.md`, the GitHub CLI (`gh`), and a git checkout per target repository.

## Why landable exists

Trending rank is not contribution fitness. A promising project can still be a bad fit: owner-only merge history, hardened review gates, no scoped issues, or a stack mismatch. landable exists to **spend effort only where a PR can plausibly land** — and to keep contribution artifacts (comments, commits, PR text) indistinguishable from a competent human contributor's.

## Profile → Scout → Assess → Implement → Ship → Track

| Stage | Produces | Human decides |
|---|---|---|
| **Profile** | interest card: domains, languages, layer (kernel/infra/app); capability card: available hardware/compute | source of interests + resource constraints |
| **Scout** | ranked candidates in the star range | which candidates to assess |
| **Assess** | per-repo acceptance evidence + feasible issues | which issues to pursue |
| **Implement** | local branches: fix + regression test + draft PR text | approve / adjust each patch |
| **Ship** | pushed branches, PRs on the correct base branch | — |
| **Track** | CI status, failure root cause, review replies | escalations |

## Stage gates are blocking

Every stage ends by **presenting a choice and stopping** — a plain-text summary that lets the conversation drift forward is not a gate. At each boundary:

1. Emit the stage deliverable (table or list).
2. Offer an explicit menu — e.g. "assess: all / picks / none", "pursue these issues: which?", "ship: approve / adjust / drop" — using the host agent's multiple-choice mechanism when one exists.
3. **Wait.** Do not start the next stage until the human answers.

Hard gates on top of that: nothing is implemented before the human picks issues; nothing is pushed before the human reviews the patch list. Claiming an issue (a comment) is allowed inside Implement — but only after the feasibility check in Assess passes.

## Read only what is needed now

| Reference | Load when |
|---|---|
| [Scout](references/scout.md) | Discovering and ranking candidate repositories |
| [Assess](references/assess.md) | Judging a repo's openness and picking issues |
| [Implement](references/implement.md) | Forking, claiming, coding, committing |
| [Ship](references/ship.md) | Reviewing locally, pushing, opening PRs, tracking CI |

Do not preload the directory. Follow the current stage only.

## Scripts

`scripts/` holds small stdlib helpers; none are required for the pipeline to work.

- `scripts/trending.py` — fetch GitHub Trending (daily/weekly), filter by star range, print a ranked table.
- `scripts/probe.py` — one GraphQL call per repo: rules hints, acceptance mix, issue responsiveness, and the claimed/free triage table.
- `scripts/acceptance.py` — standalone version of probe's merged-PR author-association check.

## Defaults

- Star range **0–10,000** by default — Scout offers preset bands (0–1k / 1k–5k / 5k–10k / all / custom); window **daily + weekly** trending.
- Interests are per-request; a saved `~/.config/landable/profile.json` is offered as an option, never assumed.
- Issues already claimed by others are skipped, not raced.
- Security-model redesigns are proposed to maintainers, never implemented blind.
- Every repo's own rules win: base branch, sign-off/signing, changelog, PR template, ship bar.
- Contribution artifacts carry no tool attribution. Commits, comments, and PR bodies read like a human contributor's work in the repository's primary language.
