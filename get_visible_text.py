#!/usr/bin/env python3
"""
get_visible_text.py – Extract human‑visible text **with basic layout** (paragraph breaks, list bullets)

Changes vs. v1
--------------
* Keeps natural **line breaks**: every paragraph, heading, list item, and `<br>` becomes a line ending ("\n").
* Adds basic list formatting: each `<li>` starts with "- ".
* Still strips out all non‑visible elements and alt/title attributes.

Command‑line usage
------------------
python get_visible_text.py https://example.com              # prints Markdown‑ish text
python get_visible_text.py https://example.com -o page.txt  # writes to file

The helper function
    visible_text(url: str, timeout: int = 20) -> str
returns a newline‑separated, lightly‑formatted string suitable for copy/paste.
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
    "Mozilla/5.0 (compatible; CleanTextBot/2.0; +https://github.com/Mjeezuz/clean-text-extractor)"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def visible_text(url: str, timeout: int = 20) -> str:
    """Return only the human‑visible text at *url* with basic formatting.

    The algorithm:
    1. Fetches *url* with a desktop User‑Agent and reasonable timeout.
    2. Parses HTML using **lxml** + **BeautifulSoup4**.
    3. **Removes** elements never displayed: ``script``, ``style``, ``noscript``,
       ``img``, ``svg``, ``iframe``, ``head``, ``title``.
    4. Converts list items to Markdown‑style bullets ("- ").
    5. Replaces ``<br>`` tags with explicit line breaks.
    6. Extracts text with ``separator="\n"`` so every block‑level element is on
       its own line.
    7. Collapses internal whitespace while preserving deliberate newlines.
    """

    # --- 1. download --------------------------------------------------------
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()

    # --- 2. parse -----------------------------------------------------------
    soup = BeautifulSoup(response.text, "lxml")

    # --- 3. strip non‑visible elements -------------------------------------
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

    # --- 4. bullet lists ----------------------------------------------------
    for li in soup.find_all("li"):
        text_li = li.get_text(" ", strip=True)
        li.clear()
        li.append(f"- {text_li}")

    # --- 5. explicit <br> handling -----------------------------------------
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # --- 6. gather text with line breaks -----------------------------------
    raw_text = soup.get_text(separator="\n")

    # --- 7. normalise -------------------------------------------------------
    #   * collapse runs of whitespace within lines
    #   * drop empty lines
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines()]
    cleaned_lines = [ln for ln in lines if ln]

    return "\n".join(cleaned_lines)


# ---------------------------------------------------------------------------
# Command‑line interface
# ---------------------------------------------------------------------------

def _cli() -> None:  # pragma: no cover (simple CLI wrapper)
    parser = argparse.ArgumentParser(description="Extract visible text from a web page (with line breaks).")
    parser.add_argument("url", help="Web page URL to fetch")
    parser.add_argument("-o", "--output", metavar="FILE", help="Write result to FILE instead of stdout")
    parser.add_argument("-t", "--timeout", type=int, default=20, help="HTTP timeout in seconds (default: 20)")
    args = parser.parse_args()

    text = visible_text(args.url, timeout=args.timeout)

    if args.output:
        path = pathlib.Path(args.output)
        path.write_text(text, encoding="utf-8")
        print(f"✔ Saved to {path.resolve()}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    _cli()
