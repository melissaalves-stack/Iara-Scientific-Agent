package org.iara.campo.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import org.iara.campo.Preferencias
import org.iara.campo.data.AppDatabase
import org.iara.campo.data.RegistroEntity
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Envia a fila de registros para o backend quando houver internet.
 *
 * O WorkManager só executa este trabalho com rede disponível (Constraints) e
 * tenta de novo sozinho, com espera crescente, se a conexão cair no meio.
 * Como cada registro tem um UUID gerado no celular, reenviar não duplica
 * nada no servidor.
 */
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val dao = AppDatabase.get(applicationContext).registros()
        val pendentes = dao.pendentes()
        if (pendentes.isEmpty()) return@withContext Result.success()

        val prefs = Preferencias(applicationContext)
        val corpo = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart("pacote", montarPacote(pendentes, prefs).toString())
        pendentes.forEach { r ->
            val foto = r.fotoCaminho?.let { File(it) }
            if (foto != null && foto.exists()) {
                corpo.addFormDataPart("fotos", "${r.id}__${foto.name}", foto.asRequestBody("image/jpeg".toMediaType()))
            }
        }

        val requisicao = Request.Builder()
            .url("${prefs.urlServidor.trimEnd('/')}/api/v1/registros/sync")
            .post(corpo.build())
            .build()

        try {
            cliente.newCall(requisicao).execute().use { resposta ->
                when {
                    resposta.isSuccessful -> {
                        dao.marcarSincronizados(pendentes.map { it.id })
                        Result.success()
                    }
                    resposta.code in 400..499 -> Result.failure()  // pacote inválido: tentar de novo não ajuda
                    else -> Result.retry()
                }
            }
        } catch (e: IOException) {
            Result.retry()  // sem rede, servidor fora do ar, timeout...
        }
    }

    private fun montarPacote(registros: List<RegistroEntity>, prefs: Preferencias): JSONObject {
        val lista = JSONArray()
        registros.forEach { r ->
            lista.put(JSONObject().apply {
                put("id", r.id)
                put("nome_popular", r.nomePopular)
                put("parte_usada", r.parteUsada ?: JSONObject.NULL)
                put("modo_preparo", r.modoPreparo ?: JSONObject.NULL)
                put("indicacao", r.indicacao ?: JSONObject.NULL)
                put("sazonalidade", r.sazonalidade ?: JSONObject.NULL)
                put("comunidade", r.comunidade ?: JSONObject.NULL)
                put("consentimento_escopo", r.consentimento)
                put("consentimento_registrado_por", prefs.pesquisador)
                put("latitude", r.latitude)
                put("longitude", r.longitude)
                put("precisao_gps_m", r.precisaoGpsM?.toDouble() ?: JSONObject.NULL)
                put("coletado_em", r.coletadoEm)
                put("conversa", JSONArray(r.conversaJson))
                put("relato_original", relatoOriginal(r.conversaJson))
                put("qualidade_foto", r.qualidadeFotoJson?.let { JSONObject(it) } ?: JSONObject.NULL)
            })
        }
        return JSONObject()
            .put("dispositivo_id", prefs.dispositivoId)
            .put("expedicao", JSONObject().put("id", prefs.expedicaoId).put("nome", prefs.expedicaoNome))
            .put("registros", lista)
    }

    /** Junta as falas do pesquisador: é o relato "cru", antes da estruturação. */
    private fun relatoOriginal(conversaJson: String): String {
        val conversa = JSONArray(conversaJson)
        return (0 until conversa.length()).map { conversa.getJSONObject(it) }
            .filter { it.getString("autor") == "pesquisador" }
            .joinToString(" ") { it.getString("texto") }
    }

    companion object {
        private const val NOME = "sync-registros"

        private val cliente = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build()

        /** Agenda o envio. Se não houver internet agora, ele espera a conexão voltar. */
        fun agendar(context: Context) {
            val rede = if (Preferencias(context).soWifi) NetworkType.UNMETERED else NetworkType.CONNECTED
            val pedido = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(Constraints.Builder().setRequiredNetworkType(rede).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build()
            WorkManager.getInstance(context).enqueueUniqueWork(NOME, ExistingWorkPolicy.REPLACE, pedido)
        }
    }
}
