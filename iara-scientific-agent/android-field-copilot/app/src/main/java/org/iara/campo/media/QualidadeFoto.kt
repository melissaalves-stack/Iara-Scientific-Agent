package org.iara.campo.media

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import org.json.JSONObject

/**
 * Avalia a qualidade da foto no próprio celular, sem internet.
 *
 * - Nitidez: variância do Laplaciano. O Laplaciano realça bordas; numa foto
 *   desfocada há poucas bordas, então a variância fica baixa.
 * - Brilho: média dos tons de cinza (0 = preto, 255 = branco).
 *
 * A imagem é reduzida para ~320 px antes do cálculo, para ser rápido.
 */
data class ResultadoQualidade(val nitidez: Double, val brilho: Double, val aprovada: Boolean, val motivo: String?) {
    fun toJson(): String = JSONObject()
        .put("nitidez", nitidez).put("brilho", brilho).put("aprovada", aprovada).put("motivo", motivo ?: JSONObject.NULL)
        .toString()
}

object QualidadeFoto {
    private const val NITIDEZ_MINIMA = 80.0
    private const val BRILHO_MINIMO = 50.0
    private const val BRILHO_MAXIMO = 225.0

    fun avaliar(context: Context, uri: Uri): ResultadoQualidade? {
        val bitmap = carregarReduzido(context, uri) ?: return null
        val w = bitmap.width
        val h = bitmap.height
        val pixels = IntArray(w * h)
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h)
        val cinza = DoubleArray(w * h) { i ->
            val p = pixels[i]
            0.299 * Color.red(p) + 0.587 * Color.green(p) + 0.114 * Color.blue(p)
        }

        val brilho = cinza.average()

        // Laplaciano 3x3: 4*centro - cima - baixo - esquerda - direita
        val valores = ArrayList<Double>((w - 2) * (h - 2))
        for (y in 1 until h - 1) {
            for (x in 1 until w - 1) {
                val i = y * w + x
                valores += 4 * cinza[i] - cinza[i - 1] - cinza[i + 1] - cinza[i - w] - cinza[i + w]
            }
        }
        val media = valores.average()
        val nitidez = valores.sumOf { (it - media) * (it - media) } / valores.size

        val problemas = buildList {
            if (nitidez < NITIDEZ_MINIMA) add("desfocada")
            if (brilho < BRILHO_MINIMO) add("muito escura")
            if (brilho > BRILHO_MAXIMO) add("muito clara")
        }
        val motivo = if (problemas.isEmpty()) null else "Foto ${problemas.joinToString(" e ")}. Tente de novo."
        return ResultadoQualidade(nitidez, brilho, problemas.isEmpty(), motivo)
    }

    private fun carregarReduzido(context: Context, uri: Uri): Bitmap? {
        val limites = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, limites) }
        var escala = 1
        while (limites.outWidth / (escala * 2) >= 320) escala *= 2
        val opcoes = BitmapFactory.Options().apply { inSampleSize = escala }
        return context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, opcoes) }
    }
}
