# Implement

Read when the human has picked issues. Implement produces tested local branches — nothing is pushed.

## Fork, clone, claim

1. `gh repo fork` if needed; clone the **upstream** repo over SSH, then add the fork as a `fork` remote. SSH avoids HTTPS proxy/framing failures on some networks.
2. Branch from the correct base (`develop` vs `main` per the rules file), named `fix/…` or `feat/…` in the repo's style.
3. **Claim the issue with a comment** — one or two lines in the repository's primary language, stating intent and rough approach. Keep it boring; maintainers skim.

## Fix like a repo native

- Read the target file's docstring and adjacent implementations before editing. Find the **root cause** first; a patch that treats symptoms gets reverted in review.
- Write the regression test first when practical. Never make tests depend on live network or API keys — fake the client boundary.
- Keep the diff surgical. No drive-by cleanup, no unrelated formatting, no abstractions the codebase doesn't have.
- Respect the repo's own conventions for error handling, naming, units, and data semantics. For data-mapping work, verify field semantics against real output before mapping — a plausible-looking wrong mapping is worse than a missing one.
- Run the repo's documented gates: its own test runner invocation, lint, format, typecheck — not your defaults.
- If `uv run`/`npm`/build tooling rewrites lockfiles unrelated to your change, revert those hunks before committing.

## Commits and voice

- Match the log's commit style (`git log --oneline -10`): conventional prefix, language, capitalization.
- Honor signing requirements: `-s` sign-off, `-S` cryptographic signing where the repo demands it. If no signing key is configured on the machine, say so and let the human amend — never weaken a repo's stated requirements quietly.
- **No tool attribution anywhere**: no generated-by footers, no AI co-author trailers, no agent branding in commit messages, issue comments, or PR bodies. Write like a human contributor: short, technical, on-topic.
- PR-facing text goes in the repository's primary language (the README's language), fills the repo's PR template honestly, and states only what changed, why, and what was actually run.

## Stop at the patch list

When all picked issues are done, present the review list: per change — repo, issue, branch, files changed, what it does in one line, tests run and results, and known limitations. Then stop. Pushing is Ship's job and requires explicit approval.
