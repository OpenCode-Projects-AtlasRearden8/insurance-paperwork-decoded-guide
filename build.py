#!/usr/bin/env python3
"""Build the insurance-paperwork-decoded-guide static site.

Reads docs/**/*.md, renders plain-HTML pages into site/, generates an
index with a table of contents. Standard library only; no network.

Usage:
    python3 build.py            # build into ./site
    python3 build.py --out DIR  # build into DIR
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"

CSS = """
:root {
  --ink: #1f2933; --muted: #52606d; --accent: #1b6e5a;
  --bg: #faf9f6; --card: #ffffff; --line: #e4e1da;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 17px/1.65 Georgia, 'Times New Roman', serif;
}
.wrap { max-width: 46rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
header.site {
  border-bottom: 1px solid var(--line); background: var(--card);
}
header.site .wrap { padding-top: 1.25rem; padding-bottom: 1.25rem; }
.site-title { font-size: 1.15rem; font-weight: bold; margin: 0; }
.site-title a { color: var(--ink); text-decoration: none; }
.site-tag { color: var(--muted); font-size: 0.9rem; margin: 0.25rem 0 0; }
nav.toc {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 8px; padding: 1rem 1.25rem; margin: 1.5rem 0;
  font-family: system-ui, sans-serif; font-size: 0.92rem;
}
nav.toc strong { display: block; margin-bottom: 0.4rem; }
nav.toc ol { margin: 0; padding-left: 1.25rem; }
nav.toc a { color: var(--accent); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }
h1, h2, h3 { font-family: system-ui, sans-serif; line-height: 1.25; }
h1 { font-size: 1.7rem; margin: 0 0 1rem; }
h2 { font-size: 1.25rem; margin: 2rem 0 0.6rem; border-bottom: 1px solid var(--line); padding-bottom: 0.3rem; }
h3 { font-size: 1.05rem; margin: 1.5rem 0 0.4rem; }
p, li { margin: 0.6rem 0; }
blockquote {
  margin: 1.2rem 0; padding: 0.75rem 1.1rem;
  border-left: 4px solid var(--accent); background: var(--card);
  border-radius: 0 8px 8px 0; color: var(--muted);
}
blockquote p { margin: 0.25rem 0; }
code {
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.88em; background: #efece5; padding: 0.1em 0.35em;
  border-radius: 4px;
}
pre {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 8px; padding: 1rem; overflow-x: auto;
  font-size: 0.85rem; line-height: 1.5;
}
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.93rem; }
th, td { border: 1px solid var(--line); padding: 0.45rem 0.7rem; text-align: left; vertical-align: top; }
th { background: var(--card); font-family: system-ui, sans-serif; font-size: 0.88rem; }
hr { border: none; border-top: 1px solid var(--line); margin: 2rem 0; }
a { color: var(--accent); }
.pagenav {
  display: flex; justify-content: space-between; gap: 1rem;
  margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--line);
  font-family: system-ui, sans-serif; font-size: 0.92rem;
}
.disclaimer {
  margin-top: 2.5rem; padding: 0.8rem 1rem; border: 1px dashed var(--line);
  border-radius: 8px; color: var(--muted); font-size: 0.88rem;
  font-family: system-ui, sans-serif;
}
footer.site { margin-top: 2rem; color: var(--muted); font-size: 0.85rem; font-family: system-ui, sans-serif; }
"""

DISCLAIMER = (
    "This site is education only — never coverage, legal, medical, or tax "
    "advice. Your policy's own wording controls."
)

PAGE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Insurance Paperwork, Decoded</title>
<style>{css}</style>
</head>
<body>
<header class="site"><div class="wrap">
<p class="site-title"><a href="{prefix}index.html">Insurance Paperwork, Decoded</a></p>
<p class="site-tag">An education-only manual by Asdale Dynamics, LLC</p>
</div></header>
<div class="wrap">
{content}
<div class="pagenav">{prev}{next}</div>
<p class="disclaimer">{disclaimer}</p>
<footer class="site">Insurance Paperwork, Decoded · MIT License ·
Copyright (c) 2026 Asdale Dynamics, LLC</footer>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Minimal markdown -> HTML (subset used by docs/)
# ---------------------------------------------------------------------------

def inline(text: str) -> str:
    """Render inline markdown: code, bold, italic, links."""
    placeholders: list[str] = []

    def stash(m: re.Match) -> str:
        placeholders.append("<code>%s</code>" % html.escape(m.group(1)))
        return "\x00%d\x00" % (len(placeholders) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<em>\1</em>", text)

    def link(m: re.Match) -> str:
        href, label = m.group(2), m.group(1)
        if href.endswith(".md"):
            href = href[:-3] + ".html"
        return '<a href="%s">%s</a>' % (html.escape(href, quote=True), label)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    for i, ph in enumerate(placeholders):
        text = text.replace("\x00%d\x00" % i, ph)
    return text


def render_markdown(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped.startswith("```"):
            flush_para()
            code: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code)))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, inline(m.group(2)), level))
            i += 1
            continue

        if re.match(r"^-{3,}$", stripped) or re.match(r"^\*{3,}$", stripped):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            quote: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % render_blocks(quote))
            continue

        # table
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            flush_para()
            rows: list[list[str]] = []
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            def row_html(cells: list[str], tag: str) -> str:
                return "<tr>%s</tr>" % "".join(
                    "<%s>%s</%s>" % (tag, inline(c), tag) for c in cells)
            out.append("<table><thead>%s</thead><tbody>%s</tbody></table>" % (
                row_html(header, "th"),
                "".join(row_html(r, "td") for r in rows)))
            continue

        # unordered list (incl. checkboxes)
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            items: list[str] = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                i += 1
                while (i < n and re.match(r"^\s{2,}\S", lines[i])
                       and not re.match(r"^([-*]\s+|\d+\.\s+|```)", lines[i].strip())):
                    item += " " + lines[i].strip()
                    i += 1
                cb = re.match(r"^\[( |x|X)\]\s+(.*)$", item)
                if cb:
                    checked = cb.group(1).lower() == "x"
                    box = "&#9745;" if checked else "&#9744;"
                    items.append("<li>%s %s</li>" % (box, inline(cb.group(2))))
                else:
                    items.append("<li>%s</li>" % inline(item))
            out.append("<ul>%s</ul>" % "".join(items))
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", stripped):
            flush_para()
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                i += 1
                while (i < n and re.match(r"^\s{2,}\S", lines[i])
                       and not re.match(r"^([-*]\s+|\d+\.\s+|```)", lines[i].strip())):
                    item += " " + lines[i].strip()
                    i += 1
                items.append("<li>%s</li>" % inline(item))
            out.append("<ol>%s</ol>" % "".join(items))
            continue

        para.append(stripped)
        i += 1

    flush_para()
    return "\n".join(out)


def render_blocks(lines: list[str]) -> str:
    """Render a small list of already-stripped lines (used in blockquotes)."""
    return render_markdown("\n".join(lines))


# ---------------------------------------------------------------------------
# Site assembly
# ---------------------------------------------------------------------------

def title_of(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return m.group(1).strip()
    return fallback


def collect_docs() -> list[Path]:
    if not DOCS.is_dir():
        sys.exit("error: docs/ directory not found next to build.py")
    return sorted(DOCS.rglob("*.md"))


def rel_url(src: Path) -> str:
    rel = src.relative_to(DOCS).with_suffix(".html")
    return rel.as_posix()


def build(out: Path) -> list[Path]:
    docs = collect_docs()
    pages: list[dict] = []
    for src in docs:
        md_text = src.read_text(encoding="utf-8")
        pages.append({
            "src": src,
            "url": rel_url(src),
            "title": title_of(md_text, src.stem),
            "body": render_markdown(md_text),
        })

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    written: list[Path] = []
    for idx, page in enumerate(pages):
        depth = page["url"].count("/")
        prefix = "../" * depth
        prev_page = pages[idx - 1] if idx > 0 else None
        next_page = pages[idx + 1] if idx < len(pages) - 1 else None
        prev_html = ('<a href="%s%s">&larr; %s</a>' % (prefix, prev_page["url"], html.escape(prev_page["title"]))
                     if prev_page else "<span></span>")
        next_html = ('<a href="%s%s">%s &rarr;</a>' % (prefix, next_page["url"], html.escape(next_page["title"]))
                     if next_page else "<span></span>")
        toc_page = ('<nav class="toc"><strong>Contents</strong><ol>%s</ol></nav>'
                    % "".join('<li><a href="%s%s">%s</a></li>'
                              % (prefix, p["url"], html.escape(p["title"]))
                              for p in pages))
        body = toc_page + page["body"]
        html_text = PAGE_TMPL.format(
            title=html.escape(page["title"]), css=CSS, content=body,
            prev=prev_html, next=next_html, disclaimer=DISCLAIMER, prefix=prefix)
        dest = out / page["url"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html_text, encoding="utf-8")
        written.append(dest)

    index_toc = ('<nav class="toc"><strong>Contents</strong><ol>%s</ol></nav>'
                 % "".join('<li><a href="%s">%s</a></li>' % (p["url"], html.escape(p["title"]))
                           for p in pages))
    index_html = PAGE_TMPL.format(
        title="Start Here", css=CSS,
        content=INDEX_INTRO + index_toc, prev="<span></span>", next="<span></span>",
        disclaimer=DISCLAIMER, prefix="")
    index_dest = out / "index.html"
    index_dest.write_text(index_html, encoding="utf-8")
    written.append(index_dest)

    return written


INDEX_INTRO = """<h1>Insurance Paperwork, Decoded</h1>
<p>An <strong>education-only</strong> manual for reading everyday insurance
policies &mdash; auto, renters, homeowners, health, and life &mdash;
translated section by section into plain English. Premiums, deductibles,
and out-of-pocket costs in plain arithmetic; declaration pages decoded;
claim-filing walkthroughs with document checklists; denial-letter first
responses; and an annual review ritual.</p>
<p>Built by <strong>Asdale Dynamics, LLC</strong> in the same spirit as
<em>The Massive AI Manual</em>: plain English, step by step, never
condescending. Health-insurance specifics are complemented by the companion
project <em>medicare-decoded-guide</em>.</p>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "site"),
                        help="output directory (default: ./site)")
    args = parser.parse_args()
    out = Path(args.out)
    written = build(out)
    print("Built %d pages into %s" % (len(written), out))


if __name__ == "__main__":
    main()
