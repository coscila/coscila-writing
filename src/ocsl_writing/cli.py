"""Operator and runtime commands for the writing companion."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import catalogs, environments, integration, skills
from .config import resolve_paths
from .errors import WritingError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="ocsl-writing", description=__doc__)
    root.add_argument("--home", help="Immutable source checkout (OCSL_WRITING_HOME)")
    root.add_argument("--state", help="Operator state outside source and chats (OCSL_WRITING_STATE)")
    root.add_argument("--lab-repo", help="OC Science Lab checkout used for staging")
    commands = root.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser("catalog").add_subparsers(dest="action", required=True)
    catalog.add_parser("validate")
    skill_commands = commands.add_parser("skills").add_subparsers(dest="action", required=True)
    skill_commands.add_parser("list")
    skill_commands.add_parser("validate")
    skill_commands.add_parser("show").add_argument("skill")
    env_commands = commands.add_parser("env").add_subparsers(dest="action", required=True)
    env_commands.add_parser("list")
    build = env_commands.add_parser("build")
    selection = build.add_mutually_exclusive_group(required=True)
    selection.add_argument("--environment")
    selection.add_argument("--all", action="store_true")
    build.add_argument("--timeout", type=float, default=1800)
    build.add_argument("--probe-timeout", type=float, default=120)
    for action in ("ensure", "run", "verify", "describe"):
        item = env_commands.add_parser(action)
        item.add_argument("--workspace", type=Path, default=Path.cwd())
        item.add_argument("--environment")
        item.add_argument("--skill")
        item.add_argument("--chat-root")
        item.add_argument("--timeout", type=float, default=1800)
        if action == "run":
            item.add_argument("argv", nargs=argparse.REMAINDER)
    mcp_commands = commands.add_parser("mcp").add_subparsers(dest="action", required=True)
    for action in ("list", "render", "config", "doctor", "verify"):
        item = mcp_commands.add_parser(action)
        item.add_argument("--live", action="store_true")
        item.add_argument("--strict", action="store_true")
        item.add_argument("--staged-config", type=Path)
    migration = commands.add_parser("integrate").add_subparsers(dest="action", required=True)
    install = migration.add_parser("install")
    install.add_argument("--cache-root")
    install.add_argument("--skill-root", action="append")
    install.add_argument("--mcp-config")
    install.add_argument("--staged-config")
    install.add_argument("--stage-command", help="Shell-quoted argv; executed without a shell")
    install.add_argument("--stage-cwd")
    install.add_argument("--stage-timeout", type=float, default=900)
    migration.add_parser("status")
    verify = migration.add_parser("verify")
    verify.add_argument("--live", action="store_true")
    verify.add_argument("--strict", action="store_true")
    uninstall = migration.add_parser("uninstall")
    uninstall.add_argument("--stage-timeout", type=float, default=900)
    translations = commands.add_parser("translations").add_subparsers(dest="action", required=True)
    translations.add_parser("verify")
    fact_commands = commands.add_parser("facts").add_subparsers(dest="action", required=True)
    for action in ("verify", "render"):
        item = fact_commands.add_parser(action)
        item.add_argument("--facts", type=Path, required=True)
        if action == "render":
            item.add_argument("--template", type=Path, required=True)
            item.add_argument("--output", type=Path, required=True)
    lint = fact_commands.add_parser("lint", help="bare-number gate: every numeral must come from a fact token")
    lint.add_argument("--manuscript", type=Path, required=True)
    lint.add_argument("--facts", type=Path, help="also require every token to name a verified fact")
    lint.add_argument("--allow", action="append", default=[], help="extra regular expression for allowed numerals")
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--live", action="store_true")
    doctor.add_argument("--strict", action="store_true")
    doctor.add_argument("--staged-config", type=Path)
    return root


def dispatch(args):
    paths = args.paths
    command, action = args.command, getattr(args, "action", None)
    if command == "catalog":
        return catalogs.validate_catalogs(paths)
    if command == "skills":
        if action == "list": return skills.list_skills(paths)
        if action == "show": return skills.show_skill(paths, args.skill)
        return skills.validate_catalog(paths)
    if command == "env":
        if action == "list": return environments.list_environments(paths)
        if action == "build":
            chosen = [row["id"] for row in environments.definitions(paths)] if args.all else [args.environment]
            return [environments.build_template(paths, item, timeout=args.timeout, probe_timeout=args.probe_timeout)
                    for item in chosen]
        identifier = args.environment
        if args.skill:
            selected = skills.get_skill(paths, args.skill)["primary_environment"]
            if identifier and selected != identifier:
                raise WritingError("--skill and --environment disagree")
            identifier = selected
        if not identifier:
            raise WritingError("select --environment or --skill")
        options = {"workspace": args.workspace, "environment_id": identifier, "chat_root": args.chat_root}
        if action == "run":
            return environments.run_in_environment(paths, args.argv, timeout=args.timeout, **options)
        if action == "ensure":
            return environments.ensure_environment(paths, timeout=args.timeout, **options)
        if action == "verify":
            return environments.verify_environment(paths, **options)
        return {**environments.definition(paths, identifier), "workspace": str(args.workspace)}
    if command == "mcp":
        from . import mcps
        method = {"list": mcps.cmd_list, "render": mcps.cmd_render, "config": mcps.cmd_render,
                  "doctor": mcps.cmd_doctor, "verify": mcps.cmd_doctor}[action]
        return method(paths, args)
    if command == "integrate":
        if action == "install":
            return integration.install_integration(paths, **integration.resolve_arguments(args))
        if action == "uninstall":
            return integration.uninstall_integration(paths, stage_timeout=args.stage_timeout)
        result = integration.status(paths, verify=action == "verify")
        if action == "verify" and result.get("installed"):
            from . import mcps
            state = json.loads(integration.install_state_path(paths).read_text())
            result["mcpAcceptance"] = mcps.verify(paths, staged_config=Path(state["mcp"]["stagedConfigPath"]),
                                                 live=args.live, strict=args.strict)
        return result
    if command == "translations":
        from . import translations
        return translations.verify(paths)
    if command == "facts":
        from . import facts
        if action == "verify":
            return facts.verify_facts(args.facts)
        if action == "lint":
            return facts.lint_manuscript(args.manuscript, args.facts, args.allow)
        return facts.render_facts(args.facts, args.template, args.output)
    if command == "doctor":
        from . import mcps, translations
        result = {"catalogs": catalogs.validate_catalogs(paths), "translations": translations.verify(paths),
                  "environments": environments.list_environments(paths), "mcp": mcps.cmd_doctor(paths, args)}
        mcp = result["mcp"]
        reports = []
        for server in mcp.get("servers", []):
            reports.append(server.get("source", {}))
            if mcp.get("stagedConfigChecked"):
                reports.append(server.get("staged", {}))
        protocol_keys = ("initialized", "schemaMatches", "errorPath", "cleanShutdown")
        mcp_ok = bool(reports) and all(all(report.get(key) is True for key in protocol_keys)
                                       for report in reports)
        if args.live:
            mcp_ok = mcp_ok and all(report.get("acceptanceComplete") is True for report in reports)
        if args.strict:
            mcp_ok = mcp_ok and mcp.get("acceptanceComplete") is True
        result["ok"] = (result["catalogs"].get("ok") is True
                        and result["translations"].get("ok") is True and mcp_ok)
        return result
    raise WritingError(f"unsupported command: {command}")


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        args.paths = resolve_paths(home=args.home, state=args.state, lab_repo=args.lab_repo)
        result = dispatch(args)
        if isinstance(result, subprocess.CompletedProcess):
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 1 if isinstance(result, dict) and result.get("ok") is False else 0
    except (WritingError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
