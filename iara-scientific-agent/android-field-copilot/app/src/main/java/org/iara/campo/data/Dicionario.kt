package org.iara.campo.data

import android.content.Context
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.iara.campo.agent.Lexico
import org.json.JSONArray

/**
 * Carrega o dicionário embarcado (assets/dicionario_etnobotanico.json) no banco
 * na primeira execução e oferece a busca offline por nome de planta.
 */
class Dicionario(private val context: Context, private val dao: DicionarioDao) {
    private val trava = Mutex()  // evita carregar duas vezes se chamado ao mesmo tempo

    suspend fun popularSeVazio() = trava.withLock {
        if (dao.total() > 0) return@withLock
        val json = context.assets.open("dicionario_etnobotanico.json").bufferedReader().use { it.readText() }
        val array = JSONArray(json)
        val itens = (0 until array.length()).map { i ->
            val o = array.getJSONObject(i)
            val populares = o.getJSONArray("nomes_populares").let { a -> (0 until a.length()).map { a.getString(it) } }
            val sinonimos = o.getJSONArray("sinonimos").let { a -> (0 until a.length()).map { a.getString(it) } }
            val todos = populares + sinonimos + o.getString("nome_cientifico")
            DicionarioEntity(
                termos = todos.joinToString("|") { Lexico.normalizar(it) },
                nomePopular = populares.first(),
                nomeCientifico = o.getString("nome_cientifico"),
                familia = o.getString("familia"),
                usosConhecidos = o.getString("usos_conhecidos"),
            )
        }
        dao.inserir(itens)
    }

    /**
     * Procura no texto livre algum nome de planta conhecido.
     * Usa o índice FTS para achar candidatos por prefixo de palavra e depois
     * confere se o nome completo aparece no texto.
     */
    suspend fun encontrarPlanta(texto: String): DicionarioEntity? {
        val normalizado = Lexico.normalizar(texto).replace('-', ' ')
        val palavras = normalizado.split(" ").filter { it.length >= 4 && it !in Lexico.PALAVRAS_VAZIAS }
        val candidatos = palavras.flatMap { dao.buscar("$it*") }.distinct()
        return candidatos.firstOrNull { item ->
            item.termos.split("|").any { nome -> " $normalizado ".contains(" ${nome.replace('-', ' ')} ") }
        }
    }
}
