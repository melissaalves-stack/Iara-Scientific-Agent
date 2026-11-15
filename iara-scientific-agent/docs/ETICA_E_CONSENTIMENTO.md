# Ética, consentimento e dados de conhecimento tradicional

O Iara lida com **conhecimento tradicional associado à biodiversidade**: saberes que pertencem
a povos indígenas, comunidades tradicionais e agricultores tradicionais. Por isso, as regras de
consentimento não ficam só neste documento; elas estão **implementadas no código**.

> Este documento descreve decisões de projeto. Não é parecer jurídico. Antes de qualquer uso
> real, o protocolo de pesquisa deve passar pelo comitê de ética da instituição e pela
> assessoria responsável pelo SisGen.

## Marco legal considerado

| Norma | O que importa para o sistema |
|---|---|
| **Lei nº 13.123/2015** (Lei da Biodiversidade) e **Decreto nº 8.772/2016** | Regulam o acesso ao conhecimento tradicional associado. Exigem **consentimento prévio informado** da comunidade e **cadastro da atividade no SisGen** antes de divulgar resultados. A lei também alcança conhecimento obtido de fontes secundárias, como publicações e cadastros. Um banco como este, portanto, também é uma forma de sistematização. |
| **Protocolo de Nagoia** | Ratificado pelo Brasil em 2021 e promulgado pelo Decreto nº 11.865/2023. Trata de acesso e repartição justa de benefícios. |
| **LGPD (Lei nº 13.709/2018)** | Nomes de pessoas e comunidades são dados pessoais ou sensíveis e exigem finalidade clara e minimização. |
| **Princípios CARE** (governança de dados indígenas) | Benefício coletivo, autoridade para controlar, responsabilidade e ética. O Iara aplica principalmente a "autoridade para controlar" (revogação). |

## Como o código aplica isso

### 1. Consentimento com escopo, registrado no momento da coleta
O agente de campo do app Android **só fecha um registro depois de perguntar explicitamente**
sobre o consentimento. Ele não assume "sim" por padrão. Os escopos são:

| Escopo | Significado | Efeito na exportação Darwin Core |
|---|---|---|
| `uso_interno` | Só para a equipe de pesquisa | **Não exporta** |
| `publicacao_sem_conhecimento` | Pode publicar que a planta ocorre ali, mas não o uso | Exporta a ocorrência; o saber tradicional é retido (`informationWithheld`) |
| `publicacao_completa` | Comunidade autorizou publicar tudo | Exporta também o uso, em `dynamicProperties` |
| `revogado` | Comunidade retirou a autorização | **Não exporta**, e o conhecimento é apagado |

Arquivos: `android-field-copilot/.../agent/EdgeAgentEngine.kt` (pergunta obrigatória),
`backend-agents/app/services/darwin_core.py` (regras de exportação).

### 2. Revogação de verdade
`POST /api/v1/registros/{id}/revogar-consentimento` apaga o modo de preparo, a indicação, o
relato e a conversa. Um reenvio antigo do celular **não consegue desfazer** a revogação (há
teste automatizado para isso: `test_aprovar_e_revogar`).

### 3. Localização protegida
Toda exportação arredonda as coordenadas para 0,01° (cerca de 1 km) e registra isso em
`dataGeneralizations`. A localização exata de territórios e de plantas de valor econômico pode
expor comunidades à biopirataria e a invasões.

### 4. O modelo de IA nunca decide o consentimento
O agente de campo aceita um LLM local opcional, mas ele é **impedido** de preencher o campo de
consentimento: essa resposta precisa vir explicitamente da conversa com a comunidade.

### 5. "Achado inédito" não é descoberta
Quando o uso relatado não aparece na literatura, o sistema sinaliza o registro para
**prioridade de revisão humana**. Ele não afirma eficácia nem descoberta científica. Um uso
"não documentado" pode ser só uma lacuna da base de literatura.

## O que ainda não está no MVP (e deveria estar num sistema real)

- Registro do **documento** de consentimento (termo assinado, áudio ou vídeo, conforme os usos e
  costumes da comunidade), e não só o escopo.
- Número de cadastro no **SisGen** vinculado à expedição, bloqueando a exportação sem ele.
- Painel para a **própria comunidade** consultar e gerir seus registros.
- Criptografia do banco local no celular (ex.: SQLCipher), caso o aparelho seja perdido em campo.
- Controle de acesso por papel (pesquisador, curador, representante da comunidade).
