// Identidade visual "Folha-gota": a gota é folha e água num gesto só.
// A nervura divide a forma: verde-copaíba à esquerda (o saber da planta) e
// Rio Negro à direita (a mãe-d'água). Ver docs/IDENTIDADE_VISUAL.md.
import type { Classificacao } from "../types";

const GOTA = "M12 1C12 1 3 11.5 3 19.5a9 9 0 0 0 18 0C21 11.5 12 1 12 1Z";
const METADE_ESQUERDA = "M-1 -1L12 1Q8.6 14 13.4 30L-1 30Z";

/** A folha-gota. `negativa` = versão para fundos escuros. */
export function Gota({ tamanho = 24, negativa = false, id = "g" }: { tamanho?: number; negativa?: boolean; id?: string }) {
  const esquerda = negativa ? "#F3EDDD" : "#1F4A33";
  const direita = negativa ? "#9CC3D5" : "#1D3B4F";
  return (
    <svg width={tamanho * 0.75} height={tamanho} viewBox="0 0 24 32" aria-hidden="true">
      <defs>
        <clipPath id={`clip-${id}`}>
          <path d={METADE_ESQUERDA} />
        </clipPath>
      </defs>
      <path d={GOTA} fill={direita} />
      <path d={GOTA} fill={esquerda} clipPath={`url(#clip-${id})`} />
    </svg>
  );
}

/** Assinatura "ıara": a folha-gota é o pingo do i. */
export function Assinatura({ negativa = false }: { negativa?: boolean }) {
  return (
    <span className={`assinatura ${negativa ? "negativa" : ""}`} aria-label="iara">
      <span className="assinatura-i">
        <span className="assinatura-pingo">
          <Gota tamanho={13} negativa={negativa} id="pingo" />
        </span>
        ı
      </span>
      ara
    </span>
  );
}

// ---------- Ícones de status (o mesmo desenho no pino, no selo e na legenda) ----------

export function IconeStatus({ status, cor = "currentColor", tamanho = 14 }: { status: Classificacao | null; cor?: string; tamanho?: number }) {
  const p = { fill: "none", stroke: cor, strokeWidth: 2.4, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 16 16" aria-hidden="true">
      {status === "validado" && <path d="M3.5 8.5l3 3 6-7" {...p} />}
      {status === "achado_inedito" && (
        <>
          <path d="M8 14V8.5" {...p} />
          <path d="M4 3.5c0 3 1.8 5 4 5s4-2 4-5c-1.3.6-2.6.6-4-1.5-1.4 2.1-2.7 2.1-4 1.5Z" {...p} />
        </>
      )}
      {status === "alerta_geografico" && (
        <>
          <path d="M8 3v6.5" {...p} />
          <circle cx="8" cy="12.8" r="1.1" fill={cor} />
        </>
      )}
      {status === "revisao_taxonomica" && (
        <>
          <circle cx="7" cy="7" r="3.6" {...p} />
          <path d="M9.8 9.8L13 13" {...p} />
        </>
      )}
      {status === null && <circle cx="8" cy="8" r="2.2" fill={cor} />}
    </svg>
  );
}

/** Pino do mapa: a folha-gota invertida (único uso em que ela gira, 180°). */
export function pinoSvg(cor: string, status: Classificacao | null, ativo: boolean): string {
  const w = ativo ? 40 : 30;
  const h = Math.round(w * 1.3);
  const icones: Record<string, string> = {
    validado: '<path d="M10 15.5l3 3 6-7" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>',
    achado_inedito:
      '<g fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 20v-5"/><path d="M10.5 10c0 3 1.8 5 4 5s4-2 4-5c-1.3.6-2.6.6-4-1.5-1.4 2.1-2.7 2.1-4 1.5Z"/></g>',
    alerta_geografico:
      '<path d="M14.5 9v6.5" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/><circle cx="14.5" cy="19.2" r="1.4" fill="#fff"/>',
    revisao_taxonomica:
      '<g fill="none" stroke="#fff" stroke-width="2.3" stroke-linecap="round"><circle cx="13.6" cy="13.4" r="3.6"/><path d="M16.4 16.2l3 3"/></g>',
  };
  return `<svg width="${w}" height="${h}" viewBox="0 0 29 38" xmlns="http://www.w3.org/2000/svg">
    <path d="M14.5 37C14.5 37 2 23.5 2 14a12.5 12.5 0 0 1 25 0c0 9.5-12.5 23-12.5 23Z" fill="${cor}" stroke="#FBF8F0" stroke-width="2"/>
    ${status ? icones[status] : '<circle cx="14.5" cy="14" r="3" fill="#fff"/>'}
  </svg>`;
}

/** Ícone genérico de planta para cabeçalhos e listas. */
export function IconePlanta({ cor = "#1F4A33" }: { cor?: string }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke={cor} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 21V9" />
      <path d="M12 13c-3.5 0-6-2.5-6-6 3.5 0 6 2.5 6 6Z" />
      <path d="M12 11c3.5 0 6-2.5 6-6-3.5 0-6 2.5-6 6Z" />
      <path d="M12 17c-2.6 0-4.5-1.8-4.5-4.5 2.6 0 4.5 1.8 4.5 4.5Z" />
    </svg>
  );
}

/** Padrão "chuva de gotas": várias gotas apagadas e uma bicolor em destaque. */
export function ChuvaDeGotas() {
  const gotas = [];
  for (let linha = 0; linha < 4; linha++) {
    for (let col = 0; col < 7; col++) {
      const x = col * 34 + (linha % 2 ? 17 : 0) + 8;
      const y = linha * 30 + (col % 2 ? 6 : 0) + 6;
      if (linha === 1 && col === 3) continue;
      gotas.push(<path key={`${linha}-${col}`} d={GOTA} transform={`translate(${x} ${y}) scale(0.75)`} fill="#2B5068" />);
    }
  }
  return (
    <svg className="chuva" viewBox="0 0 250 125" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {gotas}
      <g transform="translate(110 30) scale(0.85)">
        <clipPath id="clip-chuva"><path d={METADE_ESQUERDA} /></clipPath>
        <path d={GOTA} fill="#9CC3D5" />
        <path d={GOTA} fill="#F3EDDD" clipPath="url(#clip-chuva)" />
      </g>
    </svg>
  );
}
