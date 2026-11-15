import { useState } from "react";
import { consultar } from "../api";
import type { RespostaConsulta } from "../types";

const EXEMPLOS = ["Achados inéditos desta expedição", "Quantos registros em área protegida?", "Registros de andiroba"];

export default function ChatBar({ demo }: { demo: boolean }) {
  const [pergunta, setPergunta] = useState("");
  const [historico, setHistorico] = useState<{ pergunta: string; resposta: RespostaConsulta | string }[]>([]);
  const [carregando, setCarregando] = useState(false);

  async function perguntar(texto: string) {
    if (!texto.trim()) return;
    setPergunta("");
    if (demo) {
      setHistorico((h) => [...h, {
        pergunta: texto,
        resposta: "No modo demonstração o chat fica desligado: ele consulta o banco de dados do servidor. Rode o projeto com docker compose para testar.",
      }]);
      return;
    }
    setCarregando(true);
    try {
      const resposta = await consultar(texto);
      setHistorico((h) => [...h, { pergunta: texto, resposta }]);
    } catch (e) {
      setHistorico((h) => [...h, { pergunta: texto, resposta: `Erro: ${(e as Error).message}` }]);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <section className="chat" aria-label="Pergunte ao Iara">
      {historico.length > 0 && (
        <div className="chat-historico" aria-live="polite">
          {historico.map((item, i) => (
            <div key={i} className="chat-troca">
              <p className="chat-pergunta">{item.pergunta}</p>
              <pre className="chat-resposta">
                {typeof item.resposta === "string" ? item.resposta : item.resposta.resposta}
              </pre>
              {typeof item.resposta !== "string" && (
                <details className="chat-filtro">
                  <summary>Filtro gerado ({item.resposta.modo === "llm" ? "LLM" : "regras"})</summary>
                  <code>{JSON.stringify(item.resposta.filtro)}</code>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
      <form
        className="chat-entrada"
        onSubmit={(e) => {
          e.preventDefault();
          perguntar(pergunta);
        }}
      >
        <h2 className="chat-titulo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 5h16v11H9l-5 4V5Z" />
          </svg>
          Pergunte ao Iara
        </h2>
        <input
          value={pergunta}
          onChange={(e) => setPergunta(e.target.value)}
          placeholder="Ex.: quais registros de copaíba têm uso confirmado por artigo?"
          aria-label="Pergunta"
        />
        <button className="primario" disabled={carregando}>{carregando ? "…" : "Perguntar"}</button>
      </form>
      <div className="chat-exemplos">
        {EXEMPLOS.map((ex) => (
          <button key={ex} className="chip" onClick={() => perguntar(ex)}>{ex}</button>
        ))}
      </div>
    </section>
  );
}
