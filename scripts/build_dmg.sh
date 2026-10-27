#!/bin/bash
# Package dist/HOBO Reader v2 Pro Max.app into a drag-to-Applications DMG (builds the app first if missing).
# Usage: scripts/build_dmg.sh [--release]   (--release also publishes it to GitHub Releases via gh)
set -e
cd "$(dirname "$0")/.."
NAME="HOBO Reader v2 Pro Max"
APP="dist/$NAME.app"
[ -d "$APP" ] || ./scripts/build_app.sh
VERSION=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' hobo/version.py)
DMG="dist/HOBO-Reader-$VERSION.dmg"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cat > "$STAGE/READ ME FIRST.txt" <<TXT
Install: drag "$NAME" onto the Applications folder.

First launch (macOS blocks apps that are not from the App Store the first time):
  1. Open Applications and double-click "$NAME". macOS will refuse.
  2. Open System Settings > Privacy & Security, scroll down, and click "Open Anyway".
     (On older macOS: right-click the app > Open > Open.)
  3. You only have to do this once.

Before reading a logger, quit HOBOware and plug in the base station.
TXT

rm -f "$DMG"
hdiutil create -volname "$NAME" -srcfolder "$STAGE" -fs HFS+ -format UDZO -ov "$DMG" >/dev/null
echo "Built: $PWD/$DMG"

if [ "$1" = "--release" ]; then
    gh release create "v$VERSION" "$DMG" --title "HOBO Reader $VERSION" --notes "Download the DMG, drag the app to Applications, and follow READ ME FIRST.txt on first launch."
fi
