"""Regression cases at the boundary between imported writing helpers."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_helper(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MarkerTests(unittest.TestCase):
    def test_nested_and_escaped_markers_preserve_surrounding_prose(self):
        helper = load_helper('writing_marker_count', 'skills/draft-marker-discipline/scripts/prose_wordcount.py')
        text = r'Before \TODO{find {nested} and escaped \} brace} after.'
        self.assertEqual(helper.strip_macro(text, 'TODO'), 'Before  after.')

    def test_unbalanced_marker_is_an_error(self):
        helper = load_helper('writing_marker_count', 'skills/draft-marker-discipline/scripts/prose_wordcount.py')
        with self.assertRaises(SystemExit):
            helper.strip_macro(r'Before \TODO{unfinished', 'TODO')


class BibliographyTests(unittest.TestCase):
    def audit(self, bib, tex=''):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'refs.bib').write_text(bib)
            (root / 'main.tex').write_text(tex)
            return subprocess.run([
                sys.executable, str(ROOT / 'skills/citation-verifier/scripts/audit_bib.py'),
                '--bib', str(root / 'refs.bib'), '--tex', str(root / 'main.tex'),
            ], capture_output=True, text=True)

    def test_undated_standard_and_missing_doi_are_not_fabricated_to_pass(self):
        result = self.audit('@manual{standard, title={Reference standard}, organization={Issuing body}}', r'\cite{standard}')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('year', result.stdout.lower())

    def test_duplicate_key_and_undefined_citation_are_blocking(self):
        result = self.audit('@misc{x,title={First}}\n@misc{x,title={Second}}', r'\cite{missing}')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('missing', result.stdout)
        self.assertIn('duplicate', result.stdout.lower())


if __name__ == '__main__':
    unittest.main()
