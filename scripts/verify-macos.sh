#!/bin/bash
# Packaging checks only: never boot the VM. Use a disposable GitHub Actions Mac.
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" = true ]] || { echo "Run this only on a disposable CI Mac." >&2; exit 1; }
[[ "$(uname -s)" = Darwin && "$(uname -m)" = arm64 ]] || exit 1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASK="thatguysam/tap/thatguysam-try-omarchy"
APP="/Applications/Try Omarchy.app"
[[ ! -e "$APP" ]] || { echo "Refusing to replace an existing app in verification." >&2; exit 1; }
export HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ASK=1
brew update
export HOMEBREW_NO_AUTO_UPDATE=1
TAP="$(brew --repository)/Library/Taps/thatguysam/homebrew-tap"
mkdir -p "$(dirname "$TAP")"
if [[ ! -e "$TAP" ]]; then
  ln -s "$ROOT" "$TAP"
fi
[[ "$(cd "$TAP" && pwd -P)" = "$(cd "$ROOT" && pwd -P)" ]] || exit 1
brew style "$ROOT/Casks/thatguysam-try-omarchy.rb"
brew audit --cask "$CASK"
brew install --cask --require-sha "$CASK"
test -d "$APP"
/usr/bin/codesign --verify --deep --strict --verbose=2 "$APP"
/usr/sbin/spctl --assess --type execute --verbose=2 "$APP"
[[ "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Contents/Info.plist")" = dev.tryomarchy.native ]]
[[ "$(/usr/bin/lipo -archs "$APP/Contents/MacOS/omarchy-vm-helper")" = arm64 ]]
# A changed OS minimum requires review and an explicit cask dependency change.
MINIMUM="$(/usr/libexec/PlistBuddy -c 'Print :LSMinimumSystemVersion' "$APP/Contents/Info.plist")"
[[ "$MINIMUM" = 15.0 || "$MINIMUM" = 15.0.0 ]] || { echo "Review changed macOS minimum: $MINIMUM" >&2; exit 1; }
brew uninstall --cask "$CASK"
[[ ! -e "$APP" ]]
echo "Verified checksum, Homebrew install/uninstall, ARM64 architecture, bundle identity, signature and Gatekeeper. VM was not booted."
