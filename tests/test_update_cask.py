import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_cask", ROOT / "scripts/update_cask.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def release(version="0.4.2", checksum="a" * 64):
    base = "https://github.com/omacom/try-omarchy/releases"
    return {
        "tag_name": f"v{version}", "draft": False, "prerelease": False,
        "html_url": f"{base}/tag/v{version}",
        "assets": [{"name": "TryOmarchy.dmg", "state": "uploaded", "size": 100,
                    "digest": f"sha256:{checksum}",
                    "browser_download_url": f"{base}/download/v{version}/TryOmarchy.dmg"}],
    }


class UpdateTests(unittest.TestCase):
    def setUp(self):
        # Fixed fixtures: tests must keep passing after automated version bumps.
        self.text = 'cask "example" do\n  version "0.4.1"\n  sha256 "' + "b" * 64 + '"\n  app "Try Omarchy.app"\nend\n'

    def test_update_changes_only_two_lines(self):
        updated, version = updater.render_update(self.text, release())
        self.assertEqual(version, "0.4.2")
        expected = self.text.replace('version "0.4.1"', 'version "0.4.2"').replace("b" * 64, "a" * 64)
        self.assertEqual(updated, expected)

    def test_idempotent(self):
        updated, _ = updater.render_update(self.text, release())
        self.assertEqual(updater.render_update(updated, release())[0], updated)

    def test_numeric_version_comparison(self):
        self.assertIn('version "0.10.0"', updater.render_update(self.text, release("0.10.0"))[0])

    def test_refuses_downgrade(self):
        with self.assertRaisesRegex(ValueError, "downgrade"):
            updater.render_update(self.text, release("0.3.9"))

    def test_refuses_replaced_asset(self):
        with self.assertRaisesRegex(ValueError, "Same-version"):
            updater.render_update(self.text, release("0.4.1"))

    def test_current_release_unchanged(self):
        self.assertEqual(updater.render_update(self.text, release("0.4.1", "b" * 64))[0], self.text)

    def test_rejects_prereleases_and_drafts(self):
        for key in ("draft", "prerelease"):
            data = release()
            data[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                updater.stable_release(data)

    def test_rejects_unsafe_tags(self):
        for version in ("0.4.2-beta", "01.2.3", '0.4.2"; system("id")', "0.4.2\nfoo", "1.2"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                updater.stable_release(release(version))

    def test_missing_duplicate_or_renamed_asset(self):
        for assets in ([], [release()["assets"][0]] * 2, [{"name": "new.dmg"}]):
            data = release()
            data["assets"] = assets
            with self.subTest(assets=assets), self.assertRaises(ValueError):
                updater.stable_release(data)

    def test_bad_checksums(self):
        for digest in (None, "", "sha256:" + "z" * 64, "md5:" + "a" * 32):
            data = release()
            data["assets"][0]["digest"] = digest
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                updater.stable_release(data)

    def test_bad_asset_metadata(self):
        for key, value in (("browser_download_url", "https://evil.example/a.dmg"),
                           ("state", "new"), ("size", 0), ("size", True), ("size", 11 * 1024**3)):
            data = release()
            data["assets"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                updater.stable_release(data)

    def test_wrong_release_repository(self):
        data = release()
        data["html_url"] = "https://github.com/other/repo/releases/tag/v0.4.2"
        with self.assertRaises(ValueError):
            updater.stable_release(data)

    def test_unexpected_recipe_shape(self):
        for text in ("", self.text + self.text, self.text.replace('sha256 "', 'sha512 "')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                updater.render_update(text, release())

    def test_checked_in_recipe_has_safe_constraints(self):
        text = updater.CASK.read_text()
        self.assertEqual(len(updater.VERSION_LINE.findall(text)), 1)
        self.assertEqual(len(updater.SHA_LINE.findall(text)), 1)
        for required in ('depends_on arch: :arm64', 'depends_on macos: :sequoia',
                         'app "Try Omarchy.app"', 'strategy :github_latest'):
            self.assertIn(required, text)
        for forbidden in ("sha256 :no_check", "auto_updates true", "uninstall quit:", "signal:"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
