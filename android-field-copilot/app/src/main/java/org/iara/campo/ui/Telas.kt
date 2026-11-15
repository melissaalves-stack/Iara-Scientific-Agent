package org.iara.campo.ui

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.speech.RecognizerIntent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.outlined.Book
import androidx.compose.material.icons.outlined.CloudDone
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.Eco
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.PhotoCamera
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.iara.campo.Preferencias
import org.iara.campo.R
import org.iara.campo.agent.Campo
import org.iara.campo.data.RegistroEntity

// ---------------- Peças comuns ----------------

/** Cabeçalho verde com a folha-gota ao fundo, como nos mockups da identidade visual. */
@Composable
fun Cabecalho(titulo: String, subtitulo: String? = null, acessorio: @Composable () -> Unit = {}) {
    Box(
        Modifier
            .fillMaxWidth()
            .background(Cores.VerdeCopaiba)
            .clip(RoundedCornerShape(0.dp)),
    ) {
        Image(
            painter = painterResource(R.drawable.gota_negativa),
            contentDescription = null,
            modifier = Modifier.align(Alignment.TopEnd).offset(x = 18.dp, y = (-22).dp).size(96.dp, 128.dp).alpha(0.16f),
        )
        Row(
            Modifier.fillMaxWidth().padding(start = 18.dp, end = 14.dp, top = 16.dp, bottom = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(titulo, style = MaterialTheme.typography.headlineLarge, color = Cores.Papel)
                subtitulo?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = Cores.Palha) }
            }
            acessorio()
        }
    }
}

@Composable
private fun Etiqueta(texto: String, icone: ImageVector, cor: Color, fundo: Color, borda: Boolean = false) {
    Row(
        Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(fundo)
            .then(if (borda) Modifier.border(1.dp, cor, RoundedCornerShape(6.dp)) else Modifier)
            .padding(horizontal = 8.dp, vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Icon(icone, contentDescription = null, tint = cor, modifier = Modifier.size(15.dp))
        Text(texto, style = MaterialTheme.typography.labelMedium, color = cor)
    }
}

@Composable
private fun IconeEspecie() {
    Box(
        Modifier.size(48.dp).clip(RoundedCornerShape(24.dp, 24.dp, 24.dp, 8.dp)).background(Cores.VerdeClaro),
        contentAlignment = Alignment.Center,
    ) { Icon(Icons.Outlined.Eco, contentDescription = null, tint = Cores.VerdeCopaiba) }
}

// ---------------- Tela 1: Campo ----------------

@Composable
fun TelaCampo(vm: CampoViewModel) {
    val estado by vm.estado.collectAsStateWithLifecycle()
    val online by vm.online.collectAsStateWithLifecycle()
    val prefs = Preferencias(LocalContext.current)
    var texto by remember { mutableStateOf("") }
    val lista = rememberLazyListState()

    // Voz: abre o reconhecimento de fala do Android, preferindo o modo offline
    val voz = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { resultado ->
        resultado.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()?.let(vm::enviar)
    }
    val camera = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { ok -> vm.fotoTirada(ok) }
    val permissaoGps = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { r ->
        if (r.values.any { it }) vm.capturarGps()
    }

    LaunchedEffect(estado.mensagens.size) {
        lista.animateScrollToItem(estado.mensagens.size)  // último item = ficha em construção
    }

    Column(Modifier.fillMaxSize().background(Cores.Palha)) {
        Cabecalho("Campo", "${prefs.expedicaoNome} · registro ${estado.numeroRegistro}") {
            Etiqueta(
                texto = if (online) "Online" else "Offline",
                icone = if (online) Icons.Outlined.CloudDone else Icons.Outlined.CloudOff,
                cor = Cores.Jenipapo,
                fundo = Cores.Papel,
            )
        }

        // Faixa do GPS
        Row(
            Modifier.fillMaxWidth().background(Cores.Papel).padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Outlined.Place, contentDescription = null, tint = Cores.Texto2, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(6.dp))
            val p = estado.posicao
            Text(
                when {
                    p != null -> "%.3f  %.3f   ±%.0f m".format(p.latitude, p.longitude, p.precisaoM)
                    estado.buscandoGps -> "Buscando satélites…"
                    else -> "Sem posição ainda"
                },
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.weight(1f),
            )
            if (p != null) {
                val bom = p.precisaoM <= 30
                Icon(
                    if (bom) Icons.Filled.Check else Icons.Outlined.ErrorOutline,
                    contentDescription = null,
                    tint = if (bom) Cores.VerdeCopaiba else Cores.Urucum,
                    modifier = Modifier.size(16.dp),
                )
                Text(
                    if (bom) " GPS bom" else " GPS fraco",
                    style = MaterialTheme.typography.labelMedium,
                    color = if (bom) Cores.VerdeCopaiba else Cores.Urucum,
                )
            }
        }

        LazyColumn(
            state = lista,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            item { Spacer(Modifier.height(4.dp)) }
            items(estado.mensagens) { m -> Balao(m) }
            item { FichaEmConstrucao(estado) }
            item { Spacer(Modifier.height(4.dp)) }
        }

        estado.aviso?.let {
            Text(
                "⚠ $it",
                style = MaterialTheme.typography.bodySmall,
                color = Cores.Urucum,
                modifier = Modifier.fillMaxWidth().background(Cores.UrucumClaro).padding(horizontal = 16.dp, vertical = 6.dp),
            )
        }

        // Área de entrada
        Column(Modifier.fillMaxWidth().background(Cores.Papel).padding(12.dp)) {
            Text("Relato", style = MaterialTheme.typography.labelMedium, color = Cores.Jenipapo)
            Spacer(Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(
                    value = texto,
                    onValueChange = { texto = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("Escreva ou fale…") },
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        unfocusedBorderColor = Cores.Jenipapo,
                        focusedBorderColor = Cores.VerdeCopaiba,
                        unfocusedContainerColor = Color.White,
                        focusedContainerColor = Color.White,
                    ),
                )
                Spacer(Modifier.width(8.dp))
                if (texto.isBlank()) {
                    IconButton(
                        onClick = {
                            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                                .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR")
                                .putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
                            try { voz.launch(intent) } catch (_: ActivityNotFoundException) { }
                        },
                        modifier = Modifier.size(54.dp),
                        colors = IconButtonDefaults.iconButtonColors(containerColor = Cores.RioNegro, contentColor = Cores.Papel),
                    ) { Icon(Icons.Filled.Mic, contentDescription = "Falar o relato") }
                } else {
                    IconButton(
                        onClick = { vm.enviar(texto); texto = "" },
                        modifier = Modifier.size(54.dp),
                        colors = IconButtonDefaults.iconButtonColors(containerColor = Cores.VerdeCopaiba, contentColor = Cores.Papel),
                    ) { Icon(Icons.Filled.ArrowUpward, contentDescription = "Enviar") }
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                BotaoAcao("Foto", Icons.Outlined.PhotoCamera, Modifier.weight(1f)) { camera.launch(vm.prepararFoto()) }
                BotaoAcao("GPS", Icons.Outlined.Place, Modifier.weight(1f)) {
                    permissaoGps.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
                }
                Button(
                    onClick = vm::salvar,
                    enabled = estado.relatoCompleto && estado.posicao != null,
                    modifier = Modifier.weight(1f).height(60.dp),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Image(painterResource(R.drawable.gota_negativa), contentDescription = null, modifier = Modifier.size(14.dp, 19.dp))
                        Text("Salvar", style = MaterialTheme.typography.labelLarge)
                    }
                }
            }
        }
    }
}

