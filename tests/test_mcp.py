"""Observable protocol, provider and egress regressions without network I/O."""
import io
import json
import os
from pathlib import Path
import types
import unittest
from unittest.mock import patch

from ocsl_writing.academic_server import AcademicDispatch, check_egress, tool_schemas
from ocsl_writing.mcp_protocol import serve_stdio

ROOT = Path(__file__).resolve().parents[1]


class McpTests(unittest.TestCase):
    def test_pinned_public_and_elsevier_surface(self):
        self.assertEqual({t['name'] for t in tool_schemas(ROOT)}, {'search_papers', 'get_paper_by_id', 'get_citation', 'lookup_mesh'})
        self.assertEqual(len(tool_schemas(ROOT, elsevier=True)), 16)

    def test_provider_error_is_not_success(self):
        fake = types.SimpleNamespace(get_paper_by_id=lambda **kw: json.dumps({'error': 'SECRET http://host?api_key=SECRET'}))
        with self.assertRaises(RuntimeError):
            AcademicDispatch(ROOT, fake)('get_paper_by_id', {'id': '1', 'id_type': 'pmid'})

    def test_async_search_works_without_nested_event_loop(self):
        async def search_papers(**kw):
            return json.dumps({'results': [{'title': 'public paper'}], 'errors': None})
        result = AcademicDispatch(ROOT, types.SimpleNamespace(search_papers=search_papers))('search_papers', {'query': 'RNA sequencing', 'sources': ['crossref']})
        self.assertEqual(result['results'][0]['title'], 'public paper')

    def test_all_failed_providers_error_and_partial_results_redact(self):
        def source(**kw):
            return json.dumps({'results': [{'title': 'paper'}], 'errors': [{'source': 'arxiv', 'error': 'secret URL'}]})
        result = AcademicDispatch(ROOT, types.SimpleNamespace(search_papers=source))('search_papers', {'query': 'RNA', 'sources': ['arxiv']})
        self.assertNotIn('secret', json.dumps(result))

    def test_elsevier_cannot_be_enabled_via_public_search_argument(self):
        with patch.dict(os.environ, {'OCSL_WRITING_ENABLE_ELSEVIER': '0'}):
            with self.assertRaises(PermissionError):
                AcademicDispatch(ROOT, object())('search_papers', {'query': 'RNA', 'sources': ['scopus']})

    def test_private_prose_and_invalid_identifier_block_before_provider(self):
        with self.assertRaises(PermissionError):
            check_egress('search_papers', {'query': 'This is our manuscript. Here is another sentence describing private patient results.'})
        with self.assertRaises(ValueError):
            AcademicDispatch(ROOT, object())('get_paper_by_id', {'id': '/local/private/manuscript.docx', 'id_type': 'doi'})

    def test_protocol_validates_inputs_redacts_errors_and_shuts_down(self):
        tools = [{'name': 'read', 'description': 'test', 'inputSchema': {'type': 'object', 'properties': {'id': {'type': 'integer'}}, 'required': ['id'], 'additionalProperties': False}}]
        calls = [
            {'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
            {'id': 2, 'method': 'tools/call', 'params': {'name': 'read', 'arguments': {'id': 'wrong'}}},
            {'id': 3, 'method': 'tools/call', 'params': {'name': 'read', 'arguments': {'id': 1}}},
            {'id': 4, 'method': 'shutdown'},
        ]
        source = io.StringIO(''.join(json.dumps({'jsonrpc': '2.0', **x}) + '\n' for x in calls))
        sink = io.StringIO()
        def broken(*_): raise RuntimeError('SECRET')
        self.assertEqual(serve_stdio('test', tools, broken, source=source, sink=sink), 0)
        results = [json.loads(x) for x in sink.getvalue().splitlines()]
        self.assertTrue(results[1]['result']['isError'])
        self.assertTrue(results[2]['result']['isError'])
        self.assertNotIn('SECRET', sink.getvalue())


if __name__ == '__main__':
    unittest.main()
