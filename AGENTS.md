# Manu

Assistente que responde dúvidas sobre eletrodomésticos só com o manual oficial do fabricante, citando a página, e diz que não sabe quando o manual não traz a resposta. Projeto de portfólio, construído em fases. `api/` é o pipeline e a API (Python, FastAPI); `web/` é a interface (Next.js).

## Convenções

- PDFs, `api/data/chroma/` e relatórios de avaliação ficam na máquina local, fora do git ([ADR 0006](docs/adr/0006-manuais-fora-do-repositorio.md)).
- Texto de produto, comentários e mensagens de commit em português; a mensagem do commit descreve o resultado para quem usa a Manu.
- Cada etapa do RAG é uma peça solta, sem framework de RAG.
- Segredos só em `.env` (modelo em `.env.example`).

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
