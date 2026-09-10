"""Select the promoted core Python for source-checkout CLI entrypoints."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .config import resolve_paths
from .environments import template_python


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
        interpreter = template_python(paths, "writing-core")
    os.execv(interpreter, [str(interpreter), "-m", "ocsl_writing.cli", *arguments])


if __name__ == "__main__":
    main()
