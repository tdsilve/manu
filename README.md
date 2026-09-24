# Manu

Assistente que responde dúvidas sobre eletrodomésticos com base no manual oficial do fabricante, citando a página. Projeto de portfólio construído em fases ([roadmap](docs/roadmap.md)).

## Fase 1: RAG básico

Perguntas em linguagem do dia a dia sobre geladeiras e micro-ondas Electrolux e Brastemp, respondidas só com o conteúdo dos manuais. Toda resposta mostra o trecho, o manual e a página. Quando os manuais não trazem a resposta, o Manu diz que não sabe.

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
.venv/bin/pip install -e ".[dev]"
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
