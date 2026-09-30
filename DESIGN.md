---
name: Manu
description: O manual que sorri. Respostas do manual oficial, com o trecho grifado e a página.
colors:
  lavender-paper: "#f8f6fc"
  lavender-deep: "#ece7f6"
  stage-top: "#ebe6fa"
  stage-mid: "#ddd4f7"
  stage-bottom: "#c9bcf2"
  aubergine-ink: "#1d1733"
  quiet-ink: "#56516a"
  manual-violet: "#6b57c7"
  paper-white: "#ffffff"
  highlighter: "#f8e38a"
  post-it-gold: "#f3b93a"
  alert-brick: "#9b2c1f"
  cover-cream: "#fbf8f1"
  spine-sand: "#e2d6bf"
  pages-linen: "#efe6d2"
  tab-coral: "#f2a07b"
  tab-pink: "#f59bb5"
  tab-mint: "#9fdcc4"
typography:
  display:
    fontFamily: "Bricolage Grotesque, Geist, sans-serif"
    fontSize: "clamp(40px, 4.6vw, 68px)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "-0.045em"
  headline:
    fontFamily: "Bricolage Grotesque, Geist, sans-serif"
    fontSize: "clamp(40px, 7vw, 72px)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "-0.045em"
  page-number:
    fontFamily: "Bricolage Grotesque, Geist, sans-serif"
    fontSize: "52px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.05em"
  title:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "19px"
    fontWeight: 500
    lineHeight: 1.375
  body:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.5
  excerpt:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.625
  label:
    fontFamily: "Geist, Helvetica Neue, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    letterSpacing: "0.12em"
rounded:
  card: "16px"
  bubble: "22px"
  stage-mobile: "28px"
  stage: "32px"
  pill: "9999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "36px"
  gutter: "clamp(20px, 3.6vw, 48px)"
components:
  button-primary:
    backgroundColor: "{colors.aubergine-ink}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.pill}"
    height: "40px"
    padding: "0 16px"
  button-primary-hover:
    backgroundColor: "#2c2447"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.aubergine-ink}"
    rounded: "{rounded.pill}"
    height: "44px"
  button-outline-hover:
    backgroundColor: "{colors.aubergine-ink}"
    textColor: "{colors.paper-white}"
  button-soft:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.aubergine-ink}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  question-bar:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.aubergine-ink}"
    rounded: "{rounded.pill}"
    height: "56px"
    padding: "6px 6px 6px 20px"
  proof-card:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.aubergine-ink}"
    typography: "{typography.excerpt}"
    rounded: "{rounded.card}"
    padding: "14px 16px"
  chat-bubble-user:
    backgroundColor: "{colors.aubergine-ink}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.bubble}"
    padding: "12px 18px"
  label:
    textColor: "{colors.quiet-ink}"
    typography: "{typography.label}"
---

# Design System: Manu

## Overview

**Creative North Star: "O manual que sorri"**

O Manu transforma o manual de papel, aquele que ninguém lê, num personagem simpático: um manual com abas, de rosto redondo, que olha para você. A graça fica toda no mascote. O resto da interface é calmo e exato, porque o produto é a prova: toda resposta mostra o trecho do manual, grifado, com o número da página em destaque.

A cena é única e clara. O fundo lavanda quase branco não compete com nada, o palco lilás arredondado é a casa do Manu e os cartões de papel branco carregam a evidência. Os títulos são grandes e confiantes; os rótulos, pequenos e discretos. A leitura vai sempre na mesma ordem: pergunta, resposta, página, trecho.

O mascote muda com o aparelho, não com o tamanho da tela. Em aparelhos com cursor (computador, mesmo com a janela estreita) ele é 3D e segue o mouse. Em aparelhos de toque (celular, tablet) ele é feito de imagens renderizadas do próprio 3D: a mesma aparência, leve, com olhar próprio e reação ao toque. As duas versões usam o mesmo enquadramento e aparecem no mesmo lugar.

**Key Characteristics:**
- Um personagem lúdico; todo o resto é sóbrio.
- A prova (grifo amarelo + página) é o centro visual de cada resposta.
- Papel branco sobre lavanda; o lilás só aparece no palco do Manu e no destaque do título.
- Títulos em Bricolage extra-bold; texto em Geist.
- Só tema claro.

## Colors

Lavanda calma de fundo, tinta berinjela para ler, um violeta de destaque e o amarelo de marca-texto como única cor quente da interface.

### Primary
- **Manual Violet** (manual-violet): a segunda linha do slogan ("Direto da fonte.") e o carregamento do chat. É a cor da marca na interface. Pouco usada de propósito.

### Secondary
- **Highlighter** (highlighter): o grifo dos trechos citados e o post-it do mascote. Aparece só onde há evidência do manual.
- **Post-it Gold** (post-it-gold): o ponto da marca "manu." e o post-it. Nunca em texto.

