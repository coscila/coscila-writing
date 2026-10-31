"""Select the promoted core Python for source-checkout CLI entrypoints."""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path

# The companion parses its catalogs with tomllib (Python 3.11+). An older interpreter, such as a host python3 of 3.10,
# would stop at the first import with a traceback; say what to do instead, before anything imports the catalogs.
MINIMUM_PYTHON = (3, 11)
if tuple(sys.version_info[:2]) < MINIMUM_PYTHON:
    sys.stderr.write(json.dumps({"ok": False, "error": (
        f"ocsl-writing needs Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} or newer; {sys.executable} is "
        f"{platform.python_version()}. Run it with an explicit interpreter: OCSL_WRITING_PYTHON=<python 3.11+> "
        "bin/ocsl-writing ... (docs/deployment.md)")}) + "\n")
    raise SystemExit(1)

from .config import resolve_paths  # noqa: E402
from .environments import template_python  # noqa: E402
from .errors import ValidationError  # noqa: E402
from .util import load_json  # noqa: E402


def template_build_python(paths) -> str | None:
    """The Python version the promoted writing-core template was built with (its template.json), if readable."""
    try:
        parent = paths.templates / "writing-core"
        build = load_json(parent / "current.json")["buildId"]
        return str(load_json(parent / build / "template.json").get("python") or "") or None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def main():
    arguments = sys.argv[1:]
    options = {}
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if item == "--":
            break
        for option in ("home", "state", "lab-repo"):
            if item == "--" + option and index + 1 < len(arguments):
                options[option.replace("-", "_")] = arguments[index + 1]
                index += 1
            elif item.startswith("--" + option + "="):
                options[option.replace("-", "_")] = item.split("=", 1)[1]
        index += 1
    paths = resolve_paths(**options)
    interpreter = Path(sys.executable)
    if paths.state and (paths.templates / "writing-core/current.json").is_file():
        try:
            interpreter = template_python(paths, "writing-core")
        except ValidationError as error:
            # The template verifies itself against the running interpreter (its build id covers the Python version):
            # started by another Python, the companion must be run with the one that built it, not rebuilt.
            built = template_build_python(paths)
            hint = (f" The template was built by Python {built.split()[0]}; {sys.executable} is "
                    f"{platform.python_version()}: run bin/ocsl-writing with the interpreter that built the templates "
                    "(OCSL_WRITING_PYTHON as the deployment environment sets it); no rebuild is needed for that."
                    if built and built != sys.version else "")
            sys.stderr.write(json.dumps({"ok": False, "error": f"writing-core template: {error}.{hint}"}) + "\n")
            raise SystemExit(1)
    os.execv(interpreter, [str(interpreter), "-m", "ocsl_writing.cli", *arguments])


if __name__ == "__main__":
    main()
