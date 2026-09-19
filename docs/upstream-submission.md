# Official Homebrew submission checklist

The personal tap works independently of acceptance into `Homebrew/homebrew-cask`.
This document is a checklist, not an assertion that the package has passed review.

1. Re-check the current [acceptance policy](https://docs.brew.sh/Package-Acceptance-Policy)
   and [acceptable casks](https://docs.brew.sh/Acceptable-Casks). The repository was
   created August 23, 2026; the normal 30-day threshold is reached September 22,
   2026, after its creation time. This is only one criterion, not guaranteed acceptance.
2. Search open and closed `Homebrew/homebrew-cask` PRs for `try-omarchy` and
   `omarchy` before opening a duplicate.
3. Fork `Homebrew/homebrew-cask` and copy the minimal recipe to
   `Casks/t/try-omarchy.rb`. Change its token from `thatguysam-try-omarchy` to
   `try-omarchy`. Do not submit this tap's scheduled updater or LaunchAgent.
4. Follow the current [contribution instructions](https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request).
   Run `brew style`, `brew audit --cask --new --online`, and installation/removal
   tests on the candidate. Test on the latest supported major macOS release too.
   Verify downloaded bytes, notarization, the bundle's actual minimum OS version,
   and that normal upgrades preserve an existing guest disk.
5. Launch the app, complete a disposable guest's setup and verify shutdown/relaunch
   on a real Apple Silicon Mac. Hosted CI cannot substitute for this VM smoke test.
6. Disclose AI assistance under Homebrew's current policy, personally review the
   changes, and follow its requirements for answering review comments.
7. After acceptance, document an explicit transition from the prefixed personal
   cask. Shut down the VM and preserve its storage. Do not install both casks over
   the same app or automatically remove users' installations.

Useful evidence for the PR: the upstream release URL, SHA-256, signature/Gatekeeper
output, successful audit logs, tested macOS/architecture, and an accurate statement
of what was and was not tested. Do not claim an upstream maintainer's endorsement.
