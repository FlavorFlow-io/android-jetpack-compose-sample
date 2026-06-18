#!/usr/bin/env bash
#
# Selects the committed golden image for a flavor (by its app name) and copies it
# into the canonical reference path that the Compose Preview Screenshot Testing
# plugin validates against.
#
# There is ONE screenshot test (AppThemePreview in ThemeScreenshotTest.kt) and
# therefore ONE reference path. We keep a per-flavor golden for each flavor under
# app/src/screenshotTest/goldens/<app name>.png and swap the matching one into the
# reference path right before `validateDebugScreenshotTest`, so every flavor in the
# white-label matrix is validated against ITS OWN golden — not a single universal
# image.
#
# Usage: scripts/select-screenshot-golden.sh "<app name>"
#   e.g. scripts/select-screenshot-golden.sh "To Com Fome"
set -euo pipefail

APP_NAME="${1:-}"
if [ -z "$APP_NAME" ]; then
  echo "::error::Usage: select-screenshot-golden.sh <app name>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GOLDENS_DIR="$REPO_ROOT/app/src/screenshotTest/goldens"
GOLDEN="$GOLDENS_DIR/${APP_NAME}.png"

# The plugin derives this filename from the preview function signature; it is
# stable as long as AppThemePreview's signature does not change.
REF_DIR="$REPO_ROOT/app/src/screenshotTestDebug/reference/dev/lucianosantos/flavorflowsample/ThemeScreenshotTestKt"
REF_FILE="$REF_DIR/AppThemePreview_748aa731_0.png"

if [ ! -f "$GOLDEN" ]; then
  echo "::error::No committed golden image for app name '$APP_NAME' (expected $GOLDEN)." >&2
  echo "Committed goldens are:" >&2
  ls -1 "$GOLDENS_DIR" >&2 || true
  exit 1
fi

mkdir -p "$REF_DIR"
cp "$GOLDEN" "$REF_FILE"
echo "Selected golden for '$APP_NAME' -> $REF_FILE"