### Neutral
- **Lavender Paper** (lavender-paper): fundo de todas as telas.
- **Lavender Deep** (lavender-deep): fundo por trás de áreas centralizadas.
- **Stage** (stage-top → stage-mid → stage-bottom): gradiente radial do palco do Manu, mais escuro embaixo, como um chão.
- **Aubergine Ink** (aubergine-ink): texto principal, botões primários, bolha da pergunta no chat, traços do mascote.
- **Quiet Ink** (quiet-ink): rótulos, texto secundário, placeholder. Cor sólida com contraste de cerca de 7:1 sobre o fundo.
- **Paper White** (paper-white): cartões de prova, barra de pergunta, botões suaves.
- **Alert Brick** (alert-brick): só no título de erro de conexão.

### Mascot
- **Cover Cream / Spine Sand / Pages Linen** (cover-cream, spine-sand, pages-linen): capa, lombada e miolo do manual.
- **Abas** (tab-coral, post-it-gold, tab-pink, tab-mint): as quatro abas de índice, sempre nessa ordem de cima para baixo.

### Named Rules
**The Solid Label Rule.** Texto secundário usa Quiet Ink sólido, nunca opacidade. Transparência em texto derruba o contraste.

**The Highlighter Is Evidence Rule.** O amarelo de grifo marca só trecho real do manual. Não serve para decorar nem para chamar atenção.

**The No Purple Book Rule.** O mascote é papel: creme, areia e linho. O lilás fica no palco, nunca no manual.

## Typography

**Display Font:** Bricolage Grotesque (com Geist de reserva)
**Body Font:** Geist (com Helvetica Neue e Arial de reserva)

**Character:** Bricolage extra-bold, compacta e um pouco excêntrica, dá voz ao título e ao número da página. Geist é neutra e muito legível para perguntas, respostas e trechos.

### Hierarchy
- **Display** (800, clamp(40px, 4.6vw, 68px), 0.95): título da home em duas linhas, a segunda em Manual Violet. No celular, 30px.
- **Headline** (800, clamp(40px, 7vw, 72px), 0.95): título do chat vazio ("Qual é a sua dúvida?").
- **Page Number** (800, 40–52px, 1): o número da página ao lado de cada trecho, com o rótulo "pág." em cima.
- **Title** (500, 19px, 1.375): a pergunta de exemplo e a resposta curta na home.
- **Body** (400, 17px, 1.5): respostas do chat (19px no desktop), no máximo 62 caracteres por linha.
- **Excerpt** (400, 15px, 1.625): o trecho do manual dentro do cartão de papel.
- **Label** (500, 11px, 0.12em, caixa alta): "Você pergunta", "O Manu responde", "pág.", legenda do manual, contadores.

### Named Rules
**The Page Is Loud Rule.** O número da página é o maior elemento de cada resposta depois do título. Se a página não aparece de relance, a prova falhou.

**The 11px Floor Rule.** Nenhum texto abaixo de 11px.

## Layout

Cada tela cabe inteira, sem rolagem, na home. Margem lateral fluida: clamp(20px, 3.6vw, 48px).

- **Home:** um layout só, centralizado, sobre o palco lilás de tela inteira. No topo, "manu." enorme (Bricolage 800, clamp(88px, 17vw, 208px)) e, logo abaixo, o botão "Converse com a Manu". O Manu ocupa a parte de baixo, com o topo do livro a 44% da altura (enquadramento *giant*). No desktop ele fica cortado na borda de baixo; no celular aparece inteiro. No desktop, o slogan "A Manu responde. Direto da fonte." fica no canto esquerdo e "Como funciona" no direito; no celular o slogan vai para baixo do nome.
- **Chat:** coluna central de até 760px, cabeçalho fixo com degradê para o fundo, barra de pergunta fixa embaixo.
- **Ritmo:** 8, 12, 16, 20, 36px. Blocos de conteúdo separados por 20px; seções maiores por 36px.

## Elevation & Depth

Profundidade suave e quase só por sombra difusa arroxeada. A única sombra "dura" é a do chão sob o mascote.

### Shadow Vocabulary
- **Card** (`0 14px 30px -16px rgb(80 60 160 / 0.4)`): cartões de prova e de recusa. Parece papel descansando sobre a lavanda.
- **Bar** (`0 1px 2px rgb(29 23 51 / 0.08), 0 18px 40px -14px rgb(80 60 160 / 0.45)`): a barra de pergunta, que flutua acima de tudo.
- **Focus** (`0 0 0 2px #1d1733` somado à sombra da barra): foco da barra de pergunta.

### Named Rules
**The Paper Floats Rule.** Só papel tem sombra: cartões e barra. Palco, botões e texto são planos.

## Shapes

Tudo é arredondado e macio, como o mascote. Não há cantos vivos.

