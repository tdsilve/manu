# Manu

Assistente que responde dúvidas sobre eletrodomésticos com base no manual oficial do fabricante, citando a página. Projeto de portfólio construído em fases ([roadmap](docs/roadmap.md)).

## Fase 1: RAG básico

Perguntas em linguagem do dia a dia sobre geladeiras e micro-ondas Electrolux e Brastemp, respondidas só com o conteúdo dos manuais. Toda resposta mostra o trecho, o manual e a página. Quando os manuais não trazem a resposta, a Manu diz que não sabe.

### O que a Fase 1 entrega

- **Base de manuais:** 17 manuais oficiais (8 de geladeira e 9 de micro-ondas, Electrolux e Brastemp), com 346 páginas indexadas. O [registro](api/data/manuals.yaml) guarda marca, códigos de modelo, categoria, link de origem e arquivo de cada um.
- **Extração de texto por página:** lê páginas em duas colunas, descarta páginas sem texto útil, respeita a área visível do PDF (CropBox) e recorta as folhas de impressão em painéis, numerando cada um pelo número impresso, para a citação bater com o manual.
- **Indexação:** uma página vira um trecho, com identificador `manual + página`, então reindexar substitui em vez de duplicar. Os metadados (marca, modelo, categoria, página) alimentam as citações. Embeddings `bge-m3` (Ollama, local) ou `voyage-3.5` (deploy), e base no ChromaDB em disco ou no Chroma Cloud, escolhidos por variável de ambiente.
- **Busca e recusa:** as 5 páginas mais parecidas com a pergunta, com similaridade. Se a melhor ficar abaixo do limiar (0,5), a Manu recusa sem chamar o Claude.
- **Resposta:** o Claude responde só com os trechos recuperados, em português e em saída estruturada, e a citação traz só as páginas que ele usou. Se os trechos não bastam, ele recusa.
- **API (FastAPI):** `POST /ask` devolve resposta, se foi recusa e as citações (marca, modelo, página, trecho, similaridade). Pergunta vazia ou com mais de 1000 caracteres retorna 422. Falha do embedder ou do Claude retorna erro 5xx, nunca uma recusa disfarçada. `GET /health` confere se está no ar.
- **Interface (Next.js):** o chat é a página inicial, com exemplos de pergunta. Cada resposta mostra as fontes (trecho destacado, manual, página e similaridade). Resposta, recusa e erro aparecem de formas distintas. A interface fala com a API pelo servidor, então o navegador não vê o endereço dela.
- **Avaliação:** um gabarito de 34 perguntas (29 com resposta e 5 sem), em que cada item traz uma evidência conferida automaticamente com o texto dos PDFs (`manu-eval --check`). O `manu-eval` roda tudo pelo pipeline real e gera um relatório com as métricas, a distribuição das similaridades e o espaço para julgar cada resposta.
- **Testes:** 21 testes automáticos, sem rede, sem Ollama e sem chave do Claude, com fixtures próprias.
- **Deploy:** API e interface em dois projetos na Vercel, com embeddings da Voyage e base no Chroma Cloud. Veja [Deploy](#deploy-vercel).

Fora desta fase: identificação do produto pela foto da etiqueta (fases 2 e 3), filtro por modelo, OCR, memória de conversa. Detalhes no [spec](docs/fases/fase-1/spec.md).

### Arquitetura

Sem framework de RAG: cada etapa é uma peça solta.

```
PDF ──pdfplumber──> texto por página ──embeddings──> ChromaDB
                                                        │
pergunta ──embeddings──> top-k páginas ──limiar──┬── abaixo: recusa (sem chamar o LLM)
                                                 └── acima: Claude (saída estruturada) ──> resposta + citações
```

Embeddings: `bge-m3` via Ollama no desenvolvimento local e `voyage-3.5` (Voyage AI) no deploy. Veja [Decisões](#decisões).

- `api/`: pipeline e API em Python (FastAPI).
- `web/`: interface em Next.js.

## Como rodar

### Pré-requisitos

- Python 3.12+
- Node 20+
- Para embeddings locais, o [Ollama](https://ollama.com) rodando, com o modelo (dispensável se você usar a Voyage, como no deploy):

```bash
ollama pull bge-m3
```

- Uma chave da API do Claude.

### 1. API

```bash
cd api
python -m venv .venv
.venv/bin/pip install -e ".[local,dev]"
cp .env.example .env
```

Preencha `ANTHROPIC_API_KEY` no `.env`.

### 2. Manuais

Os PDFs dos 17 manuais vêm junto com o repositório, em `api/data/pdfs/` ([ADR 0006](docs/adr/0006-manuais-fora-do-repositorio.md)). Eles pertencem aos fabricantes; o [`api/data/manuals.yaml`](api/data/manuals.yaml) guarda o `source_url` de cada um, para baixar de novo ou conferir a origem. Alguns PDFs são folhas de impressão, com vários painéis por folha: o campo `grid` do registro diz como recortar, e a página citada é o número impresso no painel. Confira o registro:

```bash
.venv/bin/manu-validate
```

### 3. Indexar

```bash
.venv/bin/manu-index
```

Reindexar substitui os dados anteriores. Se trocar `EMBEDDING_MODEL`, apague `data/chroma/` antes.

### 4. Subir a API

```bash
.venv/bin/uvicorn manu.main:app --port 8000
```

### 5. Subir a interface

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

Abra http://localhost:3000.

## Deploy (Vercel)

Interface e API viram dois projetos na Vercel, ligados ao mesmo repositório. O Ollama não roda na Vercel e a base vetorial não vai para o git ([ADR 0006](docs/adr/0006-manuais-fora-do-repositorio.md)). Por isso, em produção, os embeddings vêm da [Voyage AI](https://www.voyageai.com) e a base fica no [Chroma Cloud](https://www.trychroma.com).

### 1. Indexar na nuvem (uma vez, da sua máquina)

Crie uma database no Chroma Cloud e uma chave na Voyage. Em `api/.env`, preencha:

```
EMBEDDING_PROVIDER=voyage
EMBEDDING_MODEL=
VOYAGE_API_KEY=...
CHROMA_API_KEY=...
CHROMA_TENANT=...
CHROMA_DATABASE=...
```

Rode `.venv/bin/manu-index`. Para voltar ao modo local, apague essas linhas (ou volte `EMBEDDING_PROVIDER=ollama` e esvazie `CHROMA_API_KEY`).

Os limiares de similaridade mudam de um modelo de embeddings para outro: recalibre `SIMILARITY_THRESHOLD` com `manu-eval` usando essa mesma configuração.

### 2. Projeto da API

Na Vercel: **Add New → Project**, importe o repositório e defina **Root Directory = `api`**. A Vercel detecta o FastAPI e usa `manu.main:app` (`[tool.vercel]` no `pyproject.toml`). Variáveis de ambiente:

`EMBEDDING_PROVIDER=voyage`, `VOYAGE_API_KEY`, `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`, `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, `SIMILARITY_THRESHOLD` e `CORS_ORIGIN` (URL da interface; preencha depois do passo 3).

Confira em `https://<api>.vercel.app/health`.

### 3. Projeto da interface

Importe o mesmo repositório de novo, agora com **Root Directory = `web`**. Variável: `NEXT_PUBLIC_API_URL=https://<api>.vercel.app`. Depois do deploy, coloque a URL da interface em `CORS_ORIGIN` no projeto da API e faça um redeploy.

A cada push no `main`, os dois projetos são publicados de novo.

### Testes

```bash
cd api
.venv/bin/pytest
```

Os testes não usam rede, Ollama nem a chave do Claude.

### Avaliação

Com a base indexada e o gabarito preenchido em [`api/eval/gabarito.yaml`](api/eval/gabarito.yaml):

```bash
cd api
.venv/bin/manu-eval
```

O relatório é salvo em `api/eval/reports/`.

## Decisões

- **Embeddings:** dois modelos multilíngues (manuais e perguntas estão em português). O `bge-m3` via Ollama roda local e sem custo por chamada. O deploy usa o `voyage-3.5`, porque a Vercel não roda o Ollama ([ADR 0008](docs/adr/0008-embeddings-e-base-hospedados-no-deploy.md)). A avaliação abaixo usa a configuração do deploy. Uma rodada anterior com o `bge-m3` (25 perguntas, top-3, 9 manuais) deu 75% de acerto de busca, mas não é comparável com a atual: o gabarito e o top-k mudaram. O limiar vale para um modelo só, então trocar de modelo exige recalibrar.
- **Geração:** Claude com saída estruturada (`answer`, `refused`, `used_chunk_ids`). A resposta nunca depende de interpretar texto livre.
- **Duas barreiras contra alucinação:** limiar de similaridade antes do LLM e instrução para recusar quando os trechos não bastam.
- **top-k = 5:** com 3, o acerto de busca cai de 83% para 72% na mesma rodada.
- **Limiar de similaridade = 0,5:** veja [Resultados](#resultados). Subir o limiar recusa mais perguntas com resposta sem pegar muito mais perguntas sem resposta.

## Resultados

Rodada de 07/10/2026: 34 perguntas (29 com resposta nos manuais e 5 sem), 17 manuais, `voyage-3.5`, `claude-sonnet-5`, top-k 5, limiar 0,5. O relatório com cada resposta fica em `api/eval/reports/` (fora do git).

| Métrica | Valor | O que mede |
|---|---|---|
| Acerto de busca (top-5) | 83% (24/29) | a página esperada está entre as 5 recuperadas |
| Recusa correta | 80% (4/5) | perguntas sem resposta que foram recusadas |
| Recusa indevida | 14% (4/29) | perguntas com resposta que foram recusadas |
| Respostas julgadas corretas | _pendente_ | julgamento manual das 34 respostas |

### Por que o limiar é 0,5

A melhor similaridade das perguntas com resposta vai de 0,52 a 0,79; a das sem resposta, de 0,44 a 0,65. As faixas se sobrepõem, então nenhum valor separa os dois grupos. Simulando só o limiar, sem o Claude:

| Limiar | Sem resposta recusadas | Com resposta recusadas |
|---|---|---|
| 0,5 | 20% (1/5) | 0% (0/29) |
| 0,6 | 20% (1/5) | 14% (4/29) |
| 0,7 | 100% (5/5) | 72% (21/29) |

Em 0,6 o limiar já recusa perguntas com resposta sem pegar mais nenhuma sem resposta; em 0,7 pega todas, mas recusa quase três quartos das perguntas que os manuais respondem. Por isso o limiar fica baixo e a recusa depende sobretudo da segunda barreira: das 4 perguntas sem resposta recusadas, 3 foram recusadas pelo Claude e só 1 pelo limiar.

### O que não funcionou

- **Duas falhas de busca (q01, q06):** a página que responde ficou fora das 5 recuperadas. Na q01, três páginas quase idênticas dos manuais Brastemp ocuparam o topo.
- **Duas recusas indevidas com a página certa recuperada (q28, q32):** o Claude recusou mesmo com a página no contexto. Ainda a investigar.
- **Uma pergunta sem resposta que foi respondida (q19):** o Claude respondeu com o consumo em kWh, que o manual traz, e explicou que o valor em reais depende da tarifa. A resposta é boa; a pergunta é que não era totalmente sem resposta.

### Próximos passos

- **Fase 2:** identificar o modelo do produto e buscar só no manual dele. Evita a mistura entre manuais quase idênticos, como no q01.
- **Fase 6:** trechos menores que uma página, busca por palavra-chave junto com os embeddings (termos como "LOC" escapam da busca por significado) e reranking.
- **Avaliação:** gabarito maior e julgamento das respostas com ajuda de um LLM.
