#!/usr/bin/env python3
"""Validate traceability, completeness, and quality gates in a patent draft."""

# Chinese literals are compatibility identifiers: claim/site matchers or font names.
import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


SOURCE_ID = re.compile(r"^[PEFC]\d{3,}$")
PLACEHOLDER = re.compile(r"\[(?:TO CONFIRM|待确认)[^\]]*\]", re.IGNORECASE)
VAGUE_RESULT = re.compile(r"(技术结果|处理结果|最终结果)")
QUALITY_THRESHOLDS = {
    "evidence_support": 4,
    "claim_architecture": 4,
    "terminology_consistency": 4,
    "enablement_detail": 3,
    "technical_effect_reasoning": 3,
}


@dataclass
class Finding:
    level: str
    code: str
    message: str


def add(findings: list[Finding], level: str, code: str, message: str) -> None:
    findings.append(Finding(level, code, message))


def validate(data: dict) -> list[Finding]:
    findings: list[Finding] = []
    required = (
        "title",
        "metadata",
        "source_analysis",
        "source_map",
        "terminology_ledger",
        "formula_inventory",
        "figure_inventory",
        "evidence_ledger",
        "claims",
        "claim_feature_map",
        "figures",
        "specification",
        "abstract",
        "quality_assessment",
    )
    for key in required:
        if key not in data:
            add(findings, "ERROR", "MISSING_KEY", f"Missing top-level field: {key}.")

    claims = data.get("claims", [])
    numbers = [claim.get("number") for claim in claims]
    if not claims:
        add(findings, "ERROR", "NO_CLAIMS", "A complete draft must include claims.")
    elif numbers != list(range(1, len(numbers) + 1)):
        add(findings, "ERROR", "CLAIM_SEQUENCE", f"Claim numbers are not consecutive: {numbers}.")
    for claim in claims:
        text = str(claim.get("text", ""))
        if not text.strip():
            add(findings, "ERROR", "EMPTY_CLAIM", f"Claim {claim.get('number')} is empty.")
        if PLACEHOLDER.search(text):
            add(
                findings,
                "ERROR",
                "CLAIM_PLACEHOLDER",
                f"Claim {claim.get('number')} still contains a confirmation placeholder.",
            )

    source_records = data.get("source_map", [])
    source_ids = set()
    for record in source_records:
        source_id = str(record.get("id", ""))
        if not SOURCE_ID.fullmatch(source_id):
            add(findings, "ERROR", "SOURCE_ID", f"Invalid source ID: {source_id!r}.")
        if source_id in source_ids:
            add(findings, "ERROR", "DUPLICATE_SOURCE_ID", f"Duplicate source ID: {source_id}.")
        source_ids.add(source_id)
        if not record.get("locator"):
            add(findings, "WARNING", "SOURCE_LOCATOR", f"{source_id} lacks a page, section or line locator.")

    canonical_terms = set()
    forbidden_aliases = set()
    for item in data.get("terminology_ledger", []):
        canonical = str(item.get("canonical_zh", "")).strip()
        if not canonical:
            add(findings, "ERROR", "CANONICAL_TERM", "The terminology table contains an empty canonical_zh value.")
        elif canonical in canonical_terms:
            add(findings, "ERROR", "DUPLICATE_TERM", f"Duplicate canonical term: {canonical}.")
        canonical_terms.add(canonical)
        forbidden_aliases.update(
            str(alias).strip() for alias in item.get("forbidden_aliases", []) if str(alias).strip()
        )

    ledger_ids = set()
    for item in data.get("evidence_ledger", []):
        ledger_id = str(item.get("id", ""))
        if not ledger_id:
            add(findings, "ERROR", "LEDGER_ID", "An evidence-ledger entry lacks an ID.")
        elif ledger_id in ledger_ids:
            add(findings, "ERROR", "DUPLICATE_LEDGER_ID", f"Duplicate evidence-ledger ID: {ledger_id}.")
        ledger_ids.add(ledger_id)
        status = item.get("support_status")
        if status not in {"explicit", "inherent", "needs-confirmation", "unsupported"}:
            add(findings, "ERROR", "SUPPORT_STATUS", f"{ledger_id} has an invalid support status: {status}.")
        referenced = item.get("source_ids", [])
        if status in {"explicit", "inherent"} and not referenced:
            add(findings, "ERROR", "MISSING_SOURCE_LINK", f"{ledger_id} lacks source IDs.")
        for source_id in referenced:
            if source_ids and source_id not in source_ids:
                add(findings, "ERROR", "UNKNOWN_SOURCE_ID", f"{ledger_id} references an unknown source ID: {source_id}.")

    mapped_claims = set()
    for mapping in data.get("claim_feature_map", []):
        claim_number = mapping.get("claim_number")
        mapped_claims.add(claim_number)
        if claim_number not in numbers:
            add(findings, "ERROR", "UNKNOWN_CLAIM", f"A feature mapping references a nonexistent claim: {claim_number}.")
        if not str(mapping.get("feature", "")).strip():
            add(findings, "ERROR", "EMPTY_FEATURE", "A claim-feature mapping has an empty feature.")
        evidence_ids = mapping.get("evidence_ids", [])
        if not evidence_ids:
            add(
                findings,
                "ERROR",
                "UNMAPPED_FEATURE",
                f"Feature {mapping.get('feature', '')!r} in claim {claim_number} lacks evidence IDs.",
            )
        for evidence_id in evidence_ids:
            if evidence_id not in ledger_ids:
                add(
                    findings,
                    "ERROR",
                    "UNKNOWN_EVIDENCE_ID",
                    f"Claim {claim_number} references unknown evidence ID: {evidence_id}.",
                )
    for number in numbers:
        if number not in mapped_claims:
            add(findings, "ERROR", "CLAIM_NOT_MAPPED", f"Claim {number} has no feature-to-evidence mapping.")
    formal_text = "\n".join(str(claim.get("text", "")) for claim in claims)
    formal_text += "\n" + json.dumps(data.get("specification", {}), ensure_ascii=False)
    for alias in sorted(forbidden_aliases):
        if alias in formal_text:
            add(findings, "ERROR", "FORBIDDEN_ALIAS", f"Formal text uses a forbidden alias: {alias}.")

    source_analysis = data.get("source_analysis", {})
    spec = data.get("specification", {})
    equations = spec.get("equations", [])
    formula_inventory = data.get("formula_inventory", [])
    for item in formula_inventory:
        source_id = item.get("source_id")
        if source_ids and source_id not in source_ids:
            add(findings, "ERROR", "FORMULA_INVENTORY_SOURCE", f"The equation inventory references unknown source ID: {source_id}.")
        if not item.get("disposition"):
            add(findings, "ERROR", "FORMULA_DISPOSITION", f"Source equation {source_id} lacks a recorded disposition.")
    expected_formula_count = source_analysis.get("formula_count_in_source")
    if isinstance(expected_formula_count, int) and expected_formula_count != len(formula_inventory):
        add(
            findings,
            "WARNING",
            "FORMULA_INVENTORY_COUNT",
            f"Sources report {expected_formula_count} equations, but the inventory records {len(formula_inventory)}.",
        )
    if "equations" not in spec:
        add(findings, "ERROR", "EQUATIONS_ARRAY", "The specification must include an equations array.")
    if source_analysis.get("contains_core_formulas") and not equations:
        add(findings, "ERROR", "MISSING_CORE_EQUATIONS", "Sources contain core equations, but none are included in the specification.")
    equation_numbers = [equation.get("number") for equation in equations]
    if equation_numbers and equation_numbers != list(range(1, len(equation_numbers) + 1)):
        add(findings, "ERROR", "EQUATION_SEQUENCE", f"Equation numbers are not consecutive: {equation_numbers}.")
    for equation in equations:
        number = equation.get("number")
        if not equation.get("latex"):
            add(findings, "ERROR", "EQUATION_LATEX", f"Equation {number} lacks convertible LaTeX source.")
        if not equation.get("source_ids"):
            add(findings, "ERROR", "EQUATION_SOURCE", f"Equation {number} lacks source IDs.")
        for source_id in equation.get("source_ids", []):
            if source_ids and source_id not in source_ids:
                add(findings, "ERROR", "EQUATION_SOURCE", f"Equation {number} references unknown source ID: {source_id}.")
        if not equation.get("symbols"):
            add(findings, "ERROR", "EQUATION_SYMBOLS", f"Equation {number} lacks structured symbol definitions.")
        if not equation.get("technical_role"):
            add(findings, "ERROR", "EQUATION_ROLE", f"Equation {number} lacks a description of its technical role.")

    figures = data.get("figures", [])
    for item in data.get("figure_inventory", []):
        source_id = item.get("source_id")
        if source_ids and source_id not in source_ids:
            add(findings, "ERROR", "FIGURE_INVENTORY_SOURCE", f"The figure inventory references unknown source ID: {source_id}.")
        if not item.get("disposition"):
            add(findings, "ERROR", "FIGURE_DISPOSITION", f"Source figure {source_id} lacks a recorded disposition.")
    figure_numbers = [figure.get("number") for figure in figures]
    if not figures:
        add(findings, "ERROR", "NO_FIGURES", "A complete draft must include at least one patent figure.")
    elif figure_numbers != list(range(1, len(figure_numbers) + 1)):
        add(findings, "ERROR", "FIGURE_SEQUENCE", f"Figure numbers are not consecutive: {figure_numbers}.")
    abstract_figure = data.get("abstract_figure_number")
    if abstract_figure not in figure_numbers:
        add(findings, "ERROR", "ABSTRACT_FIGURE", "The abstract-figure number does not identify an existing figure.")
    for figure in figures:
        if not figure.get("source_ids"):
            add(findings, "WARNING", "FIGURE_SOURCE", f"Figure {figure.get('number')} lacks source IDs or a redraw rationale.")
        for source_id in figure.get("source_ids", []):
            if source_ids and source_id not in source_ids:
                add(
                    findings,
                    "ERROR",
                    "FIGURE_SOURCE",
                    f"Figure {figure.get('number')} references unknown source ID: {source_id}.",
                )
        end_nodes = set(str(node.get("id")) for node in figure.get("nodes", []))
        for edge in figure.get("edges", []):
            end_nodes.discard(str(edge.get("from")))
        for node in figure.get("nodes", []):
            if str(node.get("id")) in end_nodes and VAGUE_RESULT.search(str(node.get("label", ""))):
                add(
                    findings,
                    "ERROR",
                    "VAGUE_FINAL_RESULT",
                    f"Figure {figure.get('number')} uses a vague result name for its terminal node.",
                )

    for field in ("technical_field", "background", "embodiments", "figure_descriptions"):
        if not spec.get(field):
            add(findings, "ERROR", "SPEC_SECTION", f"The specification field is absent or empty: {field}.")
    invention = spec.get("invention_content", {})
    for field in ("problem", "solution", "beneficial_effects"):
        if not invention.get(field):
            add(findings, "ERROR", "INVENTION_CONTENT", f"Invention content is missing: {field}.")

    abstract = re.sub(r"\s+", "", str(data.get("abstract", "")))
    if not abstract:
        add(findings, "ERROR", "EMPTY_ABSTRACT", "The specification abstract is empty.")
    elif len(abstract) > 300:
        add(findings, "WARNING", "ABSTRACT_LENGTH", f"The abstract has approximately {len(abstract)} characters; manually check its length.")

    quality = data.get("quality_assessment", {})
    if quality.get("status") not in {"review-draft", "incomplete-draft"}:
        add(
            findings,
            "WARNING",
            "DRAFT_STATUS",
            "Use review-draft or incomplete-draft for quality_assessment.status.",
        )
    scores = quality.get("scores", {})
    for dimension, threshold in QUALITY_THRESHOLDS.items():
        item = scores.get(dimension)
        if not isinstance(item, dict) or not isinstance(item.get("score"), int):
            add(findings, "ERROR", "QUALITY_SCORE", f"Missing quality score: {dimension}.")
            continue
        score = item["score"]
        if score < 1 or score > 5:
            add(findings, "ERROR", "QUALITY_RANGE", f"{dimension} score is outside 1-5: {score}.")
        elif score < threshold:
            add(
                findings,
                "ERROR",
                "QUALITY_THRESHOLD",
                f"{dimension} score {score} is below the delivery threshold {threshold}.",
            )
        if not str(item.get("evidence", "")).strip():
            add(findings, "WARNING", "QUALITY_EVIDENCE", f"The {dimension} score lacks supporting evidence.")

    if source_analysis.get("contains_core_formulas"):
        formula_item = scores.get("formula_coverage", {})
        if formula_item.get("score", 0) < 4:
            add(findings, "ERROR", "FORMULA_SCORE", "When core equations exist, formula_coverage must be at least 4.")
    if figures:
        figure_item = scores.get("figure_alignment", {})
        if figure_item.get("score", 0) < 4:
            add(findings, "ERROR", "FIGURE_SCORE", "When figures exist, figure_alignment must be at least 4.")

    return findings


def format_report(findings: list[Finding]) -> str:
    if not findings:
        return "PASS: The draft passed the structural, provenance and quality-threshold checks.\n"
    lines = [f"{item.level}\t{item.code}\t{item.message}" for item in findings]
    errors = sum(item.level == "ERROR" for item in findings)
    warnings = sum(item.level == "WARNING" for item in findings)
    lines.extend(("", f"Summary: {errors} errors, {warnings} warnings"))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, help="UTF-8 structured patent draft JSON")
    parser.add_argument("--report", type=Path, help="Write the validation report to a file")
    parser.add_argument("--json", action="store_true", help="Print findings as JSON")
    args = parser.parse_args()

    data = json.loads(args.draft.read_text(encoding="utf-8"))
    findings = validate(data)
    report = format_report(findings)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    if args.json:
        print(json.dumps([item.__dict__ for item in findings], ensure_ascii=False, indent=2))
    else:
        print(report, end="")
    return 1 if any(item.level == "ERROR" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
