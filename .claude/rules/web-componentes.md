---
paths:
  - web/components/**
  - web/lib/**
---

# Componentes cujo papel o nome não conta

- `chat.tsx`: a única página (`/`): estado do chat (carregando, erro, pronto), a tela inicial com o mascote e os exemplos, e a lista de respostas. `chat-message.tsx` desenha uma pergunta com sua resposta e as citações.
- `honesty.tsx`: o aviso de que, fora do manual, a Manu diz que não sabe.
- `manu.tsx` escolhe o mascote; `manu-3d.tsx` e `manu-sprite.tsx` são as duas versões (regras em `web-mascote.md`).
- `lib/manu-framing.ts`: enquadramento do mascote (`hero`, `compact`), compartilhado pelas duas versões.
- `lib/use-pointer.ts`: `useFinePointer` diz se o aparelho tem cursor.
- `lib/examples.ts`: exemplos reais de pergunta e resposta, copiados do manual.
