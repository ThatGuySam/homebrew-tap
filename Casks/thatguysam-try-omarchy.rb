cask "thatguysam-try-omarchy" do
  version "0.5.1"
  sha256 "03760f542025600ef29f77319c93d7c3640a3b15fcf73bda75b9caa9fcbd9999"

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
