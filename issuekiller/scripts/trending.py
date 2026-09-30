#!/usr/bin/env python3
"""Fetch GitHub Trending and filter repositories by star ceiling.

Pure stdlib. Prints a table of full_name, language, stars, and today's/weekly
gain. The trending page is server-rendered HTML; the parser targets the
<article class="Box-row"> blocks and tolerates missing fields.

Usage:
    trending.py [--weekly] [--lang LANG] [--max-stars N] [--limit N]
"""

from __future__ import annotations

import argparse
import html.parser
import re
import sys
import urllib.request

TRENDING_URL = "https://github.com/trending"


def _num(text: str) -> int | None:
    """'4,563' -> 4563; '1.2k' -> 1200; text without digits -> None."""
    m = re.search(r"([\d.,]+)\s*(k)?", text.lower())
    if not m:
        return None
    value = float(m.group(1).replace(",", ""))
    if m.group(2):
        value *= 1000
    return int(value)


class _RowParser(html.parser.HTMLParser):
    """Extract per-repo fields from one <article> block's text + attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.in_h2 = False
        self.href = ""
        self.in_desc = False
        self.desc = ""
        self.lang = ""
        self._in_lang = False
        self.star_texts: list[str] = []
        self._in_star_link = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "h2":
            self.in_h2 = True
        elif self.in_h2 and tag == "a":
            self.href = a.get("href", "")
        elif tag == "p" and "col-9" in cls:
            self.in_desc = True
        elif a.get("itemprop") == "programmingLanguage":
            self._in_lang = True
        elif tag == "a" and a.get("href", "").endswith("/stargazers"):
            self._in_star_link = True

    def handle_endtag(self, tag):
        if tag == "h2":
            self.in_h2 = False
        elif tag == "p":
            self.in_desc = False
        elif tag == "span":
            self._in_lang = False
        elif tag == "a":
            self._in_star_link = False

    def handle_data(self, data):
        if self._in_star_link:
            self.star_texts.append(data)
        elif self._in_lang:
            self.lang += data
        elif self.in_desc:
            self.desc += data


def parse_trending(page: str) -> list[dict]:
    """Parse a trending HTML page into repo dicts."""
    articles = re.findall(r"<article\b[^>]*>(.*?)</article>", page, re.S)
    out = []
    for block in articles:
        p = _RowParser()
        p.feed(block)
        name = p.href.strip().strip("/")
        if "/" not in name:
            continue
        out.append(
            {
                "name": name,
                "lang": p.lang.strip(),
                "desc": " ".join(p.desc.split()),
                "stars": _num(" ".join(p.star_texts)),
            }
        )
    return out


def fetch(lang: str | None = None, weekly: bool = False) -> str:
    url = TRENDING_URL + (f"/{lang}" if lang else "")
    url += "?since=weekly" if weekly else "?since=daily"
    req = urllib.request.Request(url, headers={"User-Agent": "issuekiller/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--weekly", action="store_true", help="weekly instead of daily")
    ap.add_argument("--lang", help="language slug, e.g. python")
    ap.add_argument("--max-stars", type=int, default=10000)
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args(argv)

    try:
        page = fetch(lang=args.lang, weekly=args.weekly)
    except OSError as e:
        print(f"fetch failed: {e}", file=sys.stderr)
        return 1

    repos = [r for r in parse_trending(page) if (r["stars"] or 0) < args.max_stars]
    repos.sort(key=lambda r: -(r["stars"] or 0))
    for r in repos[: args.limit]:
        stars = r["stars"] if r["stars"] is not None else "?"
        print(f"{r['name']:<48} {r['lang'] or '-':<12} {stars:>7}  {r['desc'][:80]}")
    print(f"\n{len(repos)} repos under {args.max_stars} stars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
