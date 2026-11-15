package org.iara.campo.agent

import java.text.Normalizer

/**
 * Vocabulário em português usado pelas regras do agente.
 * É o mesmo vocabulário do backend (backend-agents/app/services/texto.py),
 * para que celular e servidor "entendam" o relato do mesmo jeito.
 */
object Lexico {

    fun normalizar(texto: String): String {
        val semAcento = Normalizer.normalize(texto, Normalizer.Form.NFD).replace(Regex("\\p{Mn}+"), "")
        return semAcento.lowercase()
            .replace(Regex("[^a-z0-9\\s-]"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
    }

    val PALAVRAS_VAZIAS = setOf(
        "para", "pra", "como", "essa", "esse", "isso", "aqui", "ela", "ele", "eles", "elas", "uma", "umas",
        "que", "com", "sem", "planta", "folha", "casca", "raiz", "semente", "fruto", "oleo", "usa", "usam",
        "falou", "disse", "sobre", "depois", "quando", "muito", "pouco", "tira", "tirar",
    )

    private val PARTES = linkedMapOf(
        "casca" to listOf("casca"),
        "folha" to listOf("folha", "folhas"),
        "raiz" to listOf("raiz", "raizes"),
        "semente" to listOf("semente", "sementes", "caroco"),
        "fruto" to listOf("fruto", "frutos", "fruta"),
        "oleo" to listOf("oleo", "azeite"),
        "resina" to listOf("resina", "breu", "seiva", "leite"),
        "flor" to listOf("flor", "flores"),
        "caule" to listOf("caule", "tronco", "cipo"),
    )

    private val CATEGORIAS_USO = mapOf(
        "anti-inflamatório" to listOf("inflamacao", "inflamado", "inchaco", "inchado", "desinflamar", "desinflama"),
        "cicatrizante" to listOf("ferida", "machucado", "corte", "cicatrizar"),
        "analgésico" to listOf("dor ", "dores", "doendo"),
        "repelente" to listOf("mosquito", "carapana", "inseto", "repelente", "pium", "mucuim"),
        "febre" to listOf("febre", "maleita", "malaria"),
        "respiratório" to listOf("gripe", "tosse", "resfriado", "catarro", "garganta"),
        "digestivo" to listOf("barriga", "estomago", "diarreia", "intestino", "verme"),
        "fígado" to listOf("figado", "hepatite", "ictericia"),
        "rins" to listOf("rim", "rins", "pedra nos rins", "urina"),
        "anemia" to listOf("anemia", "sangue fraco"),
        "pele" to listOf("coceira", "micose", "pele", "frieira"),
        "alimentar" to listOf("comida", "alimento", "vinho", "suco", "come "),
    )

    private val PREPARO = listOf(
        "ferve", "ferver", "cozinha", "cozinhar", "cha ", "macera", "rala", "espreme", "garrafada", "banho",
        "infusao", "emplastro", "mistura", "soca", "pila", "torra", "queima", "molho", "bate", "amassa",
    )

    private val SAZONALIDADE = listOf(
        "janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
        "novembro", "dezembro", "ano todo", "ano inteiro", "safra", "chuva", "chuvoso", "inverno", "verao",
        "seca", "cheia", "vazante", "epoca", "lua",
    )

    private fun contem(texto: String, termos: List<String>): Boolean {
        val t = " ${normalizar(texto)} "
        return termos.any { t.contains(it) }
    }

    fun extrairParte(texto: String): String? {
        val palavras = " ${normalizar(texto)} "
        return PARTES.entries.firstOrNull { (_, termos) -> termos.any { palavras.contains(" $it ") } }?.key
    }

    fun categoriasDeUso(texto: String): List<String> {
        val t = " ${normalizar(texto)} "
        return CATEGORIAS_USO.filter { (_, termos) -> termos.any { t.contains(it) } }.keys.toList()
    }

    fun falaDePreparo(texto: String) = contem(texto, PREPARO)

    fun falaDeSazonalidade(texto: String) = contem(texto, SAZONALIDADE)

    /** Interpreta a resposta sobre consentimento. Retorna null se não ficou claro. */
    fun interpretarConsentimento(texto: String): String? {
        val t = " ${normalizar(texto)} "
        return when {
            t.contains(" 2 ") || listOf("sem o saber", "sem o uso", "so a planta", "ocorre", "uso fica", "sem o conhecimento")
                .any { t.contains(it) } -> "publicacao_sem_conhecimento"
            t.contains(" 1 ") || listOf("interno", "interna", "so pesquisa", "so pra pesquisa", "nao autoriza", " nao ")
                .any { t.contains(it) } -> "uso_interno"
            t.contains(" 3 ") || listOf("completa", "tudo", "pode publicar", "autoriza", "sim")
                .any { t.contains(it) } -> "publicacao_completa"
            else -> null
        }
    }
}
