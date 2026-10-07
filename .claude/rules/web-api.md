---
paths:
  - web/lib/ask.ts
  - web/components/chat*.tsx
---

# Como a web fala com a API

`web/lib/ask.ts` faz `POST {API_URL}/ask` com `{ question }` e devolve `AskResponse`:

- `answer`: texto da resposta.
- `refused`: `true` quando os manuais não trazem a resposta. A Manu diz que não sabe; a interface não deve tratar isso como erro.
- `citations`: lista com `manual_id`, `brand`, `model`, `page`, `excerpt` e `similarity`. Toda resposta mostra trecho, manual e página.

`API_URL` vem de `NEXT_PUBLIC_API_URL` (padrão `http://localhost:8000`). O modelo está em `web/.env.example`; o valor real fica em `web/.env.local`.

O formato da resposta é definido pela API em `api/`. Ao mudar um lado, mude o outro, porque não há contrato compartilhado: os tipos de `ask.ts` são escritos à mão.
