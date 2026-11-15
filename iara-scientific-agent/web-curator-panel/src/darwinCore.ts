// Gera os arquivos Darwin Core no navegador a partir do campo `darwin_core`
// que o backend já calcula (respeitando o consentimento da comunidade).
import type { Registro } from "./types";

function baixar(conteudo: string, nome: string, tipo: string) {
  const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }));
  const link = document.createElement("a");
  link.href = url;
  link.download = nome;
  link.click();
  URL.revokeObjectURL(url);
}

function csvCelula(valor: unknown): string {
  const texto = valor === null || valor === undefined ? "" : String(valor);
  return /[",\n]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto;
}

export function exportar(registros: Registro[], formato: "csv" | "json", nome: string): number {
  const linhas = registros.map((r) => r.darwin_core).filter((d): d is NonNullable<typeof d> => d !== null);
  if (linhas.length === 0) return 0;
  if (formato === "json") {
    baixar(JSON.stringify(linhas, null, 2), `${nome}.json`, "application/json");
  } else {
    const campos = Object.keys(linhas[0]);
    const csv = [campos.join(","), ...linhas.map((l) => campos.map((c) => csvCelula(l[c])).join(","))].join("\n");
    baixar(csv, `${nome}.csv`, "text/csv;charset=utf-8");
  }
  return linhas.length;
}