@Composable
private fun BotaoAcao(rotulo: String, icone: ImageVector, modifier: Modifier, onClick: () -> Unit) {
    OutlinedButton(
        onClick = onClick,
        modifier = modifier.height(60.dp),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.5.dp, Cores.Jenipapo),
        colors = ButtonDefaults.outlinedButtonColors(containerColor = Color.White, contentColor = Cores.Jenipapo),
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(icone, contentDescription = null, modifier = Modifier.size(20.dp))
            Text(rotulo, style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun Balao(m: Mensagem) {
    val doPesquisador = m.autor == "pesquisador"
    Row(Modifier.fillMaxWidth(), horizontalArrangement = if (doPesquisador) Arrangement.End else Arrangement.Start) {
        Text(
            m.texto,
            style = MaterialTheme.typography.bodyMedium,
            color = if (doPesquisador) Cores.Papel else Cores.Jenipapo,
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(
                    RoundedCornerShape(
                        topStart = 14.dp, topEnd = 14.dp,
                        bottomStart = if (doPesquisador) 14.dp else 4.dp,
                        bottomEnd = if (doPesquisador) 4.dp else 14.dp,
                    ),
                )
                .background(if (doPesquisador) Cores.VerdeCopaiba else Color.White)
                .padding(horizontal = 12.dp, vertical = 9.dp),
        )
    }
}

/** Mostra quais campos do relato o agente já preencheu e o que falta. */
@Composable
private fun FichaEmConstrucao(estado: EstadoCampo) {
    val itens = listOf(
        "Planta" to (estado.ficha[Campo.NOME] == true),
        "Parte" to (estado.ficha[Campo.PARTE] == true),
        "Indicação" to (estado.ficha[Campo.INDICACAO] == true),
        "Preparo" to (estado.ficha[Campo.PREPARO] == true),
        "Época" to (estado.ficha[Campo.SAZONALIDADE] == true),
        "Comunidade" to (estado.ficha[Campo.COMUNIDADE] == true),
        "Consentimento" to (estado.ficha[Campo.CONSENTIMENTO] == true),
        "Foto" to (estado.qualidade?.aprovada == true),
        "GPS" to (estado.posicao != null),
    )
    Card(
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.5.dp, Cores.Jenipapo),
        colors = CardDefaults.cardColors(containerColor = Cores.Papel),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(14.dp)) {
            Text("Ficha em construção", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(8.dp))
            itens.chunked(2).forEach { linha ->
                Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
                    linha.forEach { (rotulo, ok) ->
                        Row(Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                if (ok) Icons.Filled.Check else Icons.Outlined.ErrorOutline,
                                contentDescription = if (ok) "preenchido" else "falta",
                                tint = if (ok) Cores.VerdeCopaiba else Cores.Urucum,
                                modifier = Modifier.size(16.dp),
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(
                                rotulo,
                                style = MaterialTheme.typography.bodySmall,
                                fontWeight = if (ok) FontWeight.Normal else FontWeight.SemiBold,
                                color = if (ok) Cores.Jenipapo else Cores.Urucum,
                            )
                        }
                    }
                    if (linha.size == 1) Spacer(Modifier.weight(1f))
                }
            }
        }
    }
}

