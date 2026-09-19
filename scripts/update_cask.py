#!/usr/bin/env python3
"""Update only a cask's version/checksum from a validated, stable GitHub release.

No third-party dependencies. The publishing workflow independently downloads the
DMG with Homebrew and checks its signature before committing this candidate.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASK = ROOT / "Casks/thatguysam-try-omarchy.rb"
REPO = "omacom/try-omarchy"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)")
VERSION_LINE = re.compile(r'^  version "([^"]+)"$', re.MULTILINE)
SHA_LINE = re.compile(r'^  sha256 "([0-9a-f]{64})"$', re.MULTILINE)


def stable_release(release: dict[str, Any]) -> tuple[str, str]:
    """Reject malformed, prerelease, redirected, and unhashed assets."""
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("Expected a published, non-prerelease release")
    tag = release.get("tag_name", "")
    if not isinstance(tag, str) or not tag.startswith("v") or not VERSION.fullmatch(tag[1:]):
        raise ValueError("Expected a stable vMAJOR.MINOR.PATCH tag")
    expected_release = f"https://github.com/{REPO}/releases/tag/{tag}"
    if release.get("html_url") != expected_release:
        raise ValueError("Unexpected release repository or URL")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Missing asset list")
    matches = [a for a in assets if isinstance(a, dict) and a.get("name") == "TryOmarchy.dmg"]
    if len(matches) != 1:
        raise ValueError("Expected exactly one TryOmarchy.dmg asset")
    asset = matches[0]
    expected_url = f"https://github.com/{REPO}/releases/download/{tag}/TryOmarchy.dmg"
    if asset.get("browser_download_url") != expected_url or asset.get("state") != "uploaded":
        raise ValueError("Unexpected asset URL or incomplete upload")
    size = asset.get("size")
    if type(size) is not int or not 0 < size <= 10 * 1024**3:
        raise ValueError("Invalid asset size (maximum 10 GiB)")
    digest = asset.get("digest", "")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Missing valid GitHub SHA-256 digest; manual review required")
    return tag[1:], digest.removeprefix("sha256:")


def render_update(text: str, release: dict[str, Any]) -> tuple[str, str]:
    version, digest = stable_release(release)
    versions, hashes = VERSION_LINE.findall(text), SHA_LINE.findall(text)
    if len(versions) != 1 or len(hashes) != 1 or not VERSION.fullmatch(versions[0]):
        raise ValueError("Expected exactly one pinned version and SHA-256 in cask")
    old = versions[0]
    if tuple(map(int, version.split("."))) < tuple(map(int, old.split("."))):
        raise ValueError(f"Refusing downgrade: {old} -> {version}")
    if version == old:
        if digest != hashes[0]:
            raise ValueError("Same-version asset changed: refusing to replace a trusted checksum")
        return text, version
    updated = VERSION_LINE.sub(lambda _: f'  version "{version}"', text)
    updated = SHA_LINE.sub(lambda _: f'  sha256 "{digest}"', updated)
    return updated, version


def fetch_release() -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ThatGuySam-homebrew-tap"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API_URL, headers=headers)
    # Never forward the API authorization header to a redirected host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    with urllib.request.build_opener(NoRedirect).open(request, timeout=45) as response:
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError("Oversized release response")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("Expected a release object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report candidate without modifying files")
    args = parser.parse_args()
    try:
        original = CASK.read_text(encoding="utf-8")
        updated, version = render_update(original, fetch_release())
        changed = updated != original
        if changed and not args.check:
            # Write in the same directory for an atomic replacement.
            temporary = CASK.with_suffix(".rb.tmp")
            try:
                temporary.write_text(updated, encoding="utf-8")
                temporary.replace(CASK)
            finally:
                temporary.unlink(missing_ok=True)
        if output := os.environ.get("GITHUB_OUTPUT"):
            with open(output, "a", encoding="utf-8") as stream:
                stream.write(f"changed={str(changed).lower()}\nversion={version}\n")
        print(f"{'Update available' if changed else 'Already current'}: {version}")
        return 0
    except (ValueError, OSError, urllib.error.URLError) as error:
        print(f"Release update failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
