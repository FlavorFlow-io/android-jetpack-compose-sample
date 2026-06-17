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
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.android.tools.screenshot.PreviewTest

/**
 * Per-flavor Compose Preview Screenshot Tests that validate theme application.
 *
 * There is one `@PreviewTest @Preview` per FlavorFlow client, each rendering the
 * shared UI under that flavor's brand colors. Running
 * `./gradlew :app:updateDebugScreenshotTest` writes one golden per flavor under
 * `app/src/screenshotTestDebug/reference/`; `validateDebugScreenshotTest` then
 * verifies the rendered output still matches. When a flavor's theme changes, its
 * golden changes — which is what proves theme application works.
 *
 * `@PreviewTest` (from com.android.tools.screenshot) is REQUIRED — only previews
 * carrying it are picked up by the screenshot-test engine.
 *
 * Colors mirror each client's `theme.light` from the FlavorFlow API for project
 * 0RAF99wHJEFM6otnO0Xo. They're declared here (rather than read from the live
 * theme) so each flavor renders deterministically in isolation.
 */
private data class FlavorBrand(
    val name: String,
    val primary: Color,
    val secondary: Color,
    val tertiary: Color,
    val background: Color = Color(0xFFF7F9FB),
    val onPrimary: Color = Color.White,
    val onSecondary: Color = Color.White,
)

private val CaraDePastel = FlavorBrand(
    name = "Cara de Pastel",
    primary = Color(0xFF6B4CFF),
    secondary = Color(0xFF22C55E),
    tertiary = Color(0xFF0000FF),
)

private val PaoDuro = FlavorBrand(
    name = "Pão Duro",
    primary = Color(0xFF6B4CFF),
    secondary = Color(0xFF22C55E),
    tertiary = Color(0xFF0000FF),
)

private val ToComFome = FlavorBrand(
    name = "To Com Fome",
    primary = Color(0xFF6B4CFF),
    secondary = Color(0xFF22C55E),
    tertiary = Color(0xFF0000FF),
)

/** Renders the shared UI under a flavor's brand colors. */
@Composable
private fun FlavorThemePreview(brand: FlavorBrand) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = brand.primary,
            onPrimary = brand.onPrimary,
            secondary = brand.secondary,
            onSecondary = brand.onSecondary,
            tertiary = brand.tertiary,
            background = brand.background,
        )
    ) {
        Surface(color = MaterialTheme.colorScheme.background) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text(text = brand.name, color = MaterialTheme.colorScheme.onBackground)
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
}

@Composable
private fun ColorChip(name: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(color = color, modifier = Modifier.size(56.dp), content = {})
        Text(text = name, color = MaterialTheme.colorScheme.onBackground)
    }
}

@PreviewTest
@Preview(name = "Cara de Pastel", showBackground = true)
@Composable
fun CaraDePastelThemePreview() = FlavorThemePreview(CaraDePastel)

@PreviewTest
@Preview(name = "Pão Duro", showBackground = true)
@Composable
fun PaoDuroThemePreview() = FlavorThemePreview(PaoDuro)

@PreviewTest
@Preview(name = "To Com Fome", showBackground = true)
@Composable
fun ToComFomeThemePreview() = FlavorThemePreview(ToComFome)
