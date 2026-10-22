cask "thatguysam-try-omarchy" do
  version "1.2.0"
  sha256 "403e7695c824dc67448d9f273bd105c6a17db2e89fd120d9fc7df1d647af30ba"

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
