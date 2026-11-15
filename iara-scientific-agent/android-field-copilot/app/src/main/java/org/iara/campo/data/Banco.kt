package org.iara.campo.data

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Fts4
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import kotlinx.coroutines.flow.Flow

/**
 * Banco local do celular (Room = SQLite com uma camada Kotlin por cima).
 *
 * - registros:   relatos coletados em campo, com a fila de sincronização
 *                (campo `sincronizado`).
 * - dicionario:  mini-dicionário etnobotânico com busca de texto completo (FTS),
 *                para reconhecer nomes de plantas sem internet.
 */

@Entity(tableName = "registros")
data class RegistroEntity(
    @PrimaryKey val id: String,                 // UUID gerado no celular
    val nomePopular: String,
    val parteUsada: String?,
    val modoPreparo: String?,
    val indicacao: String?,
    val sazonalidade: String?,
    val comunidade: String?,
    val consentimento: String,                  // uso_interno | publicacao_sem_conhecimento | publicacao_completa
    val latitude: Double,
    val longitude: Double,
    val precisaoGpsM: Float?,
    val coletadoEm: String,                     // data/hora ISO-8601
    val fotoCaminho: String?,                   // arquivo no armazenamento interno do app
    val qualidadeFotoJson: String?,
    val conversaJson: String,                   // conversa com o agente, em JSON
    val sincronizado: Boolean = false,
)

/** Tabela virtual FTS4: o SQLite cria um índice de palavras para busca rápida. */
@Fts4
@Entity(tableName = "dicionario")
data class DicionarioEntity(
    val termos: String,          // todos os nomes, normalizados (sem acento) e separados por "|"
    val nomePopular: String,     // nome principal para exibir
    val nomeCientifico: String,
    val familia: String,
    val usosConhecidos: String,
)

@Dao
interface RegistroDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun salvar(registro: RegistroEntity)

    @Query("SELECT * FROM registros ORDER BY coletadoEm DESC")
    fun observarTodos(): Flow<List<RegistroEntity>>

    @Query("SELECT * FROM registros WHERE sincronizado = 0")
    suspend fun pendentes(): List<RegistroEntity>

    @Query("UPDATE registros SET sincronizado = 1 WHERE id IN (:ids)")
    suspend fun marcarSincronizados(ids: List<String>)
}

@Dao
interface DicionarioDao {
    @Insert
    suspend fun inserir(itens: List<DicionarioEntity>)

    @Query("SELECT COUNT(*) FROM dicionario")
    suspend fun total(): Int

    /** Ex.: buscar("andirob*") encontra "andiroba" e "andirobeira". */
    @Query("SELECT * FROM dicionario WHERE dicionario MATCH :consulta LIMIT 5")
    suspend fun buscar(consulta: String): List<DicionarioEntity>
}

@Database(entities = [RegistroEntity::class, DicionarioEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun registros(): RegistroDao
    abstract fun dicionario(): DicionarioDao

    companion object {
        @Volatile private var instancia: AppDatabase? = null

        fun get(context: Context): AppDatabase =
            instancia ?: synchronized(this) {
                instancia ?: Room.databaseBuilder(context.applicationContext, AppDatabase::class.java, "iara.db")
                    .build()
                    .also { instancia = it }
            }
    }
}
