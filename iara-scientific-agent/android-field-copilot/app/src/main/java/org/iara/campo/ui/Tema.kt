package org.iara.campo.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import org.iara.campo.R

/**
 * Identidade visual "Folha-gota" (docs/IDENTIDADE_VISUAL.md).
 * Cores com contraste AA sobre palha; textos com no mínimo 15 sp no app.
 */
object Cores {
    val VerdeCopaiba = Color(0xFF1F4A33)
    val RioNegro = Color(0xFF1D3B4F)
    val RoxoAcai = Color(0xFF5A2A50)
    val Urucum = Color(0xFFA3401F)
    val Palha = Color(0xFFF3EDDD)
    val Papel = Color(0xFFFBF8F0)
    val Jenipapo = Color(0xFF1B1E1A)
    val Texto2 = Color(0xFF3D4A41)
    val Borda = Color(0xFFD6CCB4)
    val AguaClara = Color(0xFF9CC3D5)
    val VerdeClaro = Color(0xFFDDE8DF)
    val UrucumClaro = Color(0xFFF5DED4)
}

val YoungSerif = FontFamily(Font(R.font.young_serif))
val EbGaramondItalico = FontFamily(Font(R.font.eb_garamond_italic, FontWeight.Normal, FontStyle.Italic))
val WorkSans = FontFamily(
    Font(R.font.work_sans_regular, FontWeight.Normal),
    Font(R.font.work_sans_medium, FontWeight.Medium),
    Font(R.font.work_sans_semibold, FontWeight.SemiBold),
)

private val Tipografia = Typography(
    headlineLarge = TextStyle(fontFamily = YoungSerif, fontSize = 30.sp, lineHeight = 34.sp),
    headlineSmall = TextStyle(fontFamily = YoungSerif, fontSize = 22.sp, lineHeight = 28.sp),
    titleLarge = TextStyle(fontFamily = YoungSerif, fontSize = 20.sp, lineHeight = 26.sp),
    titleMedium = TextStyle(fontFamily = WorkSans, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 22.sp),
    bodyLarge = TextStyle(fontFamily = WorkSans, fontSize = 16.sp, lineHeight = 23.sp),
    bodyMedium = TextStyle(fontFamily = WorkSans, fontSize = 15.sp, lineHeight = 21.sp),
    bodySmall = TextStyle(fontFamily = WorkSans, fontSize = 14.sp, lineHeight = 19.sp),
    labelLarge = TextStyle(fontFamily = WorkSans, fontWeight = FontWeight.SemiBold, fontSize = 15.sp),
    labelMedium = TextStyle(fontFamily = WorkSans, fontWeight = FontWeight.SemiBold, fontSize = 13.sp),
)

private val Esquema = lightColorScheme(
    primary = Cores.VerdeCopaiba,
    onPrimary = Cores.Papel,
    primaryContainer = Cores.VerdeClaro,
    onPrimaryContainer = Cores.VerdeCopaiba,
    secondary = Cores.RioNegro,
    onSecondary = Cores.Papel,
    secondaryContainer = Cores.VerdeClaro,
    onSecondaryContainer = Cores.VerdeCopaiba,
    tertiary = Cores.RoxoAcai,
    background = Cores.Palha,
    onBackground = Cores.Jenipapo,
    surface = Cores.Papel,
    onSurface = Cores.Jenipapo,
    surfaceVariant = Cores.Palha,
    onSurfaceVariant = Cores.Texto2,
    outline = Cores.Borda,
    error = Cores.Urucum,
)

@Composable
fun IaraTema(conteudo: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Esquema, typography = Tipografia, content = conteudo)
}
