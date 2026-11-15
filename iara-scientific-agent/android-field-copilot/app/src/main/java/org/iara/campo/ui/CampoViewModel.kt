package org.iara.campo.ui

import android.app.Application
import android.net.ConnectivityManager
import android.net.Network
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.iara.campo.IaraApp
import org.iara.campo.agent.Campo
import org.iara.campo.agent.EdgeAgentEngine
import org.iara.campo.agent.PlantaEncontrada
import org.iara.campo.data.RegistroEntity
import org.iara.campo.media.Localizacao
import org.iara.campo.media.Posicao
import org.iara.campo.media.QualidadeFoto
import org.iara.campo.media.ResultadoQualidade
import org.iara.campo.sync.SyncWorker
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.OffsetDateTime
import java.util.UUID

data class Mensagem(val autor: String, val texto: String)  // autor: "pesquisador" ou "agente"

data class EstadoCampo(
    val mensagens: List<Mensagem> = emptyList(),
    val fotoCaminho: String? = null,
    val qualidade: ResultadoQualidade? = null,
    val posicao: Posicao? = null,
    val buscandoGps: Boolean = false,
    val relatoCompleto: Boolean = false,
    val aviso: String? = null,
    /** Quais campos do relato já foram preenchidos (para a "ficha em construção"). */
    val ficha: Map<Campo, Boolean> = Campo.entries.associateWith { false },
    val numeroRegistro: Int = 1,
)

class CampoViewModel(app: Application) : AndroidViewModel(app) {
    private val iara = app as IaraApp
    private val dao = iara.banco.registros()

    private val agente = EdgeAgentEngine(buscarPlanta = { texto ->
        iara.dicionario.encontrarPlanta(texto)?.let {
            PlantaEncontrada(it.nomePopular, it.nomeCientifico, it.familia, it.usosConhecidos)
        }
    })

    private val _estado = MutableStateFlow(EstadoCampo(mensagens = listOf(Mensagem("agente", agente.saudacao()))))
    val estado: StateFlow<EstadoCampo> = _estado.asStateFlow()

    val registros: StateFlow<List<RegistroEntity>> =
        dao.observarTodos().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private var fotoPendente: File? = null

    /** Há rede agora? Mostrado no chip "Offline/Online" do cabeçalho. */
    private val _online = MutableStateFlow(false)
    val online: StateFlow<Boolean> = _online.asStateFlow()

    private val _totalDicionario = MutableStateFlow(0)
    val totalDicionario: StateFlow<Int> = _totalDicionario.asStateFlow()

    private val conectividade = app.getSystemService(ConnectivityManager::class.java)
    private val ouvinteRede = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) { _online.value = true }
        override fun onLost(network: Network) { _online.value = false }
    }

    init {
        conectividade.registerDefaultNetworkCallback(ouvinteRede)
        viewModelScope.launch {
            iara.dicionario.popularSeVazio()
            _totalDicionario.value = iara.banco.dicionario().total()
        }
    }

    override fun onCleared() {
        conectividade.unregisterNetworkCallback(ouvinteRede)
    }

    private fun fichaAtual() = Campo.entries.associateWith { agente.rascunho.valor(it) != null }

    fun enviar(texto: String) {
        if (texto.isBlank()) return
        _estado.update { it.copy(mensagens = it.mensagens + Mensagem("pesquisador", texto.trim()), aviso = null) }
        viewModelScope.launch {
            val resposta = agente.processar(texto)
            _estado.update {
                it.copy(
                    mensagens = it.mensagens + Mensagem("agente", resposta),
                    relatoCompleto = agente.completo(),
                    ficha = fichaAtual(),
                )
            }
        }
    }

    /** Cria o arquivo onde a câmera vai salvar a foto e devolve o endereço dele. */
    fun prepararFoto(): Uri {
        val pasta = File(getApplication<Application>().filesDir, "fotos").apply { mkdirs() }
        val arquivo = File(pasta, "${UUID.randomUUID()}.jpg")
        fotoPendente = arquivo
        return FileProvider.getUriForFile(getApplication(), "${getApplication<Application>().packageName}.fileprovider", arquivo)
    }

    fun fotoTirada(sucesso: Boolean) {
        val arquivo = fotoPendente ?: return
        if (!sucesso) return
        viewModelScope.launch {
            val qualidade = withContext(Dispatchers.Default) {
                QualidadeFoto.avaliar(getApplication(), Uri.fromFile(arquivo))
            }
            val texto = when {
                qualidade == null -> "Não consegui analisar a foto."
                qualidade.aprovada -> "Foto aprovada ✅ (nitidez ${qualidade.nitidez.toInt()}, brilho ${qualidade.brilho.toInt()})."
                else -> "⚠️ ${qualidade.motivo} (nitidez ${qualidade.nitidez.toInt()}, brilho ${qualidade.brilho.toInt()})"
            }
            _estado.update {
                it.copy(fotoCaminho = arquivo.absolutePath, qualidade = qualidade,
                    mensagens = it.mensagens + Mensagem("agente", texto))
            }
        }
    }

    fun capturarGps() {
        _estado.update { it.copy(buscandoGps = true) }
        viewModelScope.launch {
            val posicao = runCatching { Localizacao.atual(getApplication()) }.getOrNull()
            _estado.update {
                it.copy(
                    buscandoGps = false,
                    posicao = posicao ?: it.posicao,
                    aviso = if (posicao == null) "Não consegui obter o GPS. Vá para um lugar aberto e tente de novo." else null,
                )
            }
        }
    }

    fun salvar() {
        val e = _estado.value
        val posicao = e.posicao ?: return
        val r = agente.rascunho
        if (!agente.completo()) return
        val conversa = JSONArray().apply {
            e.mensagens.forEach { put(JSONObject().put("autor", it.autor).put("texto", it.texto)) }
        }
        val registro = RegistroEntity(
            id = UUID.randomUUID().toString(),
            nomePopular = r.nomePopular!!,
            parteUsada = r.parteUsada,
            modoPreparo = r.modoPreparo,
            indicacao = r.indicacao,
            sazonalidade = r.sazonalidade,
            comunidade = r.comunidade,
            consentimento = r.consentimento!!,
            latitude = posicao.latitude,
            longitude = posicao.longitude,
            precisaoGpsM = posicao.precisaoM,
            coletadoEm = OffsetDateTime.now().toString(),
            fotoCaminho = e.fotoCaminho,
            qualidadeFotoJson = e.qualidade?.toJson(),
            conversaJson = conversa.toString(),
        )
        viewModelScope.launch {
            dao.salvar(registro)
            SyncWorker.agendar(getApplication())
            agente.reiniciar()
            fotoPendente = null
            _estado.value = EstadoCampo(
                numeroRegistro = _estado.value.numeroRegistro + 1,
                mensagens = listOf(
                    Mensagem("agente", "Registro de ${registro.nomePopular} salvo no celular ✅. " +
                        "Ele será enviado quando houver internet."),
                    Mensagem("agente", agente.saudacao()),
                ),
            )
        }
    }

    fun sincronizarAgora() = SyncWorker.agendar(getApplication())
}
