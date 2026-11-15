// Comunicação com o backend. Se a API não responder (ou no build de demonstração),
// o painel carrega public/demo-data.json e funciona em "modo demonstração".
import type { Registro, RespostaConsulta } from "./types";

const API = import.meta.env.VITE_API_URL ?? "";
const FORCAR_DEMO = import.meta.env.VITE_DEMO === "true";

export type Camadas = Record<string, GeoJSON.FeatureCollection>;

export interface DadosIniciais {
  registros: Registro[];
  camadas: Camadas;
  demo: boolean;
}

const NOMES_CAMADAS = ["amazonia_legal", "areas_protegidas", "terras_indigenas", "rios_principais"];

async function carregarDemo(): Promise<DadosIniciais> {
  const resp = await fetch("./demo-data.json");
  const dados = await resp.json();
  return { registros: dados.registros, camadas: dados.camadas, demo: true };
}

export async function carregar(): Promise<DadosIniciais> {
  if (FORCAR_DEMO) return carregarDemo();
  try {
    const resp = await fetch(`${API}/api/v1/registros`);
    if (!resp.ok) throw new Error(String(resp.status));
    const registros: Registro[] = await resp.json();
    const camadas: Camadas = {};
    for (const nome of NOMES_CAMADAS) {
      camadas[nome] = await (await fetch(`${API}/api/v1/camadas/${nome}`)).json();
    }
    return { registros, camadas, demo: false };
  } catch {
    return carregarDemo();
  }
}

export function urlFoto(caminho: string, demo: boolean): string {
  // No modo demo as fotos ficam em public/demo-fotos
  return demo ? `./demo-fotos/${caminho.split("/").pop()}` : `${API}${caminho}`;
}

async function enviar(caminho: string, metodo: string, corpo?: unknown): Promise<Registro> {
  const resp = await fetch(`${API}${caminho}`, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  });
  if (!resp.ok) throw new Error(`Erro ${resp.status}`);
  return resp.json();
}

export const aprovar = (id: string, nota?: string) =>
  enviar(`/api/v1/registros/${id}/aprovar`, "POST", { nota_curador: nota || null });

export const editar = (id: string, campos: Partial<Registro>) =>
  enviar(`/api/v1/registros/${id}`, "PATCH", campos);

export const reprocessar = (id: string) => enviar(`/api/v1/registros/${id}/reprocessar`, "POST");

export const revogar = (id: string) => enviar(`/api/v1/registros/${id}/revogar-consentimento`, "POST");

export async function consultar(pergunta: string): Promise<RespostaConsulta> {
  const resp = await fetch(`${API}/api/v1/copilot/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pergunta }),
  });
  if (!resp.ok) throw new Error(`Erro ${resp.status}`);
  return resp.json();
}
