import { useEffect, useState } from "react";
import { carregar, type DadosIniciais } from "./api";
import ChatBar from "./components/ChatBar";
import Drawer from "./components/Drawer";
import { Assinatura, ChuvaDeGotas, IconePlanta, IconeStatus } from "./components/Marca";
import Mapa from "./components/Mapa";
import { exportar } from "./darwinCore";
import { CLASSIFICACOES, type Classificacao, type Registro } from "./types";

export default function App() {
  const [dados, setDados] = useState<DadosIniciais | null>(null);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Classificacao | null>(null);
  const [avisoExport, setAvisoExport] = useState<string | null>(null);

  useEffect(() => {
    carregar().then(setDados);
  }, []);

  if (!dados) {
    return (
      <div className="carregando">
        <ChuvaDeGotas />
        <p>Carregando registros…</p>
      </div>
    );
  }

  const visiveis = filtro ? dados.registros.filter((r) => r.classificacao === filtro) : dados.registros;
  const registro = dados.registros.find((r) => r.id === selecionado) ?? null;
  const contagem = (c: Classificacao) => dados.registros.filter((r) => r.classificacao === c).length;

  function atualizar(novo: Registro) {
    setDados((d) => d && { ...d, registros: d.registros.map((r) => (r.id === novo.id ? novo : r)) });
  }

  function exportarExpedicao(formato: "csv" | "json") {
    const n = exportar(dados!.registros, formato, "iara_expedicao_darwin_core");
    const retidos = dados!.registros.length - n;
    setAvisoExport(`${n} registro(s) exportado(s)${retidos ? `; ${retidos} retido(s) por consentimento ou alerta` : ""}.`);
    setTimeout(() => setAvisoExport(null), 6000);
  }

  return (
    <div className="app">
      <header className="topo">
        <div className="marca">
          <Assinatura negativa />
          <span className="divisor" />
          <span className="subtitulo">Painel do curador</span>
        </div>
        <nav className="filtros" aria-label="Filtrar por status">
          {(Object.keys(CLASSIFICACOES) as Classificacao[]).map((c) => (
            <button
              key={c}
              className={`filtro ${filtro === c ? "ativo" : ""}`}
              style={{ background: CLASSIFICACOES[c].fundo, color: CLASSIFICACOES[c].cor }}
              aria-pressed={filtro === c}
              onClick={() => setFiltro(filtro === c ? null : c)}
            >
              <IconeStatus status={c} cor={CLASSIFICACOES[c].cor} />
              {CLASSIFICACOES[c].rotulo}
              <strong>{contagem(c)}</strong>
            </button>
          ))}
        </nav>
        <div className="exportar">
          <button className="claro" onClick={() => exportarExpedicao("csv")}>⤓ Darwin Core CSV</button>
          <button className="claro" onClick={() => exportarExpedicao("json")}>JSON</button>
        </div>
      </header>

      {(dados.demo || avisoExport) && (
        <p className="faixa">
          {avisoExport ?? (
            <>
              Modo demonstração: registros gerados pelo simulador de expedição. Mapas, GBIF e literatura são dados
              reais; relatos e comunidades são fictícios. Para usar com o servidor, rode <code>docker compose up</code>.
            </>
          )}
        </p>
      )}

      <main className="corpo">
        <div className="coluna-mapa">
          <Mapa registros={visiveis} camadas={dados.camadas} selecionado={selecionado} onSelecionar={setSelecionado} />
          <ChatBar demo={dados.demo} />
        </div>
        {registro ? (
          <Drawer key={registro.id} registro={registro} demo={dados.demo} onFechar={() => setSelecionado(null)} onAtualizar={atualizar} />
        ) : (
          <aside className="drawer drawer-vazio">
            <div className="capa">
              <ChuvaDeGotas />
            </div>
            <div className="drawer-corpo">
              <h2>{visiveis.length} registros de campo</h2>
              <p>Escolha um pino no mapa para ver a conversa de campo, o parecer dos três agentes e as ações de curadoria.</p>
              <ul className="lista">
                {visiveis.map((r) => {
                  const c = r.classificacao ? CLASSIFICACOES[r.classificacao] : null;
                  return (
                    <li key={r.id}>
                      <button className="item" onClick={() => setSelecionado(r.id)}>
                        <span className="icone-especie pequeno"><IconePlanta /></span>
                        <span className="item-texto">
                          <strong>{r.nome_popular}</strong>
                          <em className="cientifico">{r.nome_cientifico ?? "a identificar"}</em>
                        </span>
                        {c && (
                          <span className="selo mini" style={{ background: c.fundo, color: c.cor }}>
                            <IconeStatus status={r.classificacao} cor={c.cor} tamanho={12} />
                            {c.rotulo}
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          </aside>
        )}
      </main>
    </div>
  );
}
