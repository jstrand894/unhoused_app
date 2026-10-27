#!/bin/bash
# Build "Unhoused Reader Pro.app" into dist/. Needs the project venv (pyinstaller) and Homebrew libusb.
set -e
cd "$(dirname "$0")/.."
LIBUSB=$(python3 -c 'import os;print(os.path.realpath("/opt/homebrew/lib/libusb-1.0.0.dylib"))')
for i in 1 2 3 4 5; do rm -rf build dist && break; sleep 1; done   # Finder may recreate .DS_Store mid-delete
.venv/bin/pyinstaller --noconfirm --windowed \
    --name "Unhoused Reader Pro" \
    --icon assets/app.icns \
    --osx-bundle-identifier com.jstrand.unhousedreader \
    --add-data "hobo/assets:hobo/assets" \
    --add-binary "$LIBUSB:." \
    run_app.py
# stamp the version into the bundle (shows in Finder > Get Info) and re-sign, since editing breaks the signature
VERSION=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' hobo/version.py)
APP="dist/Unhoused Reader Pro.app"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$APP/Contents/Info.plist" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$APP/Contents/Info.plist" 2>/dev/null || true
codesign --force --deep -s - "$APP" >/dev/null 2>&1
echo "Version $VERSION"
echo "Built: $PWD/dist/Unhoused Reader Pro.app"
