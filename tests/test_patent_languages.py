"""Exercise document and figure output in both supported explicit languages."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/nature-paper-to-patent/scripts'


class PatentLanguages(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('docx'), 'python-docx is provided by writing-documents')
    def test_docx_defaults_to_english_and_supports_explicit_chinese(self):
        source_claim = '一种方法，其特征在于，包括获取数据和输出结果。'
        data = {'title': 'Source title', 'claims': [{'number': 1, 'text': source_claim}], 'specification': {}, 'abstract': 'Source abstract'}
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            draft = directory / 'draft.json'
            draft.write_text(json.dumps(data))
            for language, expected in [(None, 'Claims'), ('zh', '权利要求书')]:
                output = directory / f'{language or "default"}.docx'
                args = [sys.executable, str(SCRIPTS / 'render_patent_docx.py'), str(draft), '--output', str(output), '--part', 'claims']
                if language:
                    args += ['--language', language]
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                with zipfile.ZipFile(output) as archive:
                    document = ElementTree.fromstring(archive.read('word/document.xml'))
                    text = list(document.itertext())
                    self.assertIn(expected, text)
                    self.assertIn('1. ' + source_claim, text)
                    core = ElementTree.fromstring(archive.read('docProps/core.xml'))
                    self.assertIn(language or 'en', list(core.itertext()))

    def test_svg_caption_language_and_preserved_source_labels(self):
        data = {
            'claims': [{'number': 1, 'text': 'S1 acquire; S2 return.'}],
            'specification': {'figure_descriptions': ['Figure 1 is the workflow.']},
            'figures': [{'number': 1, 'type': 'flowchart', 'title': 'Source title', 'complete_claim_flow': True, 'claim_number': 1,
                         'nodes': [{'id': 'S1', 'label': 'S1 acquire', 'claim_step': 'S1'}, {'id': 'S2', 'label': 'S2 return value', 'claim_step': 'S2'}],
                         'edges': [{'from': 'S1', 'to': 'S2'}]}],
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            draft = directory / 'draft.json'
            draft.write_text(json.dumps(data))
            for language, prefix in [('en', 'Figure 1'), ('zh', '图1')]:
                output = directory / language
                result = subprocess.run([sys.executable, str(SCRIPTS / 'render_flowchart_svg.py'), str(draft), '--output-dir', str(output), '--language', language], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                svg = ElementTree.fromstring((output / 'figure-1.svg').read_text())
                text = ' '.join(svg.itertext())
                self.assertIn(prefix + ' Source title', text)
                self.assertIn('S1 acquire', text)

    @unittest.skipUnless(importlib.util.find_spec('docx') and importlib.util.find_spec('PIL'), 'document rendering dependencies are provided by writing-documents')
    def test_package_builder_renders_complete_english_package(self):
        fixture_path = ROOT / 'skills/nature-paper-to-patent/tests/test_validation.py'
        spec = importlib.util.spec_from_file_location('patent_language_fixture', fixture_path)
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
        data = fixture.valid_draft()
        data['figures'][0]['title'] = 'Method flowchart'
        for node in data['figures'][0]['nodes']:
            node['label'] = node['id'] + ' Process data'
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            draft = directory / 'draft.json'
            draft.write_text(json.dumps(data))
            output = directory / 'output'
            result = subprocess.run([sys.executable, str(SCRIPTS / 'build_patent_package.py'), str(draft), '--output-dir', str(output), '--language', 'en'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(list(output.glob('*.docx'))), 5)
            self.assertTrue((output / 'patent-figures/figure-1.png').is_file())
            with zipfile.ZipFile(output / 'patent-specification.docx') as archive:
                document = archive.read('word/document.xml')
                self.assertIn(b'Specification', document)
                self.assertIn(b'oMath', document)


if __name__ == '__main__':
    unittest.main()
