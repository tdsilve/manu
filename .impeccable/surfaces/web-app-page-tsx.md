---
version: 2
slug: "web-app-page-tsx"
primary_target: "web/app/page.tsx"
related_targets: ["web/app/chat/page.tsx","web/components/chat.tsx","web/components/home-desktop.tsx","web/components/home-mobile.tsx"]
---

# Surface brief: Manu (home + chat)

Scope: web/app/page.tsx (home, Persuade) and web/app/chat (chat, Operate). Only these two routes exist. Visual system: DESIGN.md.

Audience: dono de geladeira com uma dúvida no meio do uso; o portfólio é avaliado pelo produto funcionando. Action: perguntar (barra da home ou "Perguntar isso no chat"). Proof: exemplos reais do manual Electrolux G0045837 (págs. 4 e 5), com trecho verbatim, grifo e página. Constraints: só o que existe (Fase 1: um manual de geladeira); sem logos de fabricantes; sem números inventados.

## Direction contract

THESIS: O manual que sorri. A Manu é um manual com abas que ganhou rosto; a prova (trecho grifado + número da página) é sempre o centro da tela.

WORLD: Fundo lavanda quase branco; palco lilás arredondado onde vive a Manu; tinta berinjela; títulos em Bricolage Grotesque extra-bold com a segunda linha em roxo; cartões de papel branco com grifo amarelo; rótulos em caixa alta, cor sólida. Ver DESIGN.md.

STORY: A Manu em evidência: a pessoa vê a personagem, o nome e um único convite para conversar.

HOME (referência da autora: página de personagem com o mascote gigante e texto só nos cantos): palco lilás de tela inteira; "manu." enorme e centralizado no topo; botão "Converse com a Manu" centralizado logo abaixo; a Manu gigante ocupando a parte de baixo (enquadramento giant), cortado na borda no desktop. Cantos no desktop: "A Manu responde. / Direto da fonte." à esquerda, "Como funciona" à direita. Os exemplos com trecho e página ficam no chat.

MOBILE (<768px): o mesmo layout; o slogan vai para baixo do nome e a Manu aparece inteira.

MASCOTE POR APARELHO: a largura escolhe o layout; o aparelho escolhe a Manu. Com cursor (mesmo em janela estreita) é o 3D; em aparelho de toque são as imagens renderizadas do próprio 3D (mesma aparência), e o three.js não é baixado.

CHAT: mesmo mundo. Estado vazio com a Manu no palco, "Qual é a sua dúvida?", exemplos em pílulas e a promessa do "não sei". Resposta: rótulo "A Manu responde", texto, e cada fonte como número da página grande + cartão de papel com os termos da pergunta grifados. Recusa em cartão próprio ("Isso não está no manual.").

Signature interaction: com cursor, a Manu 3D segue o mouse com os olhos e o corpo, pisca, respira e pula a cada exemplo; levanta os braços quando a pessoa digita. No toque, a Manu em imagens tem olhar próprio (passeia, olha onde o dedo toca, acompanha o cartão deslizado, olha para o campo), pula a cada exemplo e se alegra quando é tocado.
