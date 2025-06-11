#!/usr/bin/env python3
"""
get_visible_text.py – Extract human‑visible text **with layout cues for LLMs**

▲ New in this version
---------------------
* **Headings (h1–h4)** are wrapped in *double* blank lines so block boundaries are obvious.
* **Bulleted lists** stay compact (single newline between each "- item").
* **Links** are prefixed with a hash symbol (e.g. "#Read more") so that downstream GPT pipelines can recognise anchor text.
* Runs of 3+ blank lines are collapsed to exactly two, ensuring consistent paragraph spacing.

Command‑line usage
------------------
```bash
python get_visible_text.py https://example.com              # prints formatted text
python get_visible_text.py https://example.com -o page.txt  # writes to file
```

The helper function
```
visible_text(url: str, timeout: int = 20) -> str
```
returns a lightly‑formatted string ready for copy/paste or further NLP.
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
    "Mozilla/5.0 (compatible; CleanTextBot/3.0; +https://github.com/Mjeezuz/clean-text-extractor)"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def visible_text(url: str, timeout: int = 20) -> str:
    """Return only the human‑visible text at *url* with basic formatting.

    Steps
    -----
    1. Fetch *url* with a desktop User‑Agent.
    2. Parse HTML using **lxml** + **BeautifulSoup4**.
    3. **Remove** elements never displayed: ``script``, ``style``, ``noscript``,
       ``img``, ``svg``, ``iframe``, ``head``, ``title``.
    4. Convert headings (h1‑h4) → double‑spaced blocks.
    5. Convert list items → Markdown bullets ("- ").
    6. Prefix anchor text with "#" to mark links.
    7. Replace ``<br>`` tags with explicit line breaks.
    8. Extract text with ``separator="\n"``.
    9. Collapse excess internal whitespace; keep max two blank lines.
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

    # --- 4. headings (h1‑h4) ----------------------------------------------
    for h in soup.find_all(re.compile("^h[1-4]$")):
        text_h = h.get_text(" ", strip=True)
        h.clear()
        # Wrap with blank lines before & after
        h.append(f"\n\n{text_h}\n\n")

    # --- 5. bullet lists ----------------------------------------------------
    for li in soup.find_all("li"):
        text_li = li.get_text(" ", strip=True)
        li.clear()
        li.append(f"- {text_li}")

    # --- 6. mark links ------------------------------------------------------
    for a in soup.find_all("a"):
        text_a = a.get_text(" ", strip=True)
        a.clear()
        a.append(f"#{text_a}")

    # --- 7. explicit <br> handling -----------------------------------------
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # --- 8. gather text -----------------------------------------------------
    raw_text = soup.get_text(separator="\n")

    # --- 9. normalise -------------------------------------------------------
    # Collapse runs of whitespace inside lines but *keep* newlines we inserted.
    lines = [re.sub(r"\s+", " ", line).rstrip() for line in raw_text.splitlines()]
    text_with_lines = "\n".join(lines)

    # Reduce triples or more blank lines to exactly two.
    cleaned = re.sub(r"\n{3,}", "\n\n", text_with_lines).strip()

    return cleaned


# ---------------------------------------------------------------------------
# Command‑line interface
# ---------------------------------------------------------------------------

def _cli() -> None:  # pragma: no cover (simple CLI wrapper)
    parser = argparse.ArgumentParser(
        description="Extract visible text from a web page with helpful spacing."
    )
    parser.add_argument("url", help="Web page URL to fetch")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="Write result to FILE instead of stdout"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, default=20, help="HTTP timeout in seconds (default: 20)"
    )
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
