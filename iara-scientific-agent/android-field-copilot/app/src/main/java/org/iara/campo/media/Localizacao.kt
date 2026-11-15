package org.iara.campo.media

import android.annotation.SuppressLint
import android.content.Context
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.tasks.await

data class Posicao(val latitude: Double, val longitude: Double, val precisaoM: Float)

/**
 * Lê a posição atual com o FusedLocationProvider.
 * O GPS funciona sem internet (usa satélites); só demora mais no primeiro uso.
 * A permissão de localização é pedida pela tela antes de chamar esta função.
 */
object Localizacao {
    @SuppressLint("MissingPermission")
    suspend fun atual(context: Context): Posicao? {
        val cliente = LocationServices.getFusedLocationProviderClient(context)
        val local = cliente.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, CancellationTokenSource().token).await()
            ?: return null
        return Posicao(local.latitude, local.longitude, local.accuracy)
    }
}
