"""Exported numbers must recompute before a manuscript can consume them."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from ocsl_writing.errors import ValidationError
from ocsl_writing.cli import main
from ocsl_writing.facts import lint_manuscript, render_facts, verify_facts
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


class FactsLintTests(unittest.TestCase):
    """Bare-number gate: numerals must come from fact tokens unless their use is structural."""

    def setUp(self):
        FactsTests.setUp(self)

    def lint(self, text, suffix=".md", **kwargs):
        path = self.root / ("manuscript" + suffix)
        path.write_text(text, encoding="utf-8")
        return lint_manuscript(path, **kwargs)

    def bare(self, text, suffix=".md", **kwargs):
        return [finding["text"] for finding in self.lint(text, suffix, **kwargs)["bareNumbers"]]

    def test_tokens_and_structural_numbers_pass(self):
        text = ("# 2 Results\n\nWe assessed {{fact:count|,d}} items from 2020 to 2026 (Fig. 2, Figs. 3-4, Tables 1 and 2, "
                "Section 4.2, Supplementary Table 5, Extended Data Fig. 1).\n"
                "Markers [12] and [3-5, 8] stay; so do COVID-19, IL-6, SHA-256, Qwen3.8, citation-census@1 and 95% CI.\n"
                "1. A numbered list item\n`code 77` and https://example.org/a1/2 and 10.5555/x123 and PMID: 123456.\n"
                "<!-- a comment with 99 -->\n\n## References\n1. Author A. Journal 12:34-56 (2019).\n")
        report = self.lint(text)
        self.assertEqual([], report["bareNumbers"])
        self.assertTrue(report["ok"])
        self.assertEqual(1, report["factTokens"])

    def test_bare_numbers_are_reported_with_positions(self):
        report = self.lint("Intro.\nWe judged 12 entries; 16 % were flagged at 0.05, -3.5 and 1,234.\n")
        self.assertFalse(report["ok"])
        self.assertEqual(["12", "16 %", "0.05", "-3.5", "1,234"], [f["text"] for f in report["bareNumbers"]])
        self.assertEqual((2, 11), (report["bareNumbers"][0]["line"], report["bareNumbers"][0]["column"]))

    def test_latex_structure(self):
        text = ("\\documentclass[11pt]{article}\n\\begin{document}\n\\section{Results}\\label{sec:2}\n"
                "We judged {{fact:count}} items (Fig.~\\ref{fig:1}, Table~2). % 99 in a comment\n"
                "\\includegraphics[width=0.8\\textwidth]{fig3.pdf}\n\\item A share of 16\\% is bare, so is 3.2.\n"
                "\\begin{thebibliography}{9}\\bibitem{x} A. J. 12, 34 (2018).\\end{thebibliography}\n\\end{document}\n")
        self.assertEqual(["16\\%", "3.2"], self.bare(text, ".tex"))

    def test_waivers_and_extra_allow_patterns(self):
        self.assertEqual([], self.bare("Threshold 0.05 here. <!-- facts-lint: allow -->\n"))
        self.assertEqual([], self.bare("Python 3.11 was used.\n", allow=[r"Python \d+\.\d+"]))
        self.assertEqual(["3.11"], self.bare("Python 3.11 was used.\n"))

    def test_unknown_fact_tokens_fail_with_facts(self):
        report = self.lint("{{fact:count}} and {{fact:missing}}\n", facts=self.path)
        self.assertEqual(["missing"], report["unknownFacts"])
        self.assertFalse(report["ok"])
        self.assertTrue(self.lint("{{fact:count}} and {{fact:rate|.1%}}\n", facts=self.path)["ok"])

    def test_command_line(self):
        manuscript = self.root / "paper.md"
        manuscript.write_text("{{fact:count}} items; 7 bare.\n", encoding="utf-8")
        self.assertEqual(1, main(["facts", "lint", "--manuscript", str(manuscript), "--facts", str(self.path)]))
        manuscript.write_text("{{fact:count}} items.\n", encoding="utf-8")
        self.assertEqual(0, main(["facts", "lint", "--manuscript", str(manuscript), "--facts", str(self.path)]))

    fact = FactsTests.fact
    save = FactsTests.save


if __name__ == "__main__":
    unittest.main()
