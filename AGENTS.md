# Manu

Assistente que responde dúvidas sobre eletrodomésticos só com o manual oficial do fabricante, citando a página, e diz que não sabe quando o manual não traz a resposta. Projeto de portfólio, construído em fases. `api/` é o pipeline e a API (Python, FastAPI); `web/` é a interface (Next.js).

## Convenções

- Os PDFs dos manuais ficam versionados em `api/data/pdfs/` ([ADR 0006](docs/adr/0006-manuais-versionados-no-repositorio.md)); `api/data/chroma/` e relatórios de avaliação ficam na máquina local, fora do git.
- Texto de produto, comentários e mensagens de commit em português; a mensagem do commit descreve o resultado para quem usa a Manu.
- Cada etapa do RAG é uma peça solta, sem framework de RAG.
- Segredos só em `.env` (modelo em `.env.example`).

## Stack

- **API** (`api/`): Python 3.12+, FastAPI, ChromaDB, Claude (Anthropic SDK); embeddings Ollama `bge-m3` local e Voyage no deploy.
- **Web** (`web/`): Next.js 16, React 19, Tailwind 4, TypeScript, three.js; npm.
- **Deploy**: dois projetos na Vercel, um para a API e outro para a web.

## Build approach

Tracer Bullet: cada fatia atravessa registro, API e interface funcionando, só que estreita, e depois engorda (definido em `docs/scope/scope.md`).

## Comandos

```bash
# API (dentro de api/)
.venv/bin/pip install -e ".[local,dev]"   # instalar
.venv/bin/uvicorn manu.main:app --port 8000   # servidor local
.venv/bin/pytest && .venv/bin/mypy manu   # testes e tipos

# Web (dentro de web/)
npm install && npm run dev   # servidor local
npm run typecheck   # único gate automático
```

Outros comandos da API (`manu-index`, `manu-eval`, `manu-validate`) e o passo a passo completo estão no `README.md`.

## Quando ler cada documento

- `api/`, pipeline, deploy: `.claude/rules/api.md`
- `web/`, interface: `web/AGENTS.md`
- Aparência da interface: `DESIGN.md`
- Escopo, voz ou público do produto: `PRODUCT.md`
- Fase atual e próximas: `docs/roadmap.md`
- Termo do domínio: `CONTEXT.md`
- Decisão de arquitetura já tomada: `docs/adr/`

## Agent skills

### Issue tracker

Issues são arquivos markdown locais em `.scratch/<feature>/` (fora do git). See `docs/agents/issue-tracker.md`.

### Triage labels

Os cinco labels padrão (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: um `CONTEXT.md` + `docs/adr/` na raiz. See `docs/agents/domain.md`.

## Specs e escopo

Specs em `docs/specs/NNNN-titulo.md`; o escopo vivo da fase atual em `docs/scope/scope.md`.

## Context files

- [web/AGENTS.md](web/AGENTS.md) (interface Next.js: verificação, design e regras por área)
