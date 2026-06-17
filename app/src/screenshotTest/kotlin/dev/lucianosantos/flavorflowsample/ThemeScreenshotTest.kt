package dev.lucianosantos.flavorflowsample

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.android.tools.screenshot.PreviewTest
import dev.lucianosantos.flavorflowsample.ui.theme.FlavorFlowSampleTheme

/**
 * Screenshot test that validates theme application.
 *
 * Nothing here is flavor-specific: it renders the app's own `FlavorFlowSampleTheme`
 * and reads the app name from resources (`R.string.app_name`). Both are rewritten
 * per client at build time by the FlavorFlow apply-flavor-action (which runs after
 * fetch-flavors-action in the build-white-label matrix), so the rendered colours
 * and name are whatever the applied flavor sets — proving theme application works
 * without hardcoding anything.
 *
 * `dynamicColor = false` forces the app's (flavor-driven) color scheme instead of
 * the device's Material You colors, so the render is deterministic.
 *
 * - Base repo: the golden reflects the default theme (guarded by screenshot-test.yml).
 * - White-label matrix: each flavor records its own screenshot after apply-flavor.
 *
 * `@PreviewTest` (com.android.tools.screenshot) is REQUIRED for the engine to pick
 * up the preview.
 */
@Composable
private fun ThemeShowcase() {
    Surface(color = MaterialTheme.colorScheme.background) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // App name comes from resources — apply-flavor sets it per client.
            Text(
                text = stringResource(R.string.app_name),
                color = MaterialTheme.colorScheme.onBackground,
            )
            // Colours come from the live theme — apply-flavor rewrites the scheme.
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ColorChip("primary", MaterialTheme.colorScheme.primary)
                ColorChip("secondary", MaterialTheme.colorScheme.secondary)
                ColorChip("tertiary", MaterialTheme.colorScheme.tertiary)
            }
            Button(
                onClick = {},
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            ) { Text("Primary button") }
            Button(
                onClick = {},
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.secondary,
                    contentColor = MaterialTheme.colorScheme.onSecondary,
                ),
            ) { Text("Secondary button") }
        }
    }
}

@Composable
private fun ColorChip(name: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(color = color, modifier = Modifier.size(56.dp), content = {})
        Text(text = name, color = MaterialTheme.colorScheme.onBackground)
    }
}

@PreviewTest
@Preview(showBackground = true)
@Composable
fun AppThemePreview() {
    FlavorFlowSampleTheme(dynamicColor = false) {
        ThemeShowcase()
    }
}
