# FlavorFlow — Jetpack Compose white-label sample

A complete, working example **and step-by-step guide** for shipping a single
Android (Jetpack Compose) app that is automatically re-branded for each of your
clients with [FlavorFlow](https://flavorflow.io).

## What is a white-label build?

With FlavorFlow you define your **clients** once — each with its own app name,
package / application id, colors, logo, and config. A GitHub Actions workflow
then fetches those clients and produces **one branded APK per client** from this
single codebase. No per-client branches, forks, or copy-paste.

The pipeline is two FlavorFlow actions wrapped around your normal Gradle build:

1. **[`fetch-flavors-action`](https://github.com/FlavorFlow-io/fetch-flavors-action)** —
   pulls every client from your project and emits them as a build matrix.
2. **[`apply-flavor-action`](https://github.com/FlavorFlow-io/apply-flavor-action)** —
   for each client, rewrites the app's branding (Compose theme, app name,
   package / application id, launcher icon) before the build.
3. **`./gradlew`** — builds the APK for that client.

The whole thing lives in [`.github/workflows/build-white-label.yml`](.github/workflows/build-white-label.yml).

## Build your own — step by step

1. **Create a project on [flavorflow.io](https://flavorflow.io)** and add a
   client for each brand (set its name, package name, and colors, and upload a
   logo).
2. **Grab your project API key and project ID** from the project settings.
3. **Make branding come from the theme, not from code.** This sample's
   `ui/theme/Theme.kt` + `Color.kt` are the stock Android Studio scaffold —
   that's all `apply-flavor-action` needs (it rewrites the color scheme and turns
   `dynamicColor` off). Keep reading brand values from
   `MaterialTheme.colorScheme` and `R.string.app_name`, never hardcoded.
4. **Copy [`.github/workflows/build-white-label.yml`](.github/workflows/build-white-label.yml)**
   into your repo.
5. **Add your credentials** under *Settings → Secrets and variables → Actions*:
   - Secret **`TEST_API_KEY`** → your project API key.
   - Variable **`TEST_PROJECT_ID`** → your project ID.

   (Rename them if you like — just keep the workflow in sync.)
6. **Push to `main`.** Actions builds one APK per client; download them from the
   run's **Artifacts**.

## What gets branded (and where)

`apply-flavor-action` (with `project-type: android-native-compose`) rewrites,
per client:

| What | Where |
| ---- | ----- |
| Colors / theme | `ui/theme/Color.kt` + `Theme.kt` (Material 3 color scheme) |
| App name | `res/values/strings.xml` → `app_name` |
| Package / application id | `app/build.gradle.kts` |
| Launcher icon | generated from the client logo |

## Theming approaches

This sample uses the **CI-plugin** approach (the action edits your theme
automatically). FlavorFlow supports two more — baking colors in at **build time**
via `BuildConfig`, or fetching the theme at **run time** from the API. Full guide:

**https://flavorflow.io/docs/platforms/android-jetpack-compose**

## Run it locally

```bash
./gradlew assembleDebug      # build the base (un-branded) app
```

---

### Note: the screenshot test

This repo also contains a screenshot test (`ThemeScreenshotTest`) with per-client
golden images. **You don't need any of this for your own white-label app** — it's
how *we* make sure `apply-flavor-action` keeps theming correctly as FlavorFlow
evolves. Feel free to ignore or delete it.