// ---------------- Tela 2: Registros e fila de sincronização ----------------

@Composable
fun TelaRegistros(vm: CampoViewModel) {
    val registros by vm.registros.collectAsStateWithLifecycle()
    var busca by remember { mutableStateOf("") }
    val pendentes = registros.count { !it.sincronizado }
    val filtrados = registros.filter { r ->
        busca.isBlank() || listOfNotNull(r.nomePopular, r.comunidade, r.indicacao).any { it.contains(busca, ignoreCase = true) }
    }

    Column(Modifier.fillMaxSize().background(Cores.Palha)) {
        Box(Modifier.background(Cores.VerdeCopaiba)) {
            Column {
                Cabecalho("Registros")
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Cores.Papel),
                    modifier = Modifier.fillMaxWidth().padding(start = 14.dp, end = 14.dp, bottom = 14.dp),
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            if (pendentes > 0) Icons.Outlined.Schedule else Icons.Outlined.CloudDone,
                            contentDescription = null,
                            tint = if (pendentes > 0) Cores.Urucum else Cores.VerdeCopaiba,
                        )
                        Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f)) {
                            Text(
                                if (pendentes > 0) "$pendentes aguardando conexão" else "Tudo sincronizado",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            Text("Envio automático quando houver rede", style = MaterialTheme.typography.bodySmall, color = Cores.Texto2)
                        }
                        if (pendentes > 0) {
                            Button(onClick = vm::sincronizarAgora, shape = RoundedCornerShape(10.dp)) { Text("Enviar já") }
                        }
                    }
                }
            }
        }

        OutlinedTextField(
            value = busca,
            onValueChange = { busca = it },
            label = { Text("Buscar") },
            placeholder = { Text("Planta, comunidade ou uso") },
            leadingIcon = { Icon(Icons.Outlined.Search, contentDescription = null) },
            singleLine = true,
            shape = RoundedCornerShape(10.dp),
            colors = OutlinedTextFieldDefaults.colors(
                unfocusedBorderColor = Cores.Jenipapo,
                unfocusedContainerColor = Color.White,
                focusedContainerColor = Color.White,
            ),
            modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp),
        )

        if (filtrados.isEmpty()) {
            Text(
                if (registros.isEmpty()) "Nenhum registro ainda. Os relatos salvos na aba Campo aparecem aqui."
                else "Nada encontrado para \"$busca\".",
                style = MaterialTheme.typography.bodyMedium,
                color = Cores.Texto2,
                modifier = Modifier.padding(20.dp),
            )
        }
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.padding(horizontal = 14.dp),
        ) {
            items(filtrados, key = { it.id }) { r -> CartaoRegistro(r) }
            item { Spacer(Modifier.height(12.dp)) }
        }
    }
}

@Composable
private fun CartaoRegistro(r: RegistroEntity) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Cores.Borda),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(Modifier.padding(12.dp)) {
            IconeEspecie()
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(r.nomePopular, style = MaterialTheme.typography.titleLarge)
                Text(
                    listOfNotNull(r.comunidade, r.coletadoEm.take(10).split("-").reversed().joinToString("/")).joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = Cores.Texto2,
                )
                Spacer(Modifier.height(6.dp))
                if (r.sincronizado) {
                    Etiqueta("Sincronizado", Icons.Outlined.CloudDone, Cores.VerdeCopaiba, Cores.VerdeClaro, borda = true)
                } else {
                    Etiqueta("Na fila", Icons.Outlined.Schedule, Cores.Urucum, Cores.UrucumClaro, borda = true)
                }
            }
        }
    }
}

