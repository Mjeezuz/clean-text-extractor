#!/usr/bin/env python3
"""
get_visible_text.py – Extracts only the human‑visible text from any web page.

Usage (CLI):
    python get_visible_text.py https://example.com           # prints to stdout
    python get_visible_text.py https://example.com -o page.txt

Features
--------
* **Skips** all <script>, <style>, <noscript>, <img>, <svg>, <iframe>, <head>, and <title> elements,
  so no alt‑text, title attributes, or other non‑visible metadata are captured.
* Collapses consecutive whitespace and converts <br> / <p> boundaries into newlines for legibility.
* Requires only three well‑known libraries: `requests`, `beautifulsoup4`, `lxml`.

Install deps once with:
    pip install -r requirements.txt

requirements.txt
-----------------
requests>=2.31
beautifulsoup4>=4.12
lxml>=5.2

"""
import argparse
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _visible_text(html: str) -> str:
    """Return the visible text from *html*, minus scripts/images/styles etc."""
    soup = BeautifulSoup(html, "lxml")

    # Remove tags that never show visible text
    for tag in soup([
        "script",
        "style",
        "noscript",
        "img",
        "svg",
        "iframe",
        "head",
        "title",
    ]):
        tag.decompose()

    # Convert <br> and paragraph ends into newlines to keep structure
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.append("\n")

    # Join visible strings, strip each piece, then collapse whitespace
    text = " ".join(s.strip() for s in soup.stripped_strings)

    # Normalize: collapse spaces around newlines, and 2+ spaces to 1 space
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# CLI entry‑point
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch a web page and output only its visible text.",
    )
    parser.add_argument("url", help="URL of the page to scrape")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write the extracted text to this file instead of stdout",
    )
    args = parser.parse_args(argv)

    try:
        resp = requests.get(args.url, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        parser.error(f"Failed to fetch {args.url}: {exc}")

    text = _visible_text(resp.text)

    if args.output:
        args.output.write_text(text, encoding="utf‑8")
    else:
        print(text)


if __name__ == "__main__":
    sys.exit(main())
