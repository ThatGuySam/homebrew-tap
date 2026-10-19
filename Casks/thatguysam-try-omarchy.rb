cask "thatguysam-try-omarchy" do
  version "1.1.0"
  sha256 "85569dae25d22a2c070bceb5da48d53a5cf593f2e53f1c9d9f9dfeb117258e24"

  url "https://github.com/omacom/try-omarchy/releases/download/v#{version}/TryOmarchy.dmg"
  name "Try Omarchy"
  desc "Run the Omarchy Linux desktop in a virtual machine on Apple Silicon"
  homepage "https://github.com/omacom/try-omarchy"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64
  depends_on macos: :sequoia

  app "Try Omarchy.app"

  # Never remove virtual-machine disks or shared folders, even with --zap.
  zap trash: "~/Library/Preferences/dev.tryomarchy.native.plist"
end
