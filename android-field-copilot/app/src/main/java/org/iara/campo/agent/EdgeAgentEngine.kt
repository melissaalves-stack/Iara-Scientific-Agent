package org.iara.campo.agent

/**
 * Agente de campo que roda 100% no celular, sem internet.
 *
 * Ele conduz um diálogo curto para transformar um relato informal em um
 * registro estruturado. A técnica é "preenchimento de lacunas" (slot filling):
 * a cada mensagem, tenta extrair os campos que faltam e pergunta o próximo.
 *
 * Por padrão usa regras + dicionário (busca FTS no SQLite). Se um modelo de
 * linguagem local estiver disponível (ver [ModeloLocal]), ele é consultado
 * primeiro e as regras completam o que faltar.
 */
class EdgeAgentEngine(
    private val buscarPlanta: suspend (String) -> PlantaEncontrada?,
    private val modeloLocal: ModeloLocal? = null,
) {
    var rascunho = Rascunho()
        private set
    private var aguardando: Campo? = Campo.NOME

    fun saudacao(): String =
        "Olá! Sou o copiloto de campo e funciono sem internet. Conte o relato com suas palavras " +
            "(ex.: \"Dona Maria usa a casca da andiroba pra inflamação\"). ${Campo.NOME.pergunta}"

    fun reiniciar() {
        rascunho = Rascunho()
        aguardando = Campo.NOME
    }

    fun proximoCampo(): Campo? = Campo.entries.firstOrNull { rascunho.valor(it) == null }

    fun completo(): Boolean = proximoCampo() == null

    suspend fun processar(texto: String): String {
        val entendido = mutableListOf<String>()

        // 1) Modelo local opcional (nunca decide o consentimento: ele precisa ser explícito)
        modeloLocal?.extrairCampos(texto)?.forEach { (campo, valor) ->
            if (campo != Campo.CONSENTIMENTO && rascunho.valor(campo) == null && valor.isNotBlank()) {
                rascunho.preencher(campo, valor)
                entendido += "${campo.rotulo}: $valor"
            }
        }

        // 2) Extração precisa (dicionário e lista de partes): vale para qualquer mensagem
        if (rascunho.nomePopular == null) {
            buscarPlanta(texto)?.let { planta ->
                rascunho.nomePopular = planta.nomePopular
                rascunho.nomeCientificoProvavel = planta.nomeCientifico
                entendido += "planta: ${planta.nomePopular} (${planta.nomeCientifico}, ${planta.familia}). " +
                    "Usos já conhecidos no dicionário: ${planta.usosConhecidos}"
            }
        }
        if (rascunho.parteUsada == null) {
            Lexico.extrairParte(texto)?.let { rascunho.parteUsada = it; entendido += "parte usada: $it" }
        }

        // 3) Resposta à pergunta que o agente fez. Ela tem prioridade: se perguntamos
        //    o modo de preparo, a mensagem inteira é o modo de preparo.
        val campoPerguntado = aguardando
        var aviso: String? = null
        var respondeuPergunta = false
        if (campoPerguntado != null && rascunho.valor(campoPerguntado) == null) {
            when (campoPerguntado) {
                Campo.CONSENTIMENTO -> {
                    val escopo = Lexico.interpretarConsentimento(texto)
                    if (escopo != null) {
                        rascunho.consentimento = escopo
                        entendido += "consentimento: ${Campo.descreverConsentimento(escopo)}"
                    } else {
                        aviso = "Não entendi a autorização. Responda 1, 2 ou 3."
                    }
                }
                Campo.NOME -> {
                    // Resposta curta = provavelmente é só o nome. Frase longa = pedimos o nome de novo.
                    if (texto.trim().split(Regex("\\s+")).size <= 4) {
                        rascunho.nomePopular = texto.trim()
                        aviso = "Esse nome não está no dicionário local. Vou registrar assim mesmo; " +
                            "se possível, colete uma amostra (exsicata) para identificação."
                    } else {
                        aviso = "Não reconheci o nome da planta no dicionário local."
                    }
                }
                else -> {
                    rascunho.preencher(campoPerguntado, texto.trim())
                    entendido += campoPerguntado.rotulo
                    respondeuPergunta = true
                }
            }
        }

        // 4) Narrativa livre (ex.: primeira mensagem): tenta aproveitar indicação,
        //    preparo e época que vierem junto, para não perguntar de novo.
        if (!respondeuPergunta) {
            if (rascunho.indicacao == null) {
                val usos = Lexico.categoriasDeUso(texto)
                if (usos.isNotEmpty()) {
                    rascunho.indicacao = texto.trim()
                    entendido += "indicação (${usos.joinToString()})"
                }
            }
            if (rascunho.modoPreparo == null && Lexico.falaDePreparo(texto)) {
                rascunho.modoPreparo = texto.trim(); entendido += "modo de preparo"
            }
            if (rascunho.sazonalidade == null && Lexico.falaDeSazonalidade(texto)) {
                rascunho.sazonalidade = texto.trim(); entendido += "sazonalidade"
            }
        }

        // 5) Monta a resposta e a próxima pergunta
        val partes = mutableListOf<String>()
        if (entendido.isNotEmpty()) partes += "Anotei → ${entendido.joinToString("; ")}."
        aviso?.let { partes += it }
        val proximo = proximoCampo()
        aguardando = proximo
        partes += proximo?.pergunta
            ?: "Relato completo! Agora tire uma foto da planta 📷 e registre o GPS 📍. Depois toque em Salvar."
        return partes.joinToString("\n")
    }
}

