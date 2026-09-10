"""Installed content must remain connected to its pinned source and shared files."""
from __future__ import annotations
import hashlib
import json
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContentInventoryTests(unittest.TestCase):
    def test_every_nature_entrypoint_and_existing_name_is_discoverable(self):
        with (ROOT / 'skills/catalog.toml').open('rb') as handle:
            catalog = tomllib.load(handle)
        identifiers = {row['id'] for row in catalog['skill']}
        nature_names = {p.parent.name for p in (ROOT / 'upstream/nature-skills/skills').glob('*/SKILL.md') if p.parent.name != 'nature-shared'}
        self.assertEqual(len(nature_names), 19)
        self.assertTrue(nature_names <= identifiers)
        self.assertEqual(len(identifiers), 37)
        aliases = {alias: row['id'] for row in catalog['skill'] for alias in row['aliases']}
        self.assertEqual(aliases['researchwrite'], 'nature-proposal-writer')
        self.assertEqual(aliases['manuscript-writing-review'], 'manuscript-review')
        resources = {row['id']: row['path'] for row in catalog['resource']}
        self.assertEqual(resources['nature-shared'], 'skills/nature-shared')
        self.assertTrue((ROOT / resources['nature-shared']).is_dir())

    def test_pinned_content_hashes_still_match_and_cover_installed_files(self):
        data = json.loads((ROOT / 'provenance/content-files.lock.json').read_text())
        paths = set()
        for item in data['files']:
            path = ROOT / item['path']
            self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
            self.assertTrue(path.is_file(), item['path'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['sha256'], item['path'])
            paths.add(item['path'])
        installed = {str(p.relative_to(ROOT)) for p in (ROOT / 'skills').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertTrue(installed <= paths, sorted(installed - paths))

    def test_restricted_document_skills_are_not_imported(self):
        for identifier in ('docx', 'pdf', 'pptx', 'xlsx'):
            self.assertFalse((ROOT / 'sources/kdense/skills' / identifier).exists())
            self.assertFalse((ROOT / 'skills' / identifier).exists())
        self.assertTrue((ROOT / 'skills/venue-templates/LICENSE-LPPL').is_file())

    def test_skill_entrypoint_markdown_links_resolve(self):
        for skill in (ROOT / 'skills').glob('*/SKILL.md'):
            for value in re.findall(r'\[[^\]]*\]\(([^)]*)\)', skill.read_text()):
                if '://' in value or value.startswith('#') or '<' in value or '$' in value:
                    continue
                # Local Markdown destinations may include an optional quoted title.
                destination = value.split(' "', 1)[0].split('#', 1)[0]
                self.assertTrue((skill.parent / destination).exists(), f'{skill.parent.name}: {value}')


if __name__ == '__main__':
    unittest.main()
