import { useState } from "react";
import * as api from "../api";
import { exportar } from "../darwinCore";
import { CLASSIFICACOES, CONSENTIMENTOS, type Parecer, type Registro } from "../types";
import { IconePlanta, IconeStatus } from "./Marca";

interface Props {
  registro: Registro;
  demo: boolean;
  onFechar: () => void;
  onAtualizar: (r: Registro) => void;
}

// Cada agente assina uma nota de herbário: numeral romano, nome, fonte consultada.
const AGENTES: Record<Parecer["agente"], { numeral: string; nome: string; fonte: string }> = {
  taxonomista: { numeral: "I", nome: "Taxonomista", fonte: "GBIF · SiBBr" },
  geoespacial: { numeral: "II", nome: "Geoespacial", fonte: "IBGE · CNUC · FUNAI · GBIF" },
  rag_cientifico: { numeral: "III", nome: "RAG Científico", fonte: "Literatura com DOI" },
};

function estado(p: Parecer): { texto: string; classe: string } {
  if (p.agente === "rag_cientifico" && p.detalhes.achado_inedito) return { texto: "Inédito", classe: "inedito" };
  if (p.agente === "taxonomista" && p.detalhes.taxonomia?.observacao) return { texto: "Atenção", classe: "atencao" };
  return p.status === "ok" ? { texto: "OK", classe: "ok" } : { texto: "Atenção", classe: "atencao" };
}

function NomeCientifico({ nome }: { nome: string }) {
  return <em className="cientifico">{nome}</em>;
}