// ---------------- Tela 3: Ajustes ----------------

@Composable
fun TelaAjustes(vm: CampoViewModel) {
    val prefs = Preferencias(LocalContext.current)
    val totalDicionario by vm.totalDicionario.collectAsStateWithLifecycle()
    var url by remember { mutableStateOf(prefs.urlServidor) }
    var pesquisador by remember { mutableStateOf(prefs.pesquisador) }
    var expedicao by remember { mutableStateOf(prefs.expedicaoNome) }
    var soWifi by remember { mutableStateOf(prefs.soWifi) }
    var salvo by remember { mutableStateOf(false) }
    val iniciais = pesquisador.split(" ").filter { it.isNotBlank() }.take(2).joinToString("") { it.take(1).uppercase() }

    Column(Modifier.fillMaxSize().background(Cores.Palha)) {
        Cabecalho("Ajustes", pesquisador) {
            Box(
                Modifier.size(46.dp).clip(CircleShape).background(Cores.Palha),
                contentAlignment = Alignment.Center,
            ) { Text(iniciais.ifBlank { "?" }, style = MaterialTheme.typography.titleMedium, color = Cores.VerdeCopaiba) }
        }

        LazyColumn(Modifier.padding(horizontal = 14.dp)) {
            item {
                Secao("Equipe e expedição")
                Painel {
                    CampoTexto("Pesquisador(a)", pesquisador) { pesquisador = it; salvo = false }
                    CampoTexto("Expedição", expedicao) { expedicao = it; salvo = false }
                }

                Secao("Sincronização")
                Painel {
                    CampoTexto("Endereço do servidor", url) { url = it; salvo = false }
                    Text(
                        "Emulador: http://10.0.2.2:8000 · Celular na mesma rede Wi-Fi: http://IP-DO-COMPUTADOR:8000",
                        style = MaterialTheme.typography.bodySmall,
                        color = Cores.Texto2,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 4.dp),
                    )
                    HorizontalDivider(color = Cores.Borda)
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Wifi, contentDescription = null, tint = Cores.Jenipapo)
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text("Enviar só no Wi-Fi", style = MaterialTheme.typography.titleMedium)
                            Text("Economiza dados móveis", style = MaterialTheme.typography.bodySmall, color = Cores.Texto2)
                        }
                        Switch(checked = soWifi, onCheckedChange = { soWifi = it; salvo = false })
                    }
                }

                Secao("Consentimento")
                Painel {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Check, contentDescription = null, tint = Cores.VerdeCopaiba)
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text("Perguntado em todo registro", style = MaterialTheme.typography.titleMedium)
                            Text(
                                "Obrigatório: o agente só fecha o relato depois que a comunidade escolhe o escopo.",
                                style = MaterialTheme.typography.bodySmall,
                                color = Cores.Texto2,
                            )
                        }
                    }
                }

                Secao("Offline")
                Painel {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Outlined.Book, contentDescription = null, tint = Cores.Jenipapo)
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text("Dicionário etnobotânico", style = MaterialTheme.typography.titleMedium)
                            Text("Instalado no aparelho · $totalDicionario espécies", style = MaterialTheme.typography.bodySmall, color = Cores.Texto2)
                        }
                        Etiqueta(
                            if (totalDicionario > 0) "Pronto" else "Carregando",
                            if (totalDicionario > 0) Icons.Filled.Check else Icons.Outlined.Schedule,
                            Cores.VerdeCopaiba, Cores.VerdeClaro,
                        )
                    }
                }

                Button(
                    onClick = {
                        prefs.urlServidor = url
                        prefs.pesquisador = pesquisador
                        prefs.expedicaoNome = expedicao
                        prefs.soWifi = soWifi
                        salvo = true
                    },
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth().padding(vertical = 18.dp).height(52.dp),
                ) { Text(if (salvo) "✓ Ajustes salvos" else "Salvar ajustes", style = MaterialTheme.typography.labelLarge) }
            }
        }
    }
}

@Composable
private fun Secao(titulo: String) {
    Text(titulo, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.padding(top = 18.dp, bottom = 8.dp))
}

@Composable
private fun Painel(conteudo: @Composable () -> Unit) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Cores.Borda),
        modifier = Modifier.fillMaxWidth(),
    ) { Column { conteudo() } }
}

@Composable
private fun CampoTexto(rotulo: String, valor: String, onChange: (String) -> Unit) {
    OutlinedTextField(
        value = valor,
        onValueChange = onChange,
        label = { Text(rotulo) },
        singleLine = true,
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 8.dp),
    )
}
