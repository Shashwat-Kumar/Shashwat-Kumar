"""Dependency packaging checks; browser behavior is tested separately."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and 'src' in attrs:
            self.sources.append(attrs['src'])


class DashboardAssetsTest(unittest.TestCase):
    def test_runtime_assets_are_local_and_match_documented_hashes(self):
        parser = Scripts()
        parser.feed((ROOT / 'gnn_money_mule_dashboard.html').read_text())
        self.assertEqual(len(parser.sources), 3)
        provenance = (ROOT / 'vendor/README.md').read_text()
        for source in parser.sources:
            with self.subTest(source=source):
                self.assertFalse(urlparse(source).scheme)
                self.assertFalse(urlparse(source).netloc)
                asset = (ROOT / source).resolve()
                self.assertTrue(asset.is_relative_to(ROOT / 'vendor'))
                self.assertIn(hashlib.sha256(asset.read_bytes()).hexdigest(), provenance)
        for name in ('react', 'react-dom', 'babel'):
            self.assertIn('MIT', (ROOT / f'vendor/{name}-LICENSE').read_text())


if __name__ == '__main__':
    unittest.main()
