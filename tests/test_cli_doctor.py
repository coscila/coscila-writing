"""Doctor exit status must reflect coverage and requested MCP acceptance."""

from contextlib import ExitStack, redirect_stdout
import copy
import io
import unittest
from unittest.mock import patch

from ocsl_writing import cli


class DoctorStatusTests(unittest.TestCase):
    def run_doctor(self, *, translations_ok=True, catalogs_ok=True, mcp=None, flags=()):
        protocol = {"initialized": True, "schemaMatches": True, "errorPath": True,
                    "cleanShutdown": True, "acceptanceComplete": False}
        if mcp is None:
            mcp = {"servers": [{"source": protocol}], "stagedConfigChecked": False,
                   "acceptanceComplete": False}
        with ExitStack() as stack:
            stack.enter_context(patch("ocsl_writing.cli.resolve_paths", return_value=object()))
            stack.enter_context(patch("ocsl_writing.catalogs.validate_catalogs", return_value={"ok": catalogs_ok}))
            stack.enter_context(patch("ocsl_writing.translations.verify", return_value={"ok": translations_ok}))
            stack.enter_context(patch("ocsl_writing.environments.list_environments", return_value=[]))
            stack.enter_context(patch("ocsl_writing.mcps.cmd_doctor", return_value=mcp))
            stack.enter_context(redirect_stdout(io.StringIO()))
            return cli.main(["doctor", *flags])

    def test_catalog_and_translation_failures_have_nonzero_exit(self):
        self.assertEqual(self.run_doctor(), 0)
        self.assertEqual(self.run_doctor(translations_ok=False), 1)
        self.assertEqual(self.run_doctor(catalogs_ok=False), 1)

    def test_protocol_failure_and_missing_servers_fail(self):
        self.assertEqual(self.run_doctor(mcp={"servers": []}), 1)
        self.assertEqual(self.run_doctor(mcp={"servers": [{"source": {"initialized": False}}]}), 1)

    def test_live_and_strict_modes_require_corresponding_acceptance(self):
        self.assertEqual(self.run_doctor(flags=["--live"]), 1)
        self.assertEqual(self.run_doctor(flags=["--strict"]), 1)
        protocol = {"initialized": True, "schemaMatches": True, "errorPath": True,
                    "cleanShutdown": True, "acceptanceComplete": True}
        source = {"servers": [{"source": protocol}], "stagedConfigChecked": False,
                  "acceptanceComplete": False}
        self.assertEqual(self.run_doctor(mcp=source, flags=["--live"]), 0)
        self.assertEqual(self.run_doctor(mcp=source, flags=["--live", "--strict"]), 1)
        staged = copy.deepcopy(source)
        staged.update(stagedConfigChecked=True, acceptanceComplete=True)
        staged["servers"][0]["staged"] = protocol
        self.assertEqual(self.run_doctor(mcp=staged, flags=["--live", "--strict"]), 0)
        staged["servers"][0]["staged"] = {}
        self.assertEqual(self.run_doctor(mcp=staged, flags=["--live", "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