/** Coloca nomes científicos em itálico dentro de um texto corrido (convenção botânica). */
function comItalico(texto: string, nomes: string[]) {
  const validos = [...new Set(nomes.filter(Boolean))].sort((a, b) => b.length - a.length);
  if (validos.length === 0) return texto;
  const padrao = new RegExp(`(${validos.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "g");
  return texto.split(padrao).map((parte, i) => (validos.includes(parte) ? <em key={i} className="cientifico">{parte}</em> : parte));
}

function DetalhesParecer({ parecer }: { parecer: Parecer }) {
  const d = parecer.detalhes;
  if (parecer.agente === "taxonomista") {
    const t = d.taxonomia ?? {};
    return (
      <dl className="ficha">
        {t.sinonimos?.length > 0 && (<><dt>Sinônimo</dt><dd>{t.sinonimos.map((s: string) => <NomeCientifico key={s} nome={s} />)}</dd></>)}
        {t.ocorrencias_brasil != null && (<><dt>Ocorrências BR</dt><dd>{t.ocorrencias_brasil.toLocaleString("pt-BR")} no GBIF</dd></>)}
        {t.identificador && (
          <><dt>Identificador</dt><dd className="quebra">
            {t.identificador.startsWith("http")
              ? <a href={t.identificador} target="_blank" rel="noreferrer">{t.identificador.replace("https://www.", "")}</a>
              : t.identificador}
          </dd></>
        )}
      </dl>
    );
  }
  if (parecer.agente === "geoespacial") {
    return (
      <dl className="ficha">
        {d.bioma && (<><dt>Bioma</dt><dd>{d.bioma}</dd></>)}
        {d.terra_indigena && (<><dt>Terra Indígena</dt><dd>{d.terra_indigena} <span className="sensivel">dado sensível</span></dd></>)}
        {d.ocorrencias_gbif_100km != null && (<><dt>GBIF em 100 km</dt><dd>{d.ocorrencias_gbif_100km} registro(s) da espécie</dd></>)}
        {d.rio_mais_proximo && (<><dt>Rio mais próximo</dt><dd>{d.rio_mais_proximo} ({Math.round(d.distancia_rio_km)} km)</dd></>)}
      </dl>
    );
  }
  return (
    <>
      <dl className="ficha">
        <dt>Usos relatados</dt><dd>{d.categorias_relatadas?.join(", ").replace(/_/g, " ") || "—"}</dd>
        <dt>Confirmados</dt><dd>{d.categorias_confirmadas?.join(", ").replace(/_/g, " ") || "—"}</dd>
        {d.categorias_nao_documentadas?.length > 0 && (<><dt>Sem paralelo</dt><dd>{d.categorias_nao_documentadas.join(", ").replace(/_/g, " ")}</dd></>)}
      </dl>
      {d.evidencias?.length > 0 && (
        <details className="evidencias">
          <summary>Artigos consultados ({d.evidencias.length})</summary>
          {d.evidencias.map((e: any) => (
            <div key={e.documento} className="evidencia">
              <strong>{e.titulo}</strong>
              <span className="referencia">{e.referencia}</span>
              {e.url && <a href={e.url} target="_blank" rel="noreferrer">{e.doi ? `doi:${e.doi}` : "abrir"}</a>}
              <p>{e.trecho}</p>
            </div>
          ))}
        </details>
      )}
    </>
  );
}

function formatarData(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" }).replace(".", "") +
    ", " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export default function Drawer({ registro: r, demo, onFechar, onAtualizar }: Props) {
  const [editando, setEditando] = useState(false);
  const [mostrarConversa, setMostrarConversa] = useState(false);
  const [form, setForm] = useState({
    nome_cientifico: r.nome_cientifico ?? "",
    parte_usada: r.parte_usada ?? "",
    indicacao: r.indicacao ?? "",
    nota_curador: r.nota_curador ?? "",
  });
  const [aviso, setAviso] = useState<string | null>(null);
  const classe = r.classificacao ? CLASSIFICACOES[r.classificacao] : null;
  const geo = r.pareceres.find((p) => p.agente === "geoespacial")?.detalhes;
  const tax = r.pareceres.find((p) => p.agente === "taxonomista")?.detalhes?.taxonomia;
  const sugestao: [number, number] | null = geo?.coordenada_sugerida ?? null;
  const conversa = mostrarConversa ? r.conversa : r.conversa.slice(-4);

  async function acao(fn: () => Promise<Registro>, local: Partial<Registro>, mensagem: string) {
    setAviso(null);
    try {
      if (demo) {
        onAtualizar({ ...r, ...local });
        setAviso(`${mensagem} (modo demonstração: nada foi salvo)`);
      } else {
        onAtualizar(await fn());
        setAviso(mensagem);
      }
    } catch (e) {
      setAviso(`Falhou: ${(e as Error).message}`);
    }
  }

  function exportarRegistro(formato: "csv" | "json") {
    if (exportar([r], formato, `iara_${r.nome_popular}`) === 0) {
      setAviso("Não exportável: a comunidade não autorizou a publicação ou há alerta geográfico a corrigir.");
    }
  }

  const notaExportacao =
    r.darwin_core === null
      ? "Este registro não pode ser exportado: falta consentimento ou há alerta geográfico."
      : r.consentimento_escopo === "publicacao_sem_conhecimento"
        ? "A exportação inclui só a ocorrência, conforme o consentimento."
        : "A exportação inclui o uso tradicional, autorizado pela comunidade. Coordenadas arredondadas a ~1 km.";

  return (
    <aside className="drawer" aria-label={`Registro de ${r.nome_popular}`}>
      <header className="drawer-topo">
        <span className="icone-especie"><IconePlanta /></span>
        <div className="drawer-titulo">
          <h2>{r.nome_popular}</h2>
          {r.nome_cientifico ? (
            <p className="linha-cientifica">
              <NomeCientifico nome={r.nome_cientifico} /> {tax?.autoria && <span className="autoria">{tax.autoria}</span>}
              {r.familia && <span className="familia"> · {r.familia}</span>}
            </p>
          ) : (
            <p className="linha-cientifica">Táxon não resolvido</p>
          )}
        </div>
        <button className="fechar" onClick={onFechar} aria-label="Fechar">×</button>
      </header>

      <div className="resumo-status">
        {classe && (
          <span className="selo" style={{ background: classe.fundo, color: classe.cor }}>
            <span className="selo-icone" style={{ background: classe.cor }}><IconeStatus status={r.classificacao} cor="#fff" tamanho={12} /></span>
            {classe.rotulo}
          </span>
        )}
        {r.status === "aprovado" && <span className="selo aprovado">✓ Aprovado</span>}
        {r.score_consistencia !== null && (
          <span className="score">Score de consistência <strong>{r.score_consistencia}/100</strong></span>
        )}
      </div>
      {r.score_consistencia !== null && (
        <div className="barra-score"><span style={{ width: `${r.score_consistencia}%` }} /></div>
      )}

      <div className="drawer-corpo">
        {r.fotos[0] && (
          <figure className="foto">
            <img src={api.urlFoto(r.fotos[0], demo)} alt={`Foto do registro de ${r.nome_popular}`} />
            {r.qualidade_foto && (
              <figcaption className={r.qualidade_foto.aprovada ? "ok" : "ruim"}>
                {r.qualidade_foto.aprovada ? "✓ Nitidez aprovada" : `! ${r.qualidade_foto.motivo}`}
              </figcaption>
            )}
          </figure>
        )}

        {editando ? (
          <div className="form">
            {(["nome_cientifico", "parte_usada", "indicacao", "nota_curador"] as const).map((campo) => (
              <label key={campo}>
                {campo.replace("_", " ")}
                <input value={form[campo]} onChange={(e) => setForm({ ...form, [campo]: e.target.value })} />
              </label>
            ))}
            <div className="linha-botoes">
              <button
                className="primario"
                onClick={async () => {
                  await acao(async () => {
                    await api.editar(r.id, form as Partial<Registro>);
                    return api.reprocessar(r.id);
                  }, form, "Registro editado e reavaliado pelo comitê");
                  setEditando(false);
                }}
              >Salvar e reavaliar</button>
              <button className="secundario" onClick={() => setEditando(false)}>Cancelar</button>
            </div>
          </div>
        ) : (
          <dl className="dados">
            <dt>Local</dt>
            <dd>{geo?.municipio ? `${geo.municipio}/${geo.uf}` : "—"}{geo?.area_protegida && ` · ${geo.area_protegida}`}</dd>
            <dt>Coordenadas</dt>
            <dd className="mono">
              {r.latitude.toFixed(3).replace(".", ",")} {r.longitude.toFixed(3).replace(".", ",")}
              {r.precisao_gps_m != null && ` · ±${Math.round(r.precisao_gps_m)} m`}
            </dd>
            <dt>Coletado</dt><dd>{formatarData(r.coletado_em)}</dd>
            <dt>Comunidade</dt><dd>{r.comunidade ?? "—"}</dd>
            <dt>Parte usada</dt><dd>{r.parte_usada ?? "—"}</dd>
            <dt>Indicação</dt><dd>{r.indicacao ?? "—"}</dd>
            <dt>Preparo</dt><dd>{r.modo_preparo ?? "—"}</dd>
            {r.sazonalidade && (<><dt>Época</dt><dd>{r.sazonalidade}</dd></>)}
            <dt>Consentimento</dt>
            <dd className={`consentimento c-${r.consentimento_escopo}`}>{CONSENTIMENTOS[r.consentimento_escopo]}</dd>
            {r.nota_curador && (<><dt>Nota do curador</dt><dd>{r.nota_curador}</dd></>)}
          </dl>
        )}

        <section>
          <h3>Parecer do comitê</h3>
          {r.pareceres.length === 0 && <p className="vazio-texto">Aguardando processamento…</p>}
          {r.pareceres.map((p) => {
            const a = AGENTES[p.agente];
            const e = estado(p);
            return (
              <article key={p.agente} className="parecer">
                <div className="parecer-lateral">
                  <span className="numeral">{a.numeral}</span>
                </div>
                <div className="parecer-corpo">
                  <header>
                    <h4>{a.nome} <small>{a.fonte}</small></h4>
                    <span className={`estado ${e.classe}`}>{e.texto}</span>
                  </header>
                  <p>{comItalico(p.resumo, [r.nome_cientifico ?? "", ...(tax?.sinonimos ?? [])])}</p>
                  <DetalhesParecer parecer={p} />
                </div>
              </article>
            );
          })}
          {sugestao && (
            <button
              className="secundario largo"
              onClick={() =>
                acao(async () => {
                  await api.editar(r.id, { latitude: sugestao[0], longitude: sugestao[1] });
                  return api.reprocessar(r.id);
                }, { latitude: sugestao[0], longitude: sugestao[1] }, "Coordenada corrigida e reavaliada")
              }
            >Aplicar coordenada sugerida ({sugestao[0]}, {sugestao[1]})</button>
          )}
        </section>

        <section>
          <h3>Conversa de campo</h3>
          <div className="conversa">
            {r.conversa.length === 0 && <p className="vazio-texto">Sem conversa registrada.</p>}
            {conversa.map((m, i) => (
              <div key={i} className={`balao ${m.autor}`}>{m.texto}</div>
            ))}
          </div>
          {r.conversa.length > 4 && (
            <button className="link" onClick={() => setMostrarConversa(!mostrarConversa)}>
              {mostrarConversa ? "Mostrar só o final" : `Ver conversa completa (${r.conversa.length} mensagens)`}
            </button>
          )}
        </section>
      </div>

      <footer className="acoes">
        {aviso && <p className="aviso" role="status">{aviso}</p>}
        <div className="linha-botoes">
          <button
            className="primario"
            disabled={r.status === "aprovado"}
            onClick={() => acao(() => api.aprovar(r.id, form.nota_curador), { status: "aprovado" }, "Registro aprovado")}
          >✓ Aprovar</button>
          <button className="secundario" onClick={() => setEditando(true)}>Editar</button>
          <span className="grupo-export">
            <button className="secundario" onClick={() => exportarRegistro("csv")}>Darwin Core CSV</button>
            <button className="secundario" onClick={() => exportarRegistro("json")}>JSON</button>
          </span>
        </div>
        <p className="nota-exportacao">{notaExportacao}</p>
        <button
          className="link perigo"
          disabled={r.consentimento_escopo === "revogado"}
          onClick={() => {
            if (window.confirm("A comunidade revogou o consentimento? O conhecimento tradicional deste registro será apagado.")) {
              acao(() => api.revogar(r.id),
                { consentimento_escopo: "revogado", indicacao: null, modo_preparo: null, conversa: [], darwin_core: null },
                "Consentimento revogado e conhecimento apagado");
            }
          }}
        >Revogar consentimento</button>
      </footer>
    </aside>
  );
}
