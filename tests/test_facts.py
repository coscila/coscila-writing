"""Exported numbers must recompute before a manuscript can consume them."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from ocsl_writing.errors import ValidationError
from ocsl_writing.facts import render_facts, verify_facts
from ocsl_writing.util import sha256_file


class FactsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "facts.sqlite3"
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("CREATE TABLE assessments (supported INTEGER)")
            connection.executemany("INSERT INTO assessments VALUES (?)", [(1,), (0,), (1,)])
            connection.commit()
        self.path = self.root / "facts.json"
        self.facts = {
            "schemaVersion": 1,
            "facts": {
                "count": self.fact(3, "SELECT COUNT(*) FROM assessments"),
                "rate": self.fact(2 / 3, "SELECT AVG(supported) FROM assessments"),
            },
        }
        self.save()

    def fact(self, value, sql):
        return {"value": value, "sql": sql, "method": "Synthetic assessment fixture",
                "source": {"path": self.db.name, "sha256": sha256_file(self.db)}}

    def save(self):
        self.path.write_text(json.dumps(self.facts))

    def test_recomputed_counts_and_numeric_formats_render(self):
        template, output = self.root / "template.md", self.root / "paper.md"
        template.write_text("{{fact:count|,d}} items; {{fact:rate|.1%}} supported.")
        report = render_facts(self.path, template, output)
        self.assertEqual(output.read_text(), "3 items; 66.7% supported.")
        self.assertEqual(report["usedFacts"], ["count", "rate"])
        self.assertEqual(report["outputSha256"], sha256_file(output))

    def test_changed_snapshot_and_wrong_exported_value_fail(self):
        self.facts["facts"]["count"]["value"] = 4
        self.save()
        with self.assertRaisesRegex(ValidationError, "derivation differs"):
            verify_facts(self.path)
        self.facts["facts"]["count"]["value"] = 3
        self.save()
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("INSERT INTO assessments VALUES (0)")
            connection.commit()
        with self.assertRaisesRegex(ValidationError, "SHA-256 mismatch"):
            verify_facts(self.path)

    def test_metadata_only_and_literal_echoes_are_not_derivations(self):
        for sql in (None, "SELECT 3", "SELECT COUNT(*) FROM sqlite_master"):
            with self.subTest(sql=sql):
                self.facts["facts"]["count"]["sql"] = sql
                self.save()
                with self.assertRaises(ValidationError):
                    verify_facts(self.path)

    def test_derivation_cannot_write_or_attach_external_database(self):
        for sql in ("DELETE FROM assessments RETURNING supported", "ATTACH DATABASE ':memory:' AS other"):
            with self.subTest(sql=sql):
                self.facts["facts"]["count"]["sql"] = sql
                self.save()
                with self.assertRaises(ValidationError):
                    verify_facts(self.path)
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM assessments").fetchone()[0], 3)

    def test_unknown_fact_does_not_publish_partial_or_replace_existing_output(self):
        template, output = self.root / "template.md", self.root / "paper.md"
        template.write_text("{{fact:count}} {{fact:unavailable}}")
        output.write_text("previous version")
        with self.assertRaisesRegex(ValidationError, "unknown fact"):
            render_facts(self.path, template, output)
        self.assertEqual(output.read_text(), "previous version")

    def test_sources_cannot_escape_export_and_output_cannot_replace_evidence(self):
        self.facts["facts"]["count"]["source"]["path"] = "../outside.sqlite3"
        self.save()
        with self.assertRaisesRegex(ValidationError, "inside the export"):
            verify_facts(self.path)
        self.facts["facts"]["count"]["source"]["path"] = self.db.name
        self.save()
        template = self.root / "template.md"
        template.write_text("{{fact:count}}")
        for output in (template, self.path, self.db):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValidationError, "overwrite"):
                    render_facts(self.path, template, output)

    def test_non_scalar_and_uncheckpointed_wal_are_rejected(self):
        self.facts["facts"]["count"]["sql"] = "SELECT supported FROM assessments"
        self.save()
        with self.assertRaisesRegex(ValidationError, "exactly one scalar"):
            verify_facts(self.path)
        self.facts["facts"]["count"]["sql"] = "SELECT COUNT(*) FROM assessments"
        self.save()
        Path(str(self.db) + "-wal").touch()
        with self.assertRaisesRegex(ValidationError, "without a WAL"):
            verify_facts(self.path)


if __name__ == "__main__":
    unittest.main()
