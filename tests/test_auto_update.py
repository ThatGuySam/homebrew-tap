"""Hermetic shell tests: fake brew/processes; never operate on a real Mac."""
import os
import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/auto-update.sh"


class AutoUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls"
        self.env = {**os.environ, "HOME": str(self.root / 'Sam & <test>'),
                    "PATH": f"{self.bin}:{os.environ['PATH']}", "CALLS": str(self.calls),
                    "RUNNING": "1", "INSTALLED": "0", "OUTDATED": "yes"}
        self.write("brew", '''#!/bin/bash
printf '%s\\n' "$*" >> "$CALLS"
case "$1" in
  list) exit "${INSTALLED:-0}" ;;
  outdated) [[ "${OUTDATED:-yes}" = yes ]] && echo thatguysam-try-omarchy; exit 0 ;;
  fetch) [[ "${START_DURING_FETCH:-no}" = yes ]] && touch "$CALLS.running"; exit 0 ;;
  update) exit "${UPDATE_RESULT:-0}" ;;
esac
exit 0
''')
        self.write("pgrep", '''#!/bin/bash
[[ -e "$CALLS.running" ]] && exit 0
exit "${RUNNING:-1}"
''')
        self.write("launchctl", '#!/bin/bash\nprintf "launchctl %s\\n" "$*" >> "$CALLS"\n')
        self.write("plutil", '#!/bin/bash\nexit 0\n')

    def write(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def run_core(self, **overrides):
        return subprocess.run(["bash", "-c", 'source "$1"; run_update "$2"', "test",
                               str(SCRIPT), str(self.bin / "brew")],
                              env={**self.env, **overrides}, capture_output=True, text=True)

    def commands(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def test_running_app_skips_all_changes(self):
        result = self.run_core(RUNNING="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("update\n", self.commands())
        self.assertNotIn("upgrade", self.commands())

    def test_process_inspection_error_fails_closed(self):
        result = self.run_core(RUNNING="2")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("upgrade", self.commands())

    def test_only_named_cask_upgraded(self):
        result = self.run_core()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("upgrade --cask --require-sha --no-quit thatguysam/tap/thatguysam-try-omarchy", self.commands())
        self.assertNotIn("install --cask", self.commands())

    def test_current_app_skips_download_and_upgrade(self):
        result = self.run_core(OUTDATED="no")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("fetch", self.commands())
        self.assertNotIn("upgrade", self.commands())

    def test_missing_cask_is_not_reinstalled(self):
        result = self.run_core(INSTALLED="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("update\n", self.commands())

    def test_app_started_during_download_skips_upgrade(self):
        result = self.run_core(START_DURING_FETCH="yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fetch --cask", self.commands())
        self.assertNotIn("upgrade", self.commands())

    def test_brew_update_failure_stops_upgrade(self):
        result = self.run_core(UPDATE_RESULT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("upgrade", self.commands())

    def test_launchagent_escapes_paths_and_copies_helper(self):
        result = subprocess.run(["bash", "-c", 'source "$1"; enable', 'test', str(SCRIPT)],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        home = Path(self.env["HOME"])
        path = home / "Library/LaunchAgents/com.thatguysam.homebrew.try-omarchy.plist"
        data = plistlib.loads(path.read_bytes())
        self.assertEqual(data["StartInterval"], 21600)
        self.assertTrue(data["RunAtLoad"])
        self.assertEqual(data["EnvironmentVariables"]["HOME"], str(home))
        self.assertEqual(data["ProgramArguments"][-1], str(self.bin / "brew"))
        self.assertEqual(Path(data["ProgramArguments"][1]).read_text(), SCRIPT.read_text())


if __name__ == "__main__":
    unittest.main()
