# Sam's Homebrew tap

[![Validate tap](https://github.com/ThatGuySam/homebrew-tap/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatGuySam/homebrew-tap/actions/workflows/ci.yml)

An unofficial Homebrew cask for [Try Omarchy](https://github.com/omacom/try-omarchy). Downloads the original release DMG directly from upstream; no repackaged binaries or forked app. Requires an Apple Silicon Mac running macOS 15 (Sequoia) or later.

## Install

```sh
brew install --cask thatguysam/tap/thatguysam-try-omarchy
```

The username prefix prevents collisions with a future official Homebrew cask. Homebrew adds the tap automatically. Open **Try Omarchy** from Applications after installation.

### Already installed from a DMG?

Shut down the guest and quit Try Omarchy first, then try adopting the identical app:

```sh
brew install --cask --adopt thatguysam/tap/thatguysam-try-omarchy
```

`--adopt` only works when the existing app matches the downloaded app. If Homebrew refuses, move **only `Try Omarchy.app`** from Applications to a backup location, then run the normal install command. Do not delete the VM storage or use Factory Reset. Keep a backup of important guest data before switching installation methods.

## Updates: two separate layers

**The tap:** GitHub Actions checks upstream's latest stable release daily at 10:23 UTC. It creates a candidate version/checksum change, runs tests and Mac packaging checks, and commits only after they pass. It rejects prereleases, downgrades, changed same-version assets, missing checksums, unexpected download URLs, and unreviewed changes to the app's minimum macOS requirement. A new release is downloaded only when the version changes. No personal access token or external service is required; the workflow uses the repository's `GITHUB_TOKEN`.

**Your Mac:** Homebrew does not automatically install upgrades just because a cask changed. Either run:

```sh
# Shut down the guest and quit Try Omarchy first.
brew update
brew upgrade --cask thatguysam/tap/thatguysam-try-omarchy
```

Or enable the opt-in per-user updater:

```sh
bash "$(brew --repository thatguysam/tap)/scripts/auto-update.sh" enable
```

The helper runs immediately when enabled, at login, and approximately every six hours while logged in. It refreshes Homebrew and its package definitions, but upgrades only this named app. It checks for the app/VM process before updating and again after downloading, skips if running, never forces the app to quit, and refuses to reinstall an app you removed. It requires no sudo. Failed operations are logged and retried on the next scheduled run.

Process checks reduce interruption risk but are not an atomic lock against launching the app at the exact same time as an upgrade. Keep backups; no updater can guarantee the safety or compatibility of an upstream release. For strict control, leave automatic installation disabled and upgrade manually with the app closed.

Check or disable the helper:

```sh
bash "$(brew --repository thatguysam/tap)/scripts/auto-update.sh" status
bash "$(brew --repository thatguysam/tap)/scripts/auto-update.sh" disable
```

Logs are in `~/Library/Logs/ThatGuySam Homebrew/try-omarchy.log`. The LaunchAgent is `~/Library/LaunchAgents/com.thatguysam.homebrew.try-omarchy.plist`. The helper is copied to `~/Library/Application Support/ThatGuySam Homebrew/auto-update.sh`, so updating the tap cannot rewrite a running shell script. Re-run `enable` to install a newer helper. Automatic global Homebrew cleanup is disabled for these runs; old download caches can consume disk space.

GitHub can disable public-repository scheduled workflows after 60 days without repository activity. Check the Actions tab if release tracking stops; re-enable **Update Try Omarchy** there and use **Run workflow** to check immediately. A failed signing or packaging check leaves the previous cask version in place. Repository rules that block direct bot commits will also require a manual update or a reviewed PR workflow; this project does not bypass branch protection.

## Your Linux VM is separate

This cask replaces only the Mac app. It does not run the Linux updater, migrate your guest disk, or apply every change from a new factory image to an existing VM. Use Omarchy's supported updater inside the guest. Neither ordinary uninstall nor this cask's `--zap` stanza removes VM disks or shared folders; `--zap` removes only the named Mac preferences file and can forget saved preferences. Factory Reset is destructive and is not an update mechanism.

## Validation and maintenance

```sh
python3 -m unittest discover -s tests -v
ruby -c Casks/thatguysam-try-omarchy.rb
for script in scripts/*.sh; do bash -n "$script"; done
python3 scripts/update_cask.py --check
```

The Python updater/tests use only the standard library (Python 3.9+); the Mac helper uses Bash and built-in macOS utilities. CI runs unit tests, Homebrew style/audit, actual DMG checksum validation, install/uninstall, bundle identity and architecture checks, code-signature verification, and Gatekeeper assessment on an ARM64 macOS 15 runner. CI **does not boot the Linux VM** or prove guest-update compatibility. The badge/Actions logs report results, not this README.

To update a candidate manually, run `python3 scripts/update_cask.py`, review the two changed cask fields, then run Mac packaging checks on a disposable runner before publishing. Never replace a checksum merely to silence a mismatch.

See [the official Homebrew submission checklist](docs/upstream-submission.md) for the separate upstream contribution. No official Homebrew PR is opened automatically. Initial implementation was AI-assisted.

## References

- [Homebrew taps and unique cask names](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Cask Cookbook](https://docs.brew.sh/Cask-Cookbook)
- [Homebrew command reference](https://docs.brew.sh/Manpage)
- [GitHub scheduled workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Apple launchd jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)

The tap's code is MIT-licensed. Upstream software and marks retain their respective licenses and ownership.
