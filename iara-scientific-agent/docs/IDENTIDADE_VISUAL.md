# Identidade visual: Folha-gota

<img src="img/logo.svg" alt="Logo do Iara" width="220">

A folha-gota é folha e água num gesto só. A nervura divide a forma em duas metades:
**verde-copaíba**, o saber da planta, e **Rio Negro**, a mãe-d'água. Ela é o pingo do "i" de
*iara*, o ícone do app, o pino de cada registro no mapa e o sinal dos momentos-chave, como
salvar e sincronizar.

## Regras do logo

- A nervura sempre separa verde à esquerda e azul à direita.
- Área de respiro = metade da largura da gota.
- Não girar (exceto no pino do mapa, sempre a 180°), não contornar, não aplicar sobre foto sem fundo sólido.
- Tamanho mínimo: 16 px de altura na tela.
- Versão negativa (sobre verde ou Rio Negro): palha à esquerda, água clara à direita.

## Paleta

| Cor | Hex | Uso | Contraste sobre palha |
|---|---|---|---|
| Verde-copaíba | `#1F4A33` | Principal, metade folha, validado | 8,6:1 |
| Rio Negro | `#1D3B4F` | Metade água, mapa, revisão | 10,0:1 |
| Roxo-açaí | `#5A2A50` | Achado inédito | 9,5:1 |
| Urucum | `#A3401F` | Alertas | 5,4:1 |
| Palha | `#F3EDDD` | Fundo | — |
| Jenipapo | `#1B1E1A` | Texto | 14,4:1 |

Apoio: papel `#FBF8F0` · água clara `#9CC3D5` (sobre escuros) · texto secundário `#3D4A41` · borda `#D6CCB4`.

## Tipografia

| Fonte | Uso |
|---|---|
| **Young Serif** | Títulos e assinatura. Robusta, calorosa, firme no sol |
| ***EB Garamond* itálico** | Só nomes científicos, como manda a convenção botânica |
| **Work Sans** | Interface e dados. Mínimo 13 px no painel, 15 px no app |

As três fontes têm licença SIL Open Font License e vão embutidas no painel
(`@fontsource`) e no app (`res/font/`), então funcionam sem internet.

## Status

O pino tem sempre a mesma forma; o que muda é o ícone dentro, com a palavra ao lado sempre
que há espaço. Em tons de cinza, ou para quem não distingue cores, o status continua legível.

| Status | Cor | Ícone | Significado |
|---|---|---|---|
| Validado | verde-copaíba | ✓ | Coerente nos 3 pareceres |
| Achado inédito | roxo-açaí | flor | Uso sem paralelo na literatura |
| Alerta geográfico | urucum | ! | Fora da área esperada |
| Revisão taxonômica | Rio Negro | lupa | Nome ou sinonímia a conferir |

## Onde está no código

| Peça | Painel web | App Android |
|---|---|---|
| Cores | `web-curator-panel/src/styles.css` (`:root`) | `ui/Tema.kt` (`Cores`) |
| Fontes | `src/main.tsx` | `res/font/` + `ui/Tema.kt` |
| Logo, pinos, ícones | `src/components/Marca.tsx` | `res/drawable/ic_launcher.xml`, `gota_negativa.xml` |
| Cards de parecer (nota de herbário) | `src/components/Drawer.tsx` | — |
