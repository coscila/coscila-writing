"""Regressions found during independent deployment and MCP review."""

import json
import os
from pathlib import Path
import types
import unittest
from unittest.mock import patch

from ocsl_writing.academic_server import AcademicDispatch, check_egress, tool_schemas
from ocsl_writing import integration
from ocsl_writing.errors import ValidationError
import test_integration

ROOT = Path(__file__).resolve().parents[1]


class PayloadValidationTests(unittest.TestCase):
    def test_unavailable_citation_is_not_a_successful_reference(self):
        module = types.SimpleNamespace(get_citation=lambda **kw: json.dumps({
            "id": "10.1234/missing", "citation": "Citation not available for DOI: 10.1234/missing"}))
        with self.assertRaises(RuntimeError):
            AcademicDispatch(ROOT, module)("get_citation", {"id": "10.1234/missing", "id_type": "doi"})

    def test_empty_detail_and_malformed_search_results_are_rejected(self):
        for name, arguments, payload in [
            ("get_paper_by_id", {"id": "10.1234/missing", "id_type": "doi"}, {}),
            ("get_paper_by_id", {"id": "10.1234/missing", "id_type": "doi"}, []),
            ("search_papers", {"query": "RNA", "sources": ["crossref"]}, {"results": "bad result"}),
        ]:
            with self.subTest(name=name):
                module = types.SimpleNamespace(**{name: lambda **kw: json.dumps(payload)})
                with self.assertRaises(ValueError):
                    AcademicDispatch(ROOT, module)(name, arguments)

    def test_private_prose_in_optional_fields_cannot_skip_egress_gate(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PermissionError):
                check_egress("search_papers", {"query": "RNA", "type": "Private manuscript text.\nMore private text."})

    def test_optional_string_schema_bounds_and_known_source_names(self):
        schema = next(row for row in tool_schemas(ROOT) if row["name"] == "search_papers")["inputSchema"]
        string_branch = next(branch for branch in schema["properties"]["type"]["anyOf"] if branch.get("type") == "string")
        self.assertEqual(string_branch.get("maxLength"), 500)
        module = types.SimpleNamespace(search_papers=lambda **kw: json.dumps({"results": []}))
        with self.assertRaises(ValueError):
            AcademicDispatch(ROOT, module)("search_papers", {"query": "RNA", "sources": ["unrecognized-provider"]})


class RollbackEditTests(unittest.TestCase):
    setUp = test_integration.IntegrationTests.setUp
    tearDown = test_integration.IntegrationTests.tearDown
    install = test_integration.IntegrationTests.install
    def test_concurrent_edit_during_acceptance_is_preserved_on_failure(self):
        target = self.roots[0] / "paper-test/SKILL.md"
        def edit_then_fail(*args):
            target.write_text("User edited this during the live MCP probes")
            raise ValidationError("live acceptance failed")
        with patch.object(integration, "_acceptance", side_effect=edit_then_fail):
            with self.assertRaises(Exception):
                self.install()
        self.assertEqual(target.read_text(), "User edited this during the live MCP probes")
        self.assertTrue((self.paths.integration / "pending.json").is_file())
        self.assertFalse(set(integration.OWNED_MCP_NAMES) & set(json.loads(self.config.read_text())["mcpServers"]))


if __name__ == "__main__":
    unittest.main()
