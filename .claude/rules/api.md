---
paths:
  - api/**
---

# API e pipeline

Comandos: os scripts de `[project.scripts]` em `api/pyproject.toml` (`manu-index`, `manu-eval`, `manu-validate`) e o README. Dentro de `api/`, `.venv/bin/pytest` e `.venv/bin/mypy manu` passam limpos; mypy roda em modo strict e não há lint.

## Duas barreiras contra alucinação

1. Limiar de similaridade antes do LLM: abaixo dele a API recusa sem chamar o Claude.
2. O Claude recebe a instrução de recusar quando os trechos não bastam.

A resposta é saída estruturada (`answer`, `refused`, `used_chunk_ids`), então nada depende de interpretar texto livre.

## Limiar e embeddings

O `SIMILARITY_THRESHOLD` vale para um modelo de embeddings só. Ao trocar `EMBEDDING_PROVIDER` ou `EMBEDDING_MODEL`: apague `data/chroma/` (ou use outra database no Chroma Cloud), rode `manu-index` e recalibre o limiar com `manu-eval`. Ollama `bge-m3` é o local; Voyage `voyage-3.5` com Chroma Cloud é o do deploy ([ADR 0008](../docs/adr/0008-embeddings-e-base-hospedados-no-deploy.md)).

## Dependências

O deploy na Vercel instala só `dependencies` e tem limite de 500 MB por função. Pacote usado em produção entra em `dependencies`; extração de PDF e servidor local ficam no extra `local`.

## Testes

Os testes rodam sem rede, sem Ollama e sem chave do Claude: mantenha esse isolamento em teste novo, com fixtures em `api/tests/fixtures/`.

## Produto selecionado

`GET /products/{código}` acha o manual pelo código (sem caixa, espaço nem hífen), `POST /products/detect` acha no texto da pergunta os códigos do registro (tokens de `[A-Za-z0-9]`, janelas de até 3 tokens, comparação exata; devolve `matches`, `unrecognized` e `only_codes`) e `POST /ask` aceita `manual_id` e `model_code` opcionais; com `manual_id`, a busca filtra só aquele manual. O registro `data/manuals.yaml` vai para a função da Vercel (o `vercel.json` só exclui `data/{pdfs,chroma,extracted}`) e a API não sobe sem ele. `manu-validate` falha com código repetido depois de normalizado.
