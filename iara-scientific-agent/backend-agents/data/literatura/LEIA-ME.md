# Base de literatura científica

Cada arquivo resume **um trabalho científico real**, com DOI (ou link do repositório
institucional, no caso da tese). Os resumos foram escritos com palavras próprias a partir dos
resumos publicados; consulte o trabalho original pelo DOI antes de citá-lo.

As **categorias** indicam os usos que o trabalho testa ou relata, no vocabulário de
`app/services/texto.py` (`CATEGORIAS_USO`). Elas são a base do Score de Consistência Científica.

Limitações:

- É uma base pequena (13 trabalhos, 9 espécies). "Uso não documentado" significa
  **não documentado nesta base**, não "nunca estudado".
- O cumaru (*Dipteryx odorata*) ficou sem trabalho de propósito, para mostrar como o sistema
  trata uma lacuna de literatura.

Para adicionar um trabalho, crie um arquivo `.md` com o mesmo cabeçalho:

```
---
especie: Nome científico
sinonimos: Outro nome (opcional, separados por vírgula)
titulo: Título do trabalho
autores: Autores
fonte: Revista volume(número):páginas
ano: 2024
doi: 10.xxxx/xxxxx
url: https://doi.org/10.xxxx/xxxxx
categorias: anti-inflamatorio, cicatrizante
---
Resumo com suas palavras.
```