- **Pílula** (9999px): botões, barra de pergunta, exemplos em pílula.
- **Cartão** (16px): cartões de prova e de recusa.
- **Bolha** (22px, com o canto inferior direito a 6px): a pergunta da pessoa no chat.
- **Palco** (28px no celular, 32px no desktop): a área lilás do Manu.

## Components

### Buttons
- **Shape:** pílula (9999px).
- **Primary:** Aubergine Ink com texto branco, 40px de altura (44px quando é só ícone). Usado em "Perguntar" e no botão de enviar.
- **Hover / Focus:** o primário escurece levemente; o foco é um contorno de 2px em Aubergine Ink, afastado 3px.
- **Outline:** contorno fino, que fica sólido (Aubergine Ink) no hover. Usado nas setas de exemplo e em "Nova conversa".
- **Soft:** papel semitransparente com linha finíssima. Usado nas perguntas de exemplo do chat.

### Question Bar
- **Style:** pílula branca, 56px de altura, com a sombra Bar. O campo ocupa o espaço e o botão fica à direita.
- **Focus:** contorno de 2px em Aubergine Ink em volta da pílula.
- **Placeholder:** "Qual é a sua dúvida?" em todas as telas.

### Proof (trecho citado)
- **Composição:** o número da página (Page Number, com o rótulo "pág." em cima) à esquerda e um cartão de papel à direita.
- **Cartão:** Paper White, 16px de raio, sombra Card, trecho em Excerpt com grifo Highlighter e a legenda do manual em Label.
- **Na home:** o trecho inteiro é grifado. **No chat:** só os termos da pergunta.

### Honesty Line
Ícone de check + "Não está no manual? O Manu diz que não sabe." em Quiet Ink, 13px. Aparece perto da prova, na home e no chat vazio.

### Chat Turn
- **Pergunta:** bolha em Aubergine Ink, alinhada à direita.
- **Resposta:** mini-Manu (ícone de 32px), o rótulo "O Manu responde", o texto e as provas.
- **Recusa:** cartão de papel com "Isso não está no manual." em Bricolage bold.
- **Erro:** título em Alert Brick e botão "Tentar de novo".

### Manu (mascote)
- **Forma:** manual com abas visto de frente, na proporção de cerca de 0,8 de largura para 1 de altura. Capa creme sem título; só um ícone de geladeira no rodapé e o post-it "pág. 5". Lombada areia, quatro abas (coral, mostarda, rosa, menta), braços finos em Aubergine Ink com luvas brancas, olhos grandes com brilho, bochechas rosadas.
- **Quem decide é o aparelho:** com cursor (`hover: hover` e `pointer: fine`), 3D; sem cursor, imagens. A largura só decide o layout. Tudo passa pelo componente `Manu`, e o enquadramento das duas versões vem de uma conta só (`lib/manu-framing.ts`).
- **3D (aparelhos com cursor):** feito em Three.js. Segue o cursor, pisca, respira, pula a cada exemplo e levanta os braços quando a pessoa digita. Pausa fora da tela. Até o 3D carregar, ou se não houver WebGL, aparecem as imagens no mesmo lugar, então a troca não se nota. Tem dois enquadramentos: *hero* (grande e cortado embaixo, no palco do desktop) e *compact* (inteiro, em palcos pequenos).
- **Imagens (aparelhos de toque):** 7 camadas WebP renderizadas do 3D em pose neutra (`public/manu`, cerca de 40 KB no total): braços, corpo, brancos dos olhos, pupilas, sobrancelhas e boca, animadas com CSS. Sem WebGL e sem baixar o three.js. Olhar próprio, reage ao toque, ao deslize e ao foco no campo. **Se o modelo 3D mudar, as camadas precisam ser exportadas de novo.**
- **Movimento:** desacelerações suaves (cubic-bezier(0.16, 1, 0.3, 1)), sem efeito de mola. Com "reduzir movimento" ativo, fica parado.

## Do's and Don'ts

### Do:
- **Do** mostrar a página e o trecho grifado em toda resposta com fonte.
- **Do** usar Quiet Ink sólido para texto secundário, com 11px ou mais.
- **Do** manter o mascote em tons de papel e a mesma ordem de abas em todas as versões.
- **Do** fazer cada tela da home caber sem rolagem.
- **Do** usar pílula para tudo o que se clica.

### Don't:
- **Don't** colocar título ou texto na capa do mascote.
- **Don't** usar roxo ou lilás no corpo do mascote.
- **Don't** usar o amarelo de grifo fora de trechos reais do manual.
- **Don't** usar opacidade para clarear texto.
- **Don't** usar animações de mola ou elásticas.
- **Don't** mostrar logotipos de fabricantes; marcas aparecem só como texto.
- **Don't** carregar o 3D em aparelhos de toque, nem escolher o mascote pela largura da tela.
