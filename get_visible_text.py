#!/usr/bin/env python3
"""
get_visible_text.py – Extract human‑visible text **with rich structural cues for LLMs**

v5 – 2025‑06‑11
---------------
* **Headings (h1‑h4)** now reliably come out as `**[Hn] text**` with *double blank lines* before & after – previous whitespace‑collapsing bug fixed.
* Explicitly **drops <header> and <footer>** elements no matter where they appear.
* Still limits extraction to `<main>` if present; otherwise it falls back to `<body>`.
* All earlier behaviour preserved: compact bullets, `#`‑prefixed links, collapse ≥3 blank lines to exactly two.

CLI usage unchanged. The module continues to expose **visible_text()** as its single public function.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Final

import requests
from bs4 import BeautifulSoup

USER_AGENT: Final = (
    "Mozilla/5.0 (compatible; CleanTextBot/5.0; +https://github.com/Mjeezuz/clean-text-extractor)"
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def visible_text(url: str, timeout: int = 20) -> str:
    """Return only the human‑visible text at *url* with helpful layout cues."""

    # 1 — fetch -------------------------------------------------------------
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()

    # 2 — parse -------------------------------------------------------------
    soup_full = BeautifulSoup(resp.text, "lxml")

    # 3 — isolate <main> or <body> -----------------------------------------
    main = soup_full.find("main") or soup_full.body or soup_full
    soup = BeautifulSoup(str(main), "lxml")  # operate on a copy

    # 4 — drop <header>, <footer>, and non‑visible tags --------------------
    for tag in soup.find_all(["header", "footer", "script", "style", "noscript", "img", "svg", "iframe", "head", "title"]):
        tag.decompose()

    # 5 — convert headings --------------------------------------------------
    for level in range(1, 5):
        for h in soup.find_all(f"h{level}"):
            text_h = h.get_text(" ", strip=True)
            # Replace the entire element with formatted string (using .replace_with)
            h.replace_with(f"\n\n**[H{level}] {text_h}**\n\n")

    # 6 — bullet lists ------------------------------------------------------
    for li in soup.find_all("li"):
        li_text = li.get_text(" ", strip=True)
        li.replace_with(f"- {li_text}\n")

    # 7 — mark links --------------------------------------------------------
    for a in soup.find_all("a"):
        a_text = a.get_text(" ", strip=True)
        a.replace_with(f"#{a_text}")

    # 8 — <BR> to newline ---------------------------------------------------
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # 9 — extract, normalise whitespace ------------------------------------
    raw = soup.get_text(separator="\n")

    # compress internal whitespace per line, strip right‑hand side
    lines = [re.sub(r"\s+", " ", ln).rstrip() for ln in raw.splitlines()]
    joined = "\n".join(ln for ln in lines)

    # collapse ≥3 consecutive blank lines to exactly 2
    cleaned = re.sub(r"\n{3,}", "\n\n", joined).strip()
    return cleaned

# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------

def _cli() -> None:  # pragma: no cover
    p = argparse.ArgumentParser(description="Extract visible text with layout cues.")
    p.add_argument("url", help="Web page URL to fetch")
    p.add_argument("-o", "--output", metavar="FILE", help="Write to FILE instead of stdout")
    p.add_argument("-t", "--timeout", type=int, default=20, help="HTTP timeout seconds")
    args = p.parse_args()

    txt = visible_text(args.url, timeout=args.timeout)
    if args.output:
        path = pathlib.Path(args.output)
        path.write_text(txt, encoding="utf-8")
        print(f"✔ Saved to {path.resolve()}", file=sys.stderr)
    else:
        print(txt)


if __name__ == "__main__":
    _cli()
