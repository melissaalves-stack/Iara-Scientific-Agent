package org.iara.campo

import android.content.Context
import java.util.UUID

/**
 * Configurações simples guardadas no celular (SharedPreferences).
 *
 * Endereço do servidor:
 *  - emulador do Android Studio: http://10.0.2.2:8000 (é o "localhost" do computador)
 *  - celular real na mesma rede Wi-Fi: http://IP-DO-COMPUTADOR:8000
 */
class Preferencias(context: Context) {
    private val prefs = context.getSharedPreferences("iara", Context.MODE_PRIVATE)

    var urlServidor: String
        get() = prefs.getString("url_servidor", "http://10.0.2.2:8000")!!
        set(valor) = prefs.edit().putString("url_servidor", valor.trim()).apply()

    var pesquisador: String
        get() = prefs.getString("pesquisador", "Pesquisador(a) de campo")!!
        set(valor) = prefs.edit().putString("pesquisador", valor.trim()).apply()

    var expedicaoNome: String
        get() = prefs.getString("expedicao_nome", "Expedição de campo")!!
        set(valor) = prefs.edit().putString("expedicao_nome", valor.trim()).apply()

    /** Se verdadeiro, a sincronização espera uma rede sem cobrança por dados (Wi-Fi). */
    var soWifi: Boolean
        get() = prefs.getBoolean("so_wifi", false)
        set(valor) = prefs.edit().putBoolean("so_wifi", valor).apply()

    /** O id da expedição é derivado do nome, para agrupar os registros no servidor. */
    val expedicaoId: String
        get() = "exp-" + expedicaoNome.lowercase().replace(Regex("[^a-z0-9]+"), "-").trim('-')

    val dispositivoId: String
        get() = prefs.getString("dispositivo_id", null)
            ?: UUID.randomUUID().toString().also { prefs.edit().putString("dispositivo_id", it).apply() }
}
