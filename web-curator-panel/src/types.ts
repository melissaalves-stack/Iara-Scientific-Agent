export type Classificacao = "validado" | "achado_inedito" | "alerta_geografico" | "revisao_taxonomica";

export interface Mensagem {
  autor: "pesquisador" | "agente";
  texto: string;
}

export interface Parecer {
  agente: "taxonomista" | "geoespacial" | "rag_cientifico";
  status: "ok" | "alerta" | "erro";
  resumo: string;
  detalhes: Record<string, any>;
}

export interface Registro {
  id: string;
  expedicao_id: string;
  nome_popular: string;
  nome_cientifico: string | null;
  familia: string | null;
  parte_usada: string | null;
  modo_preparo: string | null;
  indicacao: string | null;
  sazonalidade: string | null;
  comunidade: string | null;
  conversa: Mensagem[];
  consentimento_escopo: string;
  latitude: number;
  longitude: number;
  precisao_gps_m: number | null;
  coletado_em: string;
  fotos: string[];
  qualidade_foto: { nitidez: number; brilho: number; aprovada: boolean; motivo: string | null } | null;
  status: string;
  classificacao: Classificacao | null;
  score_consistencia: number | null;
  nota_curador: string | null;
  pareceres: Parecer[];
  darwin_core: Record<string, string | number> | null;
}

export interface RespostaConsulta {
  resposta: string;
  total: number;
  modo: "regras" | "llm";
  filtro: Record<string, unknown>;
}

// Paleta Folha-gota (docs/IDENTIDADE_VISUAL.md)
export const CLASSIFICACOES: Record<Classificacao, { rotulo: string; cor: string; fundo: string; descricao: string }> = {
  validado: { rotulo: "Validado", cor: "#1F4A33", fundo: "#DDE8DF", descricao: "Coerente nos 3 pareceres" },
  achado_inedito: { rotulo: "Achado inédito", cor: "#5A2A50", fundo: "#EBDDE7", descricao: "Uso sem paralelo na literatura" },
  alerta_geografico: { rotulo: "Alerta geográfico", cor: "#A3401F", fundo: "#F5DED4", descricao: "Fora da área esperada" },
  revisao_taxonomica: { rotulo: "Revisão taxonômica", cor: "#1D3B4F", fundo: "#DCE5EC", descricao: "Nome ou sinonímia a conferir" },
};

export const CONSENTIMENTOS: Record<string, string> = {
  uso_interno: "Uso interno da pesquisa; não publicar",
  publicacao_sem_conhecimento: "Publicar a ocorrência; o uso fica com a comunidade",
  publicacao_completa: "Publicação completa autorizada",
  revogado: "Consentimento revogado pela comunidade",
};
