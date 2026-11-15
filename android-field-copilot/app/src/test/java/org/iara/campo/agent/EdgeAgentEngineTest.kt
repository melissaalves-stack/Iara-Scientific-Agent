package org.iara.campo.agent

import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Testes do agente de campo. Rodam no computador, sem celular: ./gradlew test */
class EdgeAgentEngineTest {

    // Dicionário falso para os testes (no app, a busca é feita no SQLite com FTS)
    private val dicionario = mapOf(
        "andiroba" to PlantaEncontrada("andiroba", "Carapa guianensis", "Meliaceae", "anti-inflamatório"),
    )
    private fun novoAgente() = EdgeAgentEngine(buscarPlanta = { texto ->
        dicionario.entries.firstOrNull { Lexico.normalizar(texto).contains(it.key) }?.value
    })

    @Test
    fun `conduz o dialogo ate o registro completo`() = runBlocking {
        val agente = novoAgente()
        agente.processar("Dona Raimunda tira o óleo da semente da andiroba")
        assertEquals("andiroba", agente.rascunho.nomePopular)
        assertEquals("semente", agente.rascunho.parteUsada)
        assertEquals(Campo.INDICACAO, agente.proximoCampo())

        agente.processar("Passa no inchaço e na ferida")
        agente.processar("Cozinha as sementes e espreme a massa")
        agente.processar("Cai de janeiro a abril")
        agente.processar("Comunidade A")
        val resposta = agente.processar("3")

        assertEquals("publicacao_completa", agente.rascunho.consentimento)
        assertEquals("Cozinha as sementes e espreme a massa", agente.rascunho.modoPreparo)
        assertEquals("Comunidade A", agente.rascunho.comunidade)
        assertTrue(agente.completo())
        assertTrue(resposta.contains("Relato completo"))
    }

    @Test
    fun `narrativa livre aproveita varios campos de uma vez`() = runBlocking {
        val agente = novoAgente()
        agente.processar("o chá da casca de andiroba é bom pra febre")
        assertEquals("casca", agente.rascunho.parteUsada)
        assertTrue(agente.rascunho.indicacao != null && agente.rascunho.modoPreparo != null)
        assertEquals(Campo.SAZONALIDADE, agente.proximoCampo())
    }

    @Test
    fun `nome desconhecido e aceito quando a resposta e curta`() = runBlocking {
        val agente = novoAgente()
        agente.processar("pau-de-angola")
        assertEquals("pau-de-angola", agente.rascunho.nomePopular)
    }

    @Test
    fun `frase longa sem planta conhecida nao vira nome`() = runBlocking {
        val agente = novoAgente()
        agente.processar("o mateiro falou de uma planta boa pra ferida")
        assertNull(agente.rascunho.nomePopular)
        assertEquals(Campo.NOME, agente.proximoCampo())
    }

    @Test
    fun `consentimento ambiguo pede de novo`() = runBlocking {
        val agente = novoAgente()
        listOf("andiroba", "semente", "inchaço", "cozinha", "janeiro", "Comunidade A").forEach { agente.processar(it) }
        val resposta = agente.processar("talvez")
        assertNull(agente.rascunho.consentimento)
        assertTrue(resposta.contains("Responda 1, 2 ou 3"))
    }

    @Test
    fun `interpreta escopos de consentimento`() {
        assertEquals("uso_interno", Lexico.interpretarConsentimento("Por enquanto só pra pesquisa interna"))
        assertEquals("publicacao_sem_conhecimento",
            Lexico.interpretarConsentimento("Pode publicar que a planta ocorre aqui, mas o uso fica com a gente"))
        assertEquals("publicacao_completa", Lexico.interpretarConsentimento("Sim, autoriza publicar tudo"))
    }
}
