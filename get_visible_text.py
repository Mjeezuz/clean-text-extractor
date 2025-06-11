#!/usr/bin/env python3
"""
get_visible_text.py – Extract only the human‑visible text from any web page (no alt‑text, no <title>, no inline attributes).

Usage from the command line
---------------------------
python get_visible_text.py https://example.com              # prints to stdout
python get_visible_text.py https://example.com -o page.txt  # writes to file

The file also exposes a single helper function:
    visible_text(url: str, timeout: int = 20) -> str
which you can import elsewhere (e.g. from Streamlit).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Final

import requests
from bs4 import BeautifulSoup

USER_AGENT: Final = "Mozilla/5.0 (compatible; CleanTextBot/1.0; +https://github.com/Mjeezuz/clean-text-extractor)"


def visible_text(url: str, timeout: int = 20) -> str:
    """Return only the human‑visible text at *url*.

    The function:
    * Downloads *url* using :pyfunc:`requests.get` with a desktop User‑Agent.
    * Parses HTML via **lxml** + **BeautifulSoup4**.
    * Removes all tags that should never be seen by users: ``<script>``, ``<style>``,
      ``<noscript>``, ``<img>``, ``<svg>``, ``<iframe>``, ``<head>``, and ``<title>``.
    * Collapses whitespace so the result is a single paragraph‑style block suitable for NLP.
    """
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # drop non‑visible elements entirely
    for tag in soup(["script", "style", "noscript", "img", "svg", "iframe", "head", "title"]):
        tag.decompose()

    # gather remaining text fragments, strip whitespace, and join
    text = " ".join(fragment.strip() for fragment in soup.stripped_strings)
    # normalise internal whitespace to single spaces
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Command‑line interface
# ---------------------------------------------------------------------------


def _cli() -> None:  # pragma: no cover  (simple CLI wrapper, not unit‑tested)
    parser = argparse.ArgumentParser(description="Extract visible text from a web page.")
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
