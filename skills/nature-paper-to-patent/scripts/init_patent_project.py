#!/usr/bin/env python3
"""Create an agent-neutral paper-to-patent project workspace."""

import argparse
import json
import shutil
from pathlib import Path


DIRECTORIES = (
    "paper",
    "supplementary/source-code",
    "source-figures",
    "existing-patent",
    "work",
    "outputs",
)
SKILL_FILES = ("SKILL.md", "manifest.yaml", "requirements.txt")
SKILL_DIRECTORIES = ("static", "references", "scripts")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--paper", type=Path, help="Optional paper to copy into paper/")
    parser.add_argument("--force", action="store_true", help="Allow an existing project directory")
    parser.add_argument(
        "--no-embed-skill",
        action="store_true",
        help="Create only case directories without copying the skill bundle",
    )
    args = parser.parse_args()

    project = args.project_dir.resolve()
    if project.exists() and any(project.iterdir()) and not args.force:
        parser.error("project directory is not empty; use --force to add missing structure")
    project.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (project / directory).mkdir(parents=True, exist_ok=True)

    if not args.no_embed_skill:
        skill_root = Path(__file__).resolve().parents[1]
        if project != skill_root:
            for filename in SKILL_FILES:
                shutil.copy2(skill_root / filename, project / filename)
            for directory in SKILL_DIRECTORIES:
                shutil.copytree(
                    skill_root / directory,
                    project / directory,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )

    if args.paper:
        paper = args.paper.resolve()
        if not paper.is_file():
            parser.error(f"paper does not exist: {paper}")
        shutil.copy2(paper, project / "paper" / paper.name)

    intake = {
        "target_jurisdiction": "Chinese invention patent",
        "requested_deliverable": "full-draft",
        "publication_status": "[TO CONFIRM: whether the paper has been made public]",
        "publication_dates": [],
        "inventorship": "[TO CONFIRM: confirm inventors based on actual technical contributions]",
        "ownership": "[TO CONFIRM: confirm the applicant and ownership]",
        "source_files": [],
    }
    intake_path = project / "work" / "00-intake.json"
    if not intake_path.exists():
        intake_path.write_text(
            json.dumps(intake, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    notes = project / "supplementary" / "inventor-notes.md"
    if not notes.exists():
        notes.write_text(
            "# Supplementary inventor notes\n\n"
            "- Actual technical contributions:\n"
            "- Engineering implementations differing from the paper:\n"
            "- Alternative implementations and parameter ranges:\n"
            "- Date and method of first public disclosure:\n"
            "- Subject matter prioritized for protection:\n",
            encoding="utf-8",
        )

    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
