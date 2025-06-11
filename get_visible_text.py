#!/usr/bin/env python3
"""
get_visible_text.py – Extract human‑visible text **with rich structural cues for LLMs**

v7 – 2025‑06‑11
---------------
* **New header block** (always at top):
  ```
  #URL_PATH: /path/to/page
  #TITLE:     Example Domain
  #META_DESC: Example Domain is for use in illustrative…
  ```
  – makes it trivial for downstream GPT pipelines to know the source context.
* Keeps v6 features: bold tagged headings (`**[H2] …**`), double‑blank lines around headings, single‑spaced bullets, link anchors prefixed with `#`, removal of `<header>` and `<footer>`, scope within `<main>` when present, no stray line breaks on inline `<b>/<strong>`.

CLI usage unchanged; `visible_text()` remains the public API.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Final, Iterable
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup

USER_AGENT: Final = (
    "Mozilla/5.0 (compatible; CleanTextBot/7.0; +https://github.com/Mjeezuz/clean-text-extractor)"
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _first_meta_content(soup: BeautifulSoup, names: Iterable[str]) -> str:
    """Return the first <meta name="..." content="..."> that matches *names*."""
    for nm in names:
        tag = soup.find("meta", attrs={"name": nm})
        if tag and (content := tag.get("content")):
            return content.strip()
    return ""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def visible_text(url: str, timeout: int = 20) -> str:
    """Return only the human‑visible text at *url* with layout cues and a header."""

    # 1 — fetch -------------------------------------------------------------
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()

    # 2 — parse full document ----------------------------------------------
    soup_full = BeautifulSoup(resp.text, "lxml")

    # 3a — collect meta data ----------------------------------------------
    title_txt = soup_full.title.string.strip() if soup_full.title and soup_full.title.string else ""
    meta_desc = _first_meta_content(soup_full, ("description", "og:description"))
    path_id = unquote(urlparse(url).path or "/")

    # 3b — isolate <main> or <body> ----------------------------------------
    main = soup_full.find("main") or soup_full.body or soup_full
    soup = BeautifulSoup(str(main), "lxml")  # operate on a copy

    # 4 — drop unwanted blocks ---------------------------------------------
    for tag in soup.find_all(
        [
            "header",
            "footer",
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

    # 5 — mark links --------------------------------------------------------
    for a in soup.find_all("a"):
        a_text = a.get_text(" ", strip=True)
        a.replace_with(f"#{a_text}")

    # 6 — convert headings --------------------------------------------------
    for level in range(1, 5):
        for h in soup.find_all(f"h{level}"):
            text_h = h.get_text(" ", strip=True)
            h.replace_with(f"\n\n**[H{level}] {text_h}**\n\n")

    # 7 — bullet lists ------------------------------------------------------
    for li in soup.find_all("li"):
        li_text = li.get_text(" ", strip=True)
        li.replace_with(f"- {li_text}\n")

    # 8 — paragraphs --------------------------------------------------------
    for p in soup.find_all("p"):
        p_text = p.get_text(" ", strip=True)
        p.replace_with(f"{p_text}\n\n")

    # 9 — <BR> to newline ---------------------------------------------------
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # 10 — extract, normalise whitespace -----------------------------------
    raw = soup.get_text(separator=" ")  # use space to avoid inline \n breaks

    lines = [re.sub(r"\s+", " ", ln).rstrip() for ln in raw.splitlines()]
    joined = "\n".join(ln for ln in lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", joined).strip()

    # 11 — prepend header ---------------------------------------------------
    header_parts = [f"#URL_PATH: {path_id}"]
    if title_txt:
        header_parts.append(f"#TITLE: {title_txt}")
    if meta_desc:
        header_parts.append(f"#META_DESC: {meta_desc}")
    header = "\n".join(header_parts)

    return f"{header}\n\n{cleaned}"

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
