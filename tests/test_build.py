"""Tests for the insurance-paperwork-decoded-guide build.

Run with:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

sys.path.insert(0, str(ROOT))

import build  # noqa: E402


class TestDocsExist(unittest.TestCase):
    def test_all_expected_docs_exist(self):
        expected = [
            "00-start-here.md",
            "01-how-to-read-a-policy.md",
            "02-money-math.md",
            "03-declaration-pages.md",
            "04-auto.md",
            "05-renters.md",
            "06-homeowners.md",
            "07-health.md",
            "08-life.md",
            "09-claim-filing-walkthrough.md",
            "10-denial-letters.md",
            "11-annual-review-ritual.md",
            "12-glossary.md",
            "worksheets/policy-binder-worksheets.md",
        ]
        for name in expected:
            with self.subTest(doc=name):
                self.assertTrue((DOCS / name).is_file(), f"missing {name}")

    def test_every_doc_has_h1_title(self):
        for src in sorted(DOCS.rglob("*.md")):
            text = src.read_text(encoding="utf-8")
            with self.subTest(doc=src.name):
                self.assertRegex(text, r"(?m)^# \S")

    def test_every_doc_carries_disclaimer(self):
        for src in sorted(DOCS.rglob("*.md")):
            text = src.read_text(encoding="utf-8")
            with self.subTest(doc=src.name):
                self.assertIn("Education only", text)


class TestMarkdownRendering(unittest.TestCase):
    def test_headings(self):
        html_out = build.render_markdown("# Title\n\n## Sub\n\nbody")
        self.assertIn("<h1>Title</h1>", html_out)
        self.assertIn("<h2>Sub</h2>", html_out)

    def test_bold_italic_code(self):
        html_out = build.render_markdown("**bold** and *em* and `code`")
        self.assertIn("<strong>bold</strong>", html_out)
        self.assertIn("<em>em</em>", html_out)
        self.assertIn("<code>code</code>", html_out)

    def test_lists(self):
        html_out = build.render_markdown("- a\n- b\n\n1. one\n2. two")
        self.assertIn("<ul>", html_out)
        self.assertIn("<ol>", html_out)

    def test_checkboxes(self):
        html_out = build.render_markdown("- [ ] open\n- [x] done")
        self.assertIn("&#9744;", html_out)
        self.assertIn("&#9745;", html_out)

    def test_blockquote(self):
        html_out = build.render_markdown("> quoted line")
        self.assertIn("<blockquote>", html_out)
        self.assertIn("quoted line", html_out)

    def test_table(self):
        html_out = build.render_markdown("| a | b |\n| --- | --- |\n| 1 | 2 |")
        self.assertIn("<table>", html_out)
        self.assertIn("<th>a</th>", html_out)
        self.assertIn("<td>2</td>", html_out)

    def test_fenced_code_block_escapes_html(self):
        html_out = build.render_markdown("```\n<a>&b\n```")
        self.assertIn("&lt;a&gt;&amp;b", html_out)

    def test_internal_md_links_become_html(self):
        html_out = build.render_markdown("see [guide 02](02-money-math.md)")
        self.assertIn('href="02-money-math.html"', html_out)

    def test_html_is_escaped_in_text(self):
        html_out = build.render_markdown("a < b & c > d")
        self.assertIn("a &lt; b &amp; c &gt; d", html_out)


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "site"
        self.written = build.build(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_generated(self):
        self.assertTrue((self.out / "index.html").is_file())

    def test_every_doc_produces_html(self):
        docs = list(DOCS.rglob("*.md"))
        self.assertEqual(len(self.written), len(docs) + 1)  # + index

    def test_no_broken_internal_links(self):
        for page in self.written:
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="([^"]+)"', text):
                if href.startswith(("http", "mailto:", "#")):
                    continue
                target = (page.parent / href).resolve()
                with self.subTest(page=page.name, href=href):
                    self.assertTrue(target.exists(), f"broken link {href}")

    def test_disclaimer_on_every_page(self):
        for page in self.written:
            with self.subTest(page=page.name):
                self.assertIn("education only", page.read_text(encoding="utf-8"))

    def test_pages_have_nav_and_title(self):
        sample = self.out / "02-money-math.html"
        text = sample.read_text(encoding="utf-8")
        self.assertIn("<title>", text)
        self.assertIn("pagenav", text)
        self.assertIn("toc", text)

    def test_nested_page_links_resolve(self):
        text = (self.out / "worksheets" / "policy-binder-worksheets.html").read_text(
            encoding="utf-8")
        self.assertIn('href="../index.html"', text)
        self.assertIn('href="../12-glossary.html"', text)


class TestProjectFiles(unittest.TestCase):
    def test_license_text(self):
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Asdale Dynamics, LLC", lic)
        self.assertIn("MIT License", lic)

    def test_readme_credits_llc_and_disclaims(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", readme)
        self.assertIn("never coverage or legal advice", readme.lower())

    def test_no_secrets_in_repo_files(self):
        pattern = re.compile(
            r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}"
            r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "site" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, ValueError):
                continue
            with self.subTest(file=path.relative_to(ROOT)):
                self.assertIsNone(pattern.search(text), f"secret-like string in {path}")


if __name__ == "__main__":
    unittest.main()
