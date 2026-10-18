cask "thatguysam-try-omarchy" do
  version "1.0.1"
  sha256 "7ff394327b9a93ab1469ce4df192a66be8d356405a9659405dfb7ba42e0b0b52"

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
