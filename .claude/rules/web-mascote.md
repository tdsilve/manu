---
paths:
  - web/components/manu*.tsx
  - web/components/home-view.tsx
  - web/lib/manu-framing.ts
  - web/lib/use-pointer.ts
---

# Mascote: 3D ou imagens

A escolha depende do **tipo de ponteiro**, não da largura da tela:

- Com cursor (mouse ou trackpad): 3D que segue o mouse (`manu-3d.tsx`).
- Sem cursor (celular, tablet): imagens renderizadas do próprio 3D, com a mesma aparência (`manu-sprite.tsx`). Leves, com olhar próprio e reação ao toque.
- Até o 3D ficar pronto, ou sem WebGL, aparecem as imagens no mesmo lugar.

Regras e motivos:

- A escolha segue o ponteiro (`useFinePointer`), e a largura da tela fica fora dela: um desktop com janela estreita continua com cursor, e o 3D só faz sentido onde há um cursor para seguir.
- 3D e imagens usam o mesmo enquadramento, em `lib/manu-framing.ts`, para coincidirem em lugar e tamanho. Mudou um, confira o outro, senão o mascote "pula" na troca.
- O 3D é carregado com `dynamic(..., { ssr: false })` em `manu.tsx`, porque o Three.js precisa do navegador e pesa no bundle.
- A Manu em imagens só aparece com todas as camadas carregadas (commit `05b384e`), para não mostrar o mascote pela metade.
