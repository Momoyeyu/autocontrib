# Scout

Read when discovering candidate repositories. Scout turns the user's interests plus GitHub Trending into a short ranked list — nothing is assessed or forked here yet.

## Build the interest profile first

Interests are per-request — the user may bring a different set each run, and that input always wins. But check for a saved profile first: `~/.config/landable/profile.json` holds `domains`, `languages`, `layers`, `hardware`, `notes`. If it exists, offer it in the opening choice: **use saved profile / new interests this run / update saved**. If absent or the user supplies fresh interests, build the card from what they give — and offer to write it back to the profile for next time.

Read the user's stated source of interests (blog, site, pinned repos, resume) or the saved profile. Compress it into an interest card: **domains** (e.g. inference optimization, agents), **languages**, and **preferred layer** (kernel/infra/library/app). Domains rank above languages — a perfect-language project in an alien domain is a weak target.

Also build a **capability card**: what hardware/compute the user actually has (GPU? CUDA or Apple Silicon only? remote boxes? laptop only?). Assess filters issues against this — ask once, here, not mid-pipeline. A saved profile's `hardware` field can answer this silently.

If the user supplies no source and no saved profile exists, ask once for a link or a short interest list plus the resource line. Do not guess.

## Pick the star range

Stars are a **range**, not just a ceiling — offer preset bands and let the user pick (default `0–10,000`):

- `0–1,000` — youngest repos; highest early-contributor leverage, highest abandonment risk
- `1,000–5,000` — past the toy stage, contributor circles not yet set
- `5,000–10,000` — established but still porous
- `0–10,000` — everything under the old ceiling
- custom — user supplies both bounds

## Pull trending candidates

Fetch **both** daily and weekly GitHub Trending (`https://github.com/trending` and `?since=weekly`), optionally per-language. `scripts/trending.py` does this and filters by star range:

```bash
python3 landable/scripts/trending.py --weekly --min-stars 1000 --max-stars 5000
python3 landable/scripts/trending.py --lang python
```

If the fetch fails (network, markup drift), retry once; then fall back to `gh search repos "created:>YYYY-MM-DD" --sort stars` over recently-active repos and say so.

## Filter and rank

Apply the chosen star range. Then rank by interest match, giving each candidate a one-line rationale tied to the interest card, not a generic "it's popular".

Flag for the user, don't silently drop:

- **Just over the upper bound** — worth a mention as "watch list", clearly marked.
- **Very young / low stars** — higher early-contributor leverage, higher abandonment risk.
- **Stack mismatch** — e.g. JavaScript when the card says systems Python/C++; still list it, marked low-fit.

## Present, then stop

End Scout with a ranked table: project, stars, language, fit score, one-line why. Then present a **blocking choice** — which candidates to carry into Assess (offer "all / picks / none / adjust criteria") — and wait for the answer. Do not fork, clone, or open issues yet.
