#!/bin/bash
# Opt-in per-user updater. No sudo, no forced quits, no VM reset or disk deletion.
set -euo pipefail

LABEL="com.thatguysam.homebrew.try-omarchy"
CASK="thatguysam/tap/thatguysam-try-omarchy"
STATE="$HOME/Library/Application Support/ThatGuySam Homebrew"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/ThatGuySam Homebrew"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
fail() { printf '%s\n' "$*" >&2; exit 1; }
xml() { printf '%s' "$1" | sed -e 's/\&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/"/\&quot;/g' -e "s/'/\&apos;/g"; }

# Any matching launcher/VM process blocks replacement. Unexpected pgrep errors
# also block replacement instead of being mistaken for "no process".
require_idle() {
  local result
  if pgrep -f '[/]Try Omarchy[.]app/Contents/|[o]marchy-vm-helper' >/dev/null; then
    log "Try Omarchy is running; skipping this update."
    return 1
  else
    result=$?
    [[ "$result" -eq 1 ]] || fail "Unable to inspect processes; refusing upgrade."
  fi
}

run_update() {
  local brew_bin="${1:-}" outdated
  [[ "$brew_bin" = /* && -x "$brew_bin" ]] || fail "An absolute Homebrew executable path is required."
  export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1
  export HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1 HOMEBREW_NO_ASK=1
  export HOMEBREW_NO_UPGRADE_QUIT_CASKS=1
  # Do not install a missing app or re-install one the user removed.
  if ! "$brew_bin" list --cask "$CASK" >/dev/null 2>&1; then
    log "This tap's Try Omarchy cask is not installed; skipping."
    return 0
  fi
  require_idle || return 0
  "$brew_bin" update
  outdated="$("$brew_bin" outdated --cask --quiet "$CASK")"
  if [[ -z "$outdated" ]]; then
    log "Try Omarchy is current."
    return 0
  fi
  # Download and verify first, so the last running-app check is close to upgrade.
  "$brew_bin" fetch --cask "$CASK"
  require_idle || return 0
  "$brew_bin" upgrade --cask --require-sha --no-quit "$CASK" </dev/null
  log "Try Omarchy upgrade completed."
}

enable() {
  local brew_bin source_file temporary
  brew_bin="$(command -v brew)"
  [[ "$brew_bin" = /* && -x "$brew_bin" ]] || fail "Homebrew must be installed and on PATH."
  "$brew_bin" list --cask "$CASK" >/dev/null 2>&1 || fail "Install $CASK before enabling updates."
  source_file="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  mkdir -p "$STATE" "$LOG_DIR" "$(dirname "$PLIST")"
  # Keep a reviewed copy: brew update must not modify the executing shell script.
  if [[ "$source_file" != "$STATE/auto-update.sh" ]]; then
    cp "$source_file" "$STATE/auto-update.sh"
    chmod 700 "$STATE/auto-update.sh"
  fi
  temporary="$(mktemp "$PLIST.XXXXXX")"
  cat > "$temporary" <<PLIST_XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string>
    <string>$(xml "$STATE/auto-update.sh")</string>
    <string>run</string>
    <string>$(xml "$brew_bin")</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>HOME</key><string>$(xml "$HOME")</string>
    <key>PATH</key><string>$(xml "$(dirname "$brew_bin"):/usr/bin:/bin:/usr/sbin:/sbin")</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>21600</integer>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$(xml "$LOG_DIR/try-omarchy.log")</string>
  <key>StandardErrorPath</key><string>$(xml "$LOG_DIR/try-omarchy.log")</string>
</dict></plist>
PLIST_XML
  if ! plutil -lint "$temporary"; then
    rm -f "$temporary"
    fail "Invalid LaunchAgent property list; previous configuration is unchanged."
  fi
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  mv "$temporary" "$PLIST"
  chmod 600 "$PLIST"
  launchctl enable "gui/$(id -u)/$LABEL"
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  log "Enabled: on login and every six hours while logged in."
  log "Only Try Omarchy is upgraded; logs: $LOG_DIR/try-omarchy.log"
}

main() {
  [[ "$(uname -s)" = Darwin ]] || fail "This helper requires macOS."
  [[ "$(id -u)" -ne 0 ]] || fail "Run as your normal user, not with sudo."
  case "${1:-help}" in
    enable) enable ;;
    run) run_update "${2:-}" ;;
    disable)
      launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
      rm -f "$PLIST"
      log "Disabled. App, virtual machines, logs and helper copy were retained."
      ;;
    status) launchctl print "gui/$(id -u)/$LABEL" ;;
    *) printf 'Usage: bash %s {enable|disable|status|run /absolute/path/to/brew}\n' "$0" ;;
  esac
}

# Sourcing exposes the core functions for hermetic tests; it performs no writes.
if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
