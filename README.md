# Manu

Assistente que responde dúvidas sobre eletrodomésticos com base no manual oficial do fabricante, citando a página. Projeto de portfólio construído em fases ([roadmap](docs/roadmap.md)).

## Fase 1: RAG básico

Perguntas em linguagem do dia a dia sobre geladeiras e micro-ondas Electrolux e Brastemp, respondidas só com o conteúdo dos manuais. Toda resposta mostra o trecho, o manual e a página. Quando os manuais não trazem a resposta, a Manu diz que não sabe.

Fora desta fase: identificação do produto pela foto da etiqueta (fases 2 e 3), filtro por modelo, OCR, memória de conversa. Detalhes no [spec](docs/fases/fase-1/spec.md).

### Arquitetura

Sem framework de RAG: cada etapa é uma peça solta.

```
PDF ──pdfplumber──> texto por página ──Ollama (embeddings)──> ChromaDB
                                                                 │
pergunta ──Ollama──> top-k páginas ──limiar──┬── abaixo: recusa (sem chamar o LLM)
                                             └── acima: Claude (saída estruturada) ──> resposta + citações
```

- `api/`: pipeline e API em Python (FastAPI).
- `web/`: interface em Next.js.

## Como rodar

### Pré-requisitos

- Python 3.12+
- Node 20+
- [Ollama](https://ollama.com) rodando localmente, com o modelo de embeddings:

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

Os PDFs não ficam no repositório ([ADR 0006](docs/adr/0006-manuais-fora-do-repositorio.md)). Baixe cada manual pelo `source_url` listado em [`api/data/manuals.yaml`](api/data/manuals.yaml) e salve em `api/data/pdfs/` com o nome do campo `file`. Depois confira:

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

- **Embeddings:** `bge-m3` via Ollama. É multilíngue (manuais e perguntas estão em português), roda local e sem custo por chamada.
- **Geração:** Claude com saída estruturada (`answer`, `refused`, `used_chunk_ids`). A resposta nunca depende de interpretar texto livre.
- **Duas barreiras contra alucinação:** limiar de similaridade antes do LLM e instrução para recusar quando os trechos não bastam.
- **Limiar de similaridade:** _pendente de calibração com o gabarito (valor provisório 0,5)._

## Resultados

_Pendente: preenchido após a calibração do limiar com o gabarito final._

| Métrica | Valor |
|---|---|
| Acerto de busca (top-3) | — |
| Recusa correta | — |
| Recusa indevida | — |
| Respostas julgadas corretas | — |
