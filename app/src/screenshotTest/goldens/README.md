# Per-flavor screenshot goldens

These are the reference images for the theme screenshot test
(`AppThemePreview` in `ThemeScreenshotTest.kt`). There is **one golden per
flavor**, captured from a render of the test *after* `apply-flavor-action` has
rewritten the Compose theme for that flavor.

## Naming convention

```
<app name>.png
```

The file name is the flavor's **exact `app_name`** (the same value that appears
in the white-label build matrix and in the per-flavor job name), e.g.:

| Flavor / `app_name` | Golden file          |
| ------------------- | -------------------- |
| `Cara de Pastel`    | `Cara de Pastel.png` |
| `Pão Duro`          | `Pão Duro.png`       |
| `To Com Fome`       | `To Com Fome.png`    |

## How they are used

The Compose screenshot plugin validates `AppThemePreview` against a single
canonical reference path
(`app/src/screenshotTestDebug/reference/.../AppThemePreview_748aa731_0.png`,
git-ignored). Before validation runs, the white-label matrix calls
`scripts/select-screenshot-golden.sh "<app name>"`, which copies the golden for
the flavor currently being built into that canonical path. Each flavor is thus
validated against its own golden.

## Regenerating a golden

1. Apply the flavor locally (run `apply-flavor-action` with that flavor's JSON,
   `project-type: android-native-compose`).
2. `./gradlew :app:updateDebugScreenshotTest`
3. Copy the produced
   `app/src/screenshotTestDebug/reference/.../AppThemePreview_748aa731_0.png`
   to `app/src/screenshotTest/goldens/<app name>.png`.
4. Revert the working-tree changes the action made.

In CI these were initially captured from the white-label matrix's recorded
screenshot artifacts (one per flavor).