/** O que o dicionário local devolve quando reconhece uma planta. */
data class PlantaEncontrada(
    val nomePopular: String,
    val nomeCientifico: String,
    val familia: String,
    val usosConhecidos: String,
)

/**
 * Ponto de extensão para um LLM que roda no próprio celular
 * (ex.: MediaPipe LLM Inference ou ONNX Runtime com um modelo pequeno).
 * Não vem implementado no MVP: as regras já funcionam sem ele.
 */
interface ModeloLocal {
    suspend fun extrairCampos(texto: String): Map<Campo, String>
}

enum class Campo(val rotulo: String, val pergunta: String) {
    NOME("nome", "Qual é o nome da planta que a comunidade usa?"),
    PARTE("parte usada", "Qual parte da planta é usada? (folha, casca, raiz, semente, fruto, óleo, resina…)"),
    INDICACAO("indicação", "Para que ela é usada? Qual a indicação?"),
    PREPARO("modo de preparo", "Como é o modo de preparo?"),
    SAZONALIDADE("sazonalidade", "Em que época do ano é coletada?"),
    COMUNIDADE("comunidade", "Qual o nome da comunidade? (pode ser um código, se preferirem não se identificar)"),
    CONSENTIMENTO(
        "consentimento",
        "Sobre o consentimento, a comunidade autoriza:\n1) só uso interno da pesquisa\n" +
            "2) publicar a ocorrência da planta, sem o saber tradicional\n3) publicação completa",
    );

    companion object {
        fun descreverConsentimento(escopo: String) = when (escopo) {
            "uso_interno" -> "só uso interno"
            "publicacao_sem_conhecimento" -> "publicar sem o saber tradicional"
            "publicacao_completa" -> "publicação completa"
            else -> escopo
        }
    }
}

data class Rascunho(
    var nomePopular: String? = null,
    var nomeCientificoProvavel: String? = null,
    var parteUsada: String? = null,
    var indicacao: String? = null,
    var modoPreparo: String? = null,
    var sazonalidade: String? = null,
    var comunidade: String? = null,
    var consentimento: String? = null,
) {
    fun valor(campo: Campo): String? = when (campo) {
        Campo.NOME -> nomePopular
        Campo.PARTE -> parteUsada
        Campo.INDICACAO -> indicacao
        Campo.PREPARO -> modoPreparo
        Campo.SAZONALIDADE -> sazonalidade
        Campo.COMUNIDADE -> comunidade
        Campo.CONSENTIMENTO -> consentimento
    }

    fun preencher(campo: Campo, valor: String) {
        when (campo) {
            Campo.NOME -> nomePopular = valor
            Campo.PARTE -> parteUsada = valor
            Campo.INDICACAO -> indicacao = valor
            Campo.PREPARO -> modoPreparo = valor
            Campo.SAZONALIDADE -> sazonalidade = valor
            Campo.COMUNIDADE -> comunidade = valor
            Campo.CONSENTIMENTO -> consentimento = valor
        }
    }
}
