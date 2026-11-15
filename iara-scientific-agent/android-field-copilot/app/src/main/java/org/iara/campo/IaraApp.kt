package org.iara.campo

import android.app.Application
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.iara.campo.data.AppDatabase
import org.iara.campo.data.Dicionario
import org.iara.campo.sync.SyncWorker

class IaraApp : Application() {
    val escopo = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    val banco by lazy { AppDatabase.get(this) }
    val dicionario by lazy { Dicionario(this, banco.dicionario()) }

    override fun onCreate() {
        super.onCreate()
        // Na primeira abertura, carrega o dicionário etnobotânico no SQLite
        escopo.launch { dicionario.popularSeVazio() }
        // Se ficou algo na fila de uma sessão anterior, tenta enviar
        SyncWorker.agendar(this)
    }
}
