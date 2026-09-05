import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class AgentReadyBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "build.py")], cwd=ROOT, check=True)

    def test_vendored_asset_and_license_are_deployed(self):
        for name in ("agentready.min.js", "agentready.LICENSE.txt"):
            self.assertEqual((ROOT / "static" / name).read_bytes(), (DIST / name).read_bytes())

    def test_every_generated_html_page_uses_local_agentready(self):
        pages = list(DIST.glob("*.html")) + list((DIST / "ja").glob("*.html")) + list((DIST / "en").glob("*.html"))
        self.assertGreater(len(pages), 3)
        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertNotIn("@willh/agentready", html, page)
            expected = "../agentready.min.js" if page.parent != DIST else "agentready.min.js"
            self.assertIn(f'src="{expected}"', html, page)
            self.assertIn("new URLSearchParams(location.search).has('webmcp')", html, page)

    def test_three_language_indexes_expose_filter_tool(self):
        for page in (DIST / "index.html", DIST / "ja" / "index.html", DIST / "en" / "index.html"):
            html = page.read_text(encoding="utf-8")
            self.assertIn('data-agent-name="filter_restaurants"', html, page)
            for field in ("sort", "city", "cuisine"):
                self.assertIn(f'name="{field}"', html, page)

    def test_album_pages_have_semantic_landmarks(self):
        pages = list(DIST.glob("album-*.html")) + list((DIST / "ja").glob("album-*.html")) + list((DIST / "en").glob("album-*.html"))
        self.assertGreater(len(pages), 0)
        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertIn("<header", html, page)
            self.assertIn("<main>", html, page)
            self.assertIn("<footer", html, page)


if __name__ == "__main__":
    unittest.main()
