# Scout

Read when discovering candidate repositories. Scout turns the user's interests plus GitHub Trending into a short ranked list — nothing is assessed or forked here yet.

## Build the interest profile first

Read the user's stated source of interests (blog, site, pinned repos, resume). Compress it into an interest card: **domains** (e.g. inference optimization, agents), **languages**, and **preferred layer** (kernel/infra/library/app). Domains rank above languages — a perfect-language project in an alien domain is a weak target.

Also build a **capability card**: what hardware/compute the user actually has (GPU? CUDA or Apple Silicon only? remote boxes? laptop only?). Assess filters issues against this — ask once, here, not mid-pipeline.

If the user supplies no source, ask once for a link or a short interest list plus the resource line. Do not guess.

## Pull trending candidates

Fetch **both** daily and weekly GitHub Trending (`https://github.com/trending` and `?since=weekly`), optionally per-language. `scripts/trending.py` does this and filters by star ceiling:

```bash
python3 landable/scripts/trending.py --weekly --max-stars 10000
python3 landable/scripts/trending.py --lang python
```

If the fetch fails (network, markup drift), retry once; then fall back to `gh search repos "created:>YYYY-MM-DD" --sort stars` over recently-active repos and say so.

## Filter and rank

Apply the star ceiling (default 10,000) — above it, contributor circles are usually already set. Then rank by interest match, giving each candidate a one-line rationale tied to the interest card, not a generic "it's popular".

Flag for the user, don't silently drop:

- **Just over the ceiling** — worth a mention as "watch list", clearly marked.
- **Very young / low stars** — higher early-contributor leverage, higher abandonment risk.
- **Stack mismatch** — e.g. JavaScript when the card says systems Python/C++; still list it, marked low-fit.

## Present, then stop

End Scout with a ranked table: project, stars, language, fit score, one-line why. Then present a **blocking choice** — which candidates to carry into Assess (offer "all / picks / none / adjust criteria") — and wait for the answer. Do not fork, clone, or open issues yet.
