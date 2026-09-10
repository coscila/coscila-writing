"""Source, operator-state and chat-workspace trust boundaries."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import TrustBoundaryError, WritingError
from .util import is_within, no_symlinks


@dataclass(frozen=True)
class Paths:
    home: Path
    state: Path | None = None
    lab_repo: Path | None = None

    def need_state(self) -> Path:
        if self.state is None:
            raise WritingError("set OCSL_WRITING_STATE or pass --state for this command")
        validate_state(self)
        return self.state

    @property
    def skill_catalog(self) -> Path:
        return self.home / "skills/catalog.toml"

    @property
    def environment_catalog(self) -> Path:
        return self.home / "environments/catalog.toml"

    @property
    def mcp_catalog(self) -> Path:
        return self.home / "mcp/catalog.toml"

    @property
    def integration(self) -> Path:
        return self.need_state() / "integration"

    @property
    def templates(self) -> Path:
        return self.need_state() / "environment-templates"

    @property
    def cache(self) -> Path:
        return self.need_state() / "cache"


def protected_sources(paths: Paths) -> list[Path]:
    roots = [paths.home]
    for candidate in (paths.lab_repo, paths.home.parent / "oc-science-lab-bio",
                      paths.home.parent / "oc-science-lab-review"):
        if candidate and candidate.is_dir():
            roots.append(candidate.resolve())
    return roots


def validate_state(paths: Paths) -> None:
    if paths.state is None:
        return
    no_symlinks(paths.state)
    for source in protected_sources(paths):
        if is_within(paths.state, source) or is_within(source, paths.state):
            raise TrustBoundaryError(f"operator state overlaps protected source: {source}")
    declared = os.environ.get("LAB_WORKSPACE_ROOT")
    if declared and (is_within(paths.state, Path(declared)) or is_within(Path(declared), paths.state)):
        raise TrustBoundaryError("operator state overlaps the declared chat workspace")


def require_operator() -> None:
    if any(os.environ.get(key) for key in ("OCSL_WRITING_SANDBOX", "OCSL_REVIEW_SANDBOX", "LAB_SANDBOX")):
        raise TrustBoundaryError("operator commands cannot run inside a lab sandbox")
    cwd = Path.cwd().resolve()
    declared = os.environ.get("LAB_WORKSPACE_ROOT")
    if declared and is_within(cwd, Path(declared)):
        raise TrustBoundaryError("operator commands cannot run inside a chat workspace")
    for parent in (cwd, *cwd.parents):
        if (parent / "WORKSPACE.md").exists() and (parent / ".ocsl").exists():
            raise TrustBoundaryError("operator commands cannot run inside a materialized workspace")


def runtime_workspace(paths: Paths, workspace: Path) -> Path:
    no_symlinks(workspace)
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise TrustBoundaryError(f"workspace directory does not exist: {workspace}")
    for root in [*protected_sources(paths), *([paths.state] if paths.state else [])]:
        if is_within(workspace, root) or is_within(root, workspace):
            raise TrustBoundaryError(f"workspace overlaps source or operator state: {root}")
    declared = os.environ.get("LAB_WORKSPACE_ROOT")
    if declared and not is_within(workspace, Path(declared)):
        raise TrustBoundaryError("workspace is outside LAB_WORKSPACE_ROOT")
    return workspace


def resolve_paths(*, home=None, state=None, lab_repo=None, state_required=False) -> Paths:
    home_value = home or os.environ.get("OCSL_WRITING_HOME")
    source = Path(home_value).expanduser().resolve() if home_value else Path(__file__).resolve().parents[2]
    if not (source / "pyproject.toml").is_file():
        raise WritingError(f"OCSL_WRITING_HOME is not a writing checkout: {source}")
    state_value = state or os.environ.get("OCSL_WRITING_STATE")
    mutable = Path(state_value).expanduser().absolute() if state_value else None
    lab_value = lab_repo or os.environ.get("OCSL_REPO")
    lab = Path(lab_value).expanduser().resolve() if lab_value else source.parent / "oc-science-lab"
    paths = Paths(source, mutable, lab if lab.is_dir() else None)
    validate_state(paths)
    if state_required:
        paths.need_state()
    return paths
