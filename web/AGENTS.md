<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Manu web

Interface da Manu: uma só tela, o chat, que mostra o mascote e devolve a resposta com o trecho, o manual e a página. Todo texto de interface é em português.

## Verificação

Sem `lint`, os gates automáticos são `npm run typecheck` e `npm test` (Vitest, em `lib/` e `components/`): rode os dois antes de concluir. Em mudança visual, suba o dev server (`../.claude/launch.json`) e confira o chat (`/`), com e sem cursor, porque cada caso mostra um mascote diferente.

## Design

Leia `../DESIGN.md` antes de mexer em cores, tipografia, layout ou espaçamento. Cores e fontes saem dos tokens em `app/globals.css` e `lib/fonts.ts`. O site tem só tema claro.

## Código

- `"use client"` só onde há estado, efeito ou API do navegador (`chat`, `manu*`); o resto é componente de servidor.
- Componentes do shadcn entram pela CLI, em `components/ui`.
- Toda animação respeita `prefers-reduced-motion`.

## Regras por área

Mascote, chamada à API e mapa de componentes ficam em `../.claude/rules/web-*.md`. O Claude Code as carrega ao tocar nos arquivos de cada área; outros agentes leem antes de mexer nelas.
