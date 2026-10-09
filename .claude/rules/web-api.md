---
paths:
  - web/lib/ask.ts
  - web/components/chat*.tsx
---

# Como a web fala com a API

`web/lib/ask.ts` faz `POST /api/ask` com `{ question }` (mais `manual_id` e `model_code` quando há produto selecionado) e devolve `AskResponse`. Essa rota (`web/app/api/ask/route.ts`) roda no servidor e repassa o pedido à API, para o navegador nunca ver o endereço da API nem o segredo de bypass da proteção de deploy da Vercel. `AskResponse`:

- `answer`: texto da resposta.
- `refused`: `true` quando os manuais não trazem a resposta. A Manu diz que não sabe; a interface não deve tratar isso como erro.
- `citations`: lista com `manual_id`, `brand`, `model`, `page`, `excerpt` e `similarity`. Toda resposta mostra trecho, manual e página.

`web/lib/products.ts` acha o modelo no texto de cada pergunta em `POST /api/products/detect` (rota de servidor que repassa à API; qualquer falha vira "nada achado" e a pergunta segue). `GET /api/products/[code]` também repassa à API, mas o chat não o usa. `lib/detection-flow.ts` decide o que o chat faz com o resultado. Cada rota repassa o IP de quem chamou em `x-manu-client-ip` (o limite de chamadas da API vale por pessoa) e lê `MANU_API_URL` (padrão `http://localhost:8000`) e, em produção, `API_BYPASS_SECRET`, que vai no cabeçalho `x-vercel-protection-bypass`. As duas são só do servidor, sem prefixo `NEXT_PUBLIC_`. O modelo está em `web/.env.example`; os valores reais ficam em `web/.env.local` e nas variáveis da Vercel.

O formato da resposta é definido pela API em `api/`. Ao mudar um lado, mude o outro, porque não há contrato compartilhado: os tipos de `ask.ts` são escritos à mão.
