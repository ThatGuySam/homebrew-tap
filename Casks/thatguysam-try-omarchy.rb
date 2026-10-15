cask "thatguysam-try-omarchy" do
  version "0.6.0"
  sha256 "6e2e5b7b9d728b3ba697f3814418bee55f11aa3a54f3c82403566f8564fa36bc"

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
