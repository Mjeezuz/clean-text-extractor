#!/usr/bin/env python3
"""
get_visible_text.py – Extract human‑visible text **with semantic cues for LLMs**

🔄 What’s new (v4)
------------------
* **Headings h1‑h4** are now emitted as `**[H{n}] text**` and still wrapped in *double* blank lines.
  Example: `\n\n**[H2] Features**\n\n`
* Extraction is confined to the document’s `<main>` element if present, ignoring sidebars, nav, ads, etc.
* `<footer>` is discarded entirely, even when inside `<main>`.
* All earlier behaviour remains: compact bullet lists, `#` prefix for links, collapsing ≥3 blank lines to two.

Command‑line usage remains unchanged.
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
    "Mozilla/5.0 (compatible; CleanTextBot/4.0; +https://github.com/Mjeezuz/clean-text-extractor)"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def visible_text(url: str, timeout: int = 20) -> str:
    """Return only the human‑visible text at *url* with helpful layout cues.

    Steps (high‑level)
    ------------------
    1. Fetch URL with a desktop User‑Agent.
    2. Parse HTML via **lxml** + **BeautifulSoup4**.
    3. Focus on `<main>` if it exists; otherwise use `<body>`.
    4. Remove elements never rendered (script, style, img, head, footer…).
    5. Mark up headings as `**[Hn] text**` surrounded by blank lines.
    6. Convert list items to Markdown bullets.
    7. Prefix anchor text with `#`.
    8. Replace `<br>` with explicit newlines.
    9. Extract text and normalise whitespace.
    """

    # --- 1. download --------------------------------------------------------
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()

    # --- 2. parse -----------------------------------------------------------
    soup_full = BeautifulSoup(resp.text, "lxml")

    # --- 3. scope to <main> -------------------------------------------------
    main = soup_full.find("main") or soup_full.body or soup_full
    # Work on a *copy* of this subtree to avoid side‑effects on soup_full
    soup = BeautifulSoup(str(main), "lxml")

    # Always discard footer even if inside main
    for ft in soup.find_all("footer"):
        ft.decompose()

    # --- 4. strip non‑visible elements -------------------------------------
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "img",
            "svg",
            "iframe",
            "head",
            "title",
        ]
    ):
        tag.decompose()

    # --- 5. headings (h1‑h4) ----------------------------------------------
    for level in range(1, 5):
        for h in soup.find_all(f"h{level}"):
            text_h = h.get_text(" ", strip=True)
            tag = f"[H{level}]"
            h.clear()
            h.append(f"\n\n**{tag} {text_h}**\n\n")

    # --- 6. bullet lists ----------------------------------------------------
    for li in soup.find_all("li"):
        li_text = li.get_text(" ", strip=True)
        li.clear()
        li.append(f"- {li_text}")

    # --- 7. mark links ------------------------------------------------------
    for a in soup.find_all("a"):
        a_text = a.get_text(" ", strip=True)
        a.clear()
        a.append(f"#{a_text}")

    # --- 8. explicit <br> handling -----------------------------------------
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # --- 9. gather & clean --------------------------------------------------
    raw = soup.get_text(separator="\n")

    lines = [re.sub(r"\s+", " ", ln).rstrip() for ln in raw.splitlines()]
    joined = "\n".join(lines)
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
