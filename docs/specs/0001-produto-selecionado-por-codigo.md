# 0001. Produto selecionado por código exato

**Date**: 2026-10-08
**Status**: Accepted
**Updated**: 2026-10-08 (AC-8: a Manu acha o modelo no texto da pergunta, sem o botão "Procurar código"; cross check aplicado)

## Summary

A pessoa só pergunta, e a Manu identifica o modelo sozinha: a API procura no texto da pergunta os códigos que estão no registro (comparação exata). Achou um aparelho, ele vira o produto selecionado (o chip com "Tirar aparelho") e a resposta sai só do manual dele; não achou nenhum, a pergunta segue como na Fase 1; achou vários aparelhos de manuais diferentes, a Manu pergunta qual é o da pessoa antes de responder. O navegador guarda a escolha e a manda junto com cada pergunta, com o código achado como dica para a resposta. Não existe campo, modo ou botão de código. Esta é a fatia mais fina da Fase 2: só código exato, sem prefixo (fatia 2) e sem registrar o que não tem manual (fatia 3).

## Context

A Fase 1 busca em todos os 17 manuais. Quando a pergunta não diz o modelo, a Manu pergunta qual é e o trecho certo pode competir com trechos de outros aparelhos. A Fase 2 troca isso por uma escolha explícita: a pessoa diz o aparelho e as respostas saem só do manual dele.

Forças que moldam o desenho:
- A API não guarda estado e roda como função na Vercel. O chat também não guarda conversa.
- O registro `api/data/manuals.yaml` já liga cada manual aos seus `model_codes` (73 códigos normalizados, nenhum repetido entre manuais, conferido em 2026-10-08). Um manual cobre muitos códigos (o Electrolux G0045837 cobre 37).
- O `api/vercel.json` exclui `data/**` da função, então hoje o registro não chega à produção. O caminho padrão do registro (`data/manuals.yaml`) é relativo ao diretório de trabalho, que na Vercel não é garantidamente `api/`.
- Cada trecho no Chroma já tem `manual_id` nos metadados, então filtrar por manual não pede reindexar.
- A pessoa espera uma entrada só e quer que a Manu perceba o modelo sozinha, sem um passo à parte nem um botão para procurar o código. Quem não tem o código à mão tem de poder perguntar do mesmo jeito.
- Os 73 códigos do registro têm de 3 a 7 caracteres, todos com letra e número (conferido em 2026-10-08), o que torna segura uma comparação exata dentro de texto livre: uma palavra comum não vira código.
- Os testes rodam sem rede, sem Ollama e sem chave do Claude (`.claude/rules/api.md`).

## Requirements

**User stories**:
- Como pessoa com um aparelho em casa, quero dizer qual é o código do modelo para receber respostas só do manual dele.
- Como pessoa que cita o modelo na pergunta ("minha DB44 está quente"), quero que a Manu perceba e responda só com o manual dele, sem eu apertar nada.
- Como pessoa que não sabe o código, quero perguntar do mesmo jeito e receber a resposta de todos os manuais, como hoje.
- Como pessoa que tem dois aparelhos, quero tirar ou trocar o aparelho sem perder a conversa na tela, e escolher entre eles quando cito dois códigos.

**Acceptance criteria** (o contrato; cada item é checável sozinho):
- **AC-1**: `GET /products/{código}` com um código que está no registro devolve 200 com `manual_id`, `brand`, `category` (como no YAML) e `model_codes` (como no YAML).
- **AC-2**: A comparação ignora caixa, espaços e hífen: `db44`, `DB 44` e `DB-44` resolvem para o mesmo manual.
- **AC-3**: Código sem correspondência exata, ou com caractere fora de `[A-Za-z0-9 -]`, devolve 404 com "Não achei esse código nos manuais que conheço.", sem erro de servidor.
- **AC-4**: `POST /ask` com `manual_id` busca só nos trechos desse manual: toda citação devolvida tem esse `manual_id`.
- **AC-5**: `POST /ask` sem `manual_id` se comporta exatamente como na Fase 1. Ausente e `null` são iguais; string vazia dá 422.
- **AC-6**: `POST /ask` com `manual_id` fora do registro devolve 404 com "Produto não encontrado." e nunca cai na busca geral.
- **AC-7**: Com `manual_id`, as recusas dos três caminhos (limiar, recusa do gerador, resposta sem citação) usam a frase "Não encontrei essa informação no manual da {categoria} {marca}. Se o problema continuar, procure a assistência técnica autorizada do fabricante."; o limiar de similaridade não muda.
- **AC-8**: A barra de pergunta é a única entrada do chat e só recebe perguntas: título "Qual é a sua dúvida?", sem campo, modo ou botão de código. Antes de responder cada pergunta, inclusive a que chega por `?q=` na URL, o chat consulta a detecção (AC-15). Com um aparelho achado, ele vira o chip com o código do registro e "categoria marca", e a resposta sai só do manual dele.
- **AC-9**: A detecção é uma ajuda e nunca bloqueia: se ela falhar (503, rede ou qualquer outra falha), a pergunta segue com o produto que já estava escolhido, ou sem produto, e não aparece erro por isso. Zero códigos achados também segue com o produto atual, ou sem produto. Enquanto a detecção corre o turno conta como em andamento e enviar outra pergunta fica bloqueado.
- **AC-10**: Com produto selecionado, toda pergunta envia o `manual_id` e o código do registro (`model_code`). "Tirar aparelho" (no chip) limpa o produto, mantém a conversa na tela e deixa a barra pronta para a próxima pergunta, que pode citar outro modelo. Recarregar a página recomeça sem produto. Um 404 do `/ask` avisa "Esse aparelho não foi encontrado. Cite o modelo de novo na pergunta ou siga sem aparelho." e limpa o produto, mas só se ele ainda for o produto daquele turno. O "Tentar de novo" de um turno com erro envia com o produto com que o turno foi enviado, sem repetir a detecção.
- **AC-11**: `manu-validate` falha quando dois códigos de manuais diferentes, ou do mesmo manual, são iguais depois de normalizados, nomeando os manuais e o código.
- **AC-12**: Na função da Vercel o registro está disponível: `GET /products/DB44` responde 200 numa prévia, e a API falha na subida se o registro faltar.
- **AC-13**: Com `manual_id` e `model_code`, a resposta é escrita para esse código, sem listar outros modelos do mesmo manual como se fossem o da pessoa. Um `model_code` que não pertence ao manual dá 422, e `model_code` sem `manual_id` também.
- **AC-14**: Se a pergunta tem só código (`only_codes`, AC-15), nenhuma resposta é pedida à API: o aparelho é escolhido sem bolha na conversa e a barra segue esperando a pergunta. Sem produto atual aparece o chip e o aviso para leitor de tela "Aparelho escolhido: {código}, {categoria} {marca}"; com outro manual, o chip troca e vale o AC-17; com o mesmo manual, só o código do chip e o `model_code` são atualizados.
- **AC-15**: `POST /products/detect` com `{"text": "..."}` (1 a 1000 caracteres, medidos depois do `trim`, como no `/ask`) devolve 200 com `matches`, `unrecognized` e `only_codes`. Cada item de `matches` é um manual diferente, na ordem em que aparece no texto, com `code` (o código do registro, como está no YAML), `matched` (o trecho do texto, como está escrito) e `product` (`manual_id`, `brand`, `category`, `model_codes` como no YAML). Sem código reconhecido, `matches` vem vazio com status 200. Regras de comparação: token é uma sequência máxima de `[A-Za-z0-9]` e qualquer outro caractere é fronteira, então "DB44?", "(DB44)" e "DB44," casam e "XDB44Y" não; a janela junta de 1 a 3 tokens seguidos separados só por espaço ou hífen; a varredura vai da esquerda para a direita, tentando 3, 2 e 1 tokens em cada posição e consumindo os que casarem; um token de uma letra não se junta ao seguinte ("a 10" não vira "A10"); a normalização é a do AC-2. `unrecognized` lista os tokens que começam com letra, têm algum número, 3 a 15 caracteres e não foram consumidos por um código (assim "220V" e "60Hz" não entram). `only_codes` é verdadeiro quando todos os tokens do texto foram consumidos por códigos; "e" e "ou" entre códigos são ignorados. Texto vazio ou com mais de 1000 caracteres dá 422.
- **AC-16**: Com dois ou mais aparelhos de manuais diferentes na pergunta, a Manu não responde ainda: o turno mostra a bolha da pergunta e "Qual destes é o seu aparelho?" com um botão por aparelho ("código · categoria marca") e "Nenhum destes". Depois do clique, no mesmo turno, os botões viram o texto "Escolhido: {código}" ou "Sem aparelho" e a resposta entra nele. Escolher um aparelho o seleciona (e vale o AC-17 se difere do atual) e envia a mesma pergunta com ele, ou só o seleciona se `only_codes`, e nesse caso o turno fecha sem resposta; "Nenhum destes" envia a mesma pergunta sem produto e deixa o produto limpo. Vários códigos do mesmo manual contam como um aparelho só. O turno aberto não tem "Tentar de novo" e "Tirar aparelho" continua livre.
- **AC-17**: Com um aparelho já escolhido, uma pergunta que cita o código de outro manual troca o chip para o novo e avisa "Troquei para {código}, {categoria} {marca}.", acima da barra. Citar outro código do mesmo manual atualiza em silêncio o código do chip e o `model_code`, sem aviso; citar o mesmo código não muda nada. Se a pessoa tirar ou trocar o aparelho com a mão enquanto a detecção ainda corre, a pergunta segue com o estado atual da página e o resultado da detecção é descartado.
- **AC-18**: Quando a detecção não acha nenhum aparelho mas devolve `unrecognized` (um código digitado errado ou com sufixo), a pergunta é respondida como no AC-9 e a Manu avisa acima da barra, sem erro: sem produto, "Não reconheci {X}; respondi com todos os manuais."; com produto, "Não reconheci {X}; respondi com o manual de {código do chip}." O aviso some quando a pessoa começa a editar a barra.

## Options considered

### Option 1: Estado no navegador, `manual_id` em cada pergunta, endpoint de resolução separado

O chat resolve o código em `GET /products/{código}`, guarda o `manual_id` e o código digitado, e os envia em cada `/ask`. A API continua sem estado.

**Pros**:
- Combina com a função sem estado e com um chat que já não guarda conversa.
- Separa identificar de responder, e o mesmo endpoint serve às fatias 2 e 3.
- `/ask` sem os campos segue idêntico, então nada que funciona hoje quebra.

**Cons**:
- O cliente decide qual manual usar, então a API precisa validar `manual_id` e `model_code` a cada chamada.
- Um endpoint e um proxy a mais para manter.

### Option 2: Sessão na API

A API guarda o produto escolhido por sessão.

**Pros**:
- O cliente fica mais simples.

**Cons**:
- Pede armazenamento e identificação de sessão que o projeto não tem.
- Quebra o modelo de função sem estado.

### Option 3: Resolver o código dentro do `/ask`

O `/ask` recebe o código digitado e resolve a cada pergunta.

**Pros**:
- Uma chamada só.

**Cons**:
- Mistura identificar com responder e repete a resolução toda vez.
- Não deixa a interface mostrar o produto antes da primeira pergunta.

### Como a Manu identifica o modelo sozinha (decisão de 2026-10-08, depois da primeira versão)

A primeira versão pedia o código num modo da barra e tinha o botão "Procurar código". A pessoa quer que o chat perceba o modelo sem apertar nada.

- **A. Procurar o código enquanto a pessoa digita no modo aparelho**: muda pouco, mas ainda obriga a escolher o aparelho antes de perguntar e dispara buscas a cada pausa na digitação. Descartada.
- **B. Achar o código no texto da pergunta (escolhida)**: a pessoa só pergunta; a API compara o texto com o registro. Elimina o modo aparelho, serve a quem não tem o código à mão e não pede nenhuma tela nova.
- **A e B juntas**: dois caminhos para manter e uma tela com mais controles. Descartada.

Detecção em endpoint próprio (`POST /products/detect`) e não dentro do `/ask`: o `/ask` não muda (AC-4 a AC-7, AC-13 e a avaliação seguem valendo) e a interface pode perguntar "qual destes?" antes de gastar uma chamada ao gerador. A comparação é determinística e exata, sem modelo de linguagem.

## Decision

**Chosen option**: Option 1: Estado no navegador, `manual_id` em cada pergunta, endpoint de resolução separado

A API ganha `GET /products/{código}`, `POST /products/detect` (acha no texto da pergunta os códigos do registro) e os campos opcionais `manual_id` e `model_code` no `POST /ask`. A busca vetorial filtra por `manual_id`, o gerador recebe o código achado como dica, e o chat detecta o modelo em cada pergunta e guarda o produto escolhido só em memória da página.

## Rationale

A função na Vercel não guarda estado e o chat não guarda conversa, então levar a escolha no navegador custa dois campos por chamada e não cria infraestrutura nova. Separar o endpoint de resolução deixa a interface confirmar o produto antes de qualquer pergunta e prepara as fatias 2 (prefixo e candidatos) e 3 (modelo sem manual), que mexem só nesse endpoint. O risco de o cliente mandar qualquer `manual_id` é pequeno: o pior caso é consultar um manual público que a base já serve, e a API valida o id contra o registro.

Primeira decisão da pessoa que mantém a Manu (2026-10-08, trocada pela segunda, logo abaixo, no que toca ao modo aparelho): a interface tem uma entrada só. A primeira versão pôs um campo "Qual é o seu aparelho?" acima da barra, e a expectativa era uma barra única. A barra pede o código primeiro, o botão "Perguntar sem aparelho" e os exemplos dão a saída para quem não tem o código, e o chip com "Trocar" continua acima da barra. Alternativas descartadas: a Manu perguntar como bolha no chat (muda demais a tela inicial) e detectar o código dentro da pergunta (fica para a fatia 2, junto do prefixo).

Segunda decisão da pessoa que mantém a Manu (2026-10-08): a Manu identifica o modelo sozinha, achando o código no texto da pergunta (opção B). Vários códigos de manuais diferentes: a Manu pergunta qual é o da pessoa. Nenhum código: responde sem produto, como na Fase 1. O modelo achado vira o produto selecionado e vale nas perguntas seguintes. Isso reverte o que a primeira versão deixava para a fatia 2 ("detectar o código dentro da pergunta"); a fatia 2 passa a tratar só do prefixo.

Duas decisões que tomei por conta própria (RECOMMEND):
- A recusa nomeia categoria e marca, não o código. Um manual cobre dezenas de códigos, então a frase "manual da geladeira Electrolux" é a que vale para todos eles. O chip mostra o código digitado.
- O código digitado vai ao gerador como dica (`model_code`). Sem ele, o manual G0045837 pode devolver uma resposta que mistura os 37 modelos que cobre. A dica só entra se pertencer ao manual escolhido e passa por um filtro de caracteres, então não carrega texto livre para o prompt. Alternativa descartada: ficar só com o `manual_id` e aceitar a mistura de modelos.

## Feature design

**Data model sketch**: não há tabela nem coluna nova. Na subida da API monta-se um registro em memória a partir do `manuals.yaml`, com dois índices.

| Índice | Chave | Valor | Regra |
|---|---|---|---|
| `by_code` | código normalizado (maiúsculas, sem espaço, sem hífen) | `Manual` (id, brand, category, model_codes) e o código como está no YAML | único entre todos os manuais; duplicado faz `manu-validate` falhar |
| `by_id` | `manual_id` | `Manual` | único (já validado hoje) |

Código aceito: 1 a 40 caracteres de `[A-Za-z0-9 -]`; a normalização é `strip`, maiúsculas e remoção de espaços e hífens, e o limite de 40 vale antes de normalizar. Rótulos de categoria (constante `CATEGORY_LABEL`): `geladeira` → "da geladeira" e `micro-ondas` → "do micro-ondas"; o chip usa "geladeira" ou "micro-ondas" como no YAML.

**State transitions**: o estado vive só na página: `sem produto` → `produto selecionado (manual_id + código achado)` → `sem produto` ou outro produto. A barra tem um modo só, o de pergunta. Cada pergunta passa por esta decisão antes de ser respondida:

| Detecção devolve | O chat faz | O que a pessoa vê |
|---|---|---|
| falha (qualquer erro) | pergunta com o produto atual (AC-9) | nada de erro |
| 0 aparelhos, sem `unrecognized` | pergunta com o produto atual (AC-9) | resposta normal |
| 0 aparelhos, com `unrecognized` | pergunta com o produto atual e avisa (AC-18) | resposta e "Não reconheci …" |
| 1 aparelho, `only_codes`, sem produto atual | seleciona e não pergunta (AC-14) | chip e aviso de leitor de tela |
| 1 aparelho, `only_codes`, outro manual ou outro código do mesmo | atualiza o produto e não pergunta (AC-14, AC-17) | chip novo e, se for outro manual, "Troquei para …" |
| 1 aparelho, mesmo manual e mesmo código do atual | pergunta com o produto atual | resposta normal |
| 1 aparelho, mesmo manual, outro código | atualiza código e `model_code` em silêncio e pergunta (AC-17) | chip com o código novo, resposta |
| 1 aparelho, sem produto atual | seleciona e pergunta (AC-8) | chip aparece, resposta |
| 1 aparelho, outro manual que o atual | troca, avisa e pergunta (AC-17) | chip novo e "Troquei para …" |
| 2 ou mais aparelhos | não pergunta; mostra a escolha (AC-16) | "Qual destes é o seu aparelho?" |

A decisão desta tabela vive numa função pura em `web/lib/` (detecção, produto atual e `only_codes` entram; a ação sai), sem estado da página, para poder ser testada quando o web ganhar um executor de testes.

**Comportamento da barra**:
- Tela inicial e título: "Qual é a sua dúvida?", subtítulo "Pergunte do seu jeito. Se citar o modelo, como DB44, a resposta vem só do manual dele.", exemplos sempre visíveis enquanto não há conversa, placeholder "Qual é a sua dúvida?" e Enter envia, como antes da Fase 2.
- Chip e aviso ficam no espaço acima da barra: o chip mostra o código do registro, "categoria marca" e o botão "Tirar aparelho"; os avisos "Troquei para …" e "Não reconheci …" somem quando a pessoa começa a editar a barra.
- A escolha entre aparelhos (AC-16) é um turno do chat sem erro: a pergunta da pessoa aparece como bolha, com os botões no lugar da resposta, e depois do clique o próprio turno recebe a resposta. Com ela aberta, enviar nova pergunta fica bloqueado, como com uma resposta em andamento.
- Foco e leitor de tela: depois de "Tirar aparelho" e de escolher o aparelho (AC-14) o foco vai para a barra. Uma região `aria-live="polite"` anuncia "Aparelho escolhido: {código}, {categoria} {marca}", "Troquei para {código}, {categoria} {marca}", "Não reconheci {X}" e "Sem aparelho".
- Com uma resposta em andamento: "Tirar aparelho" continua livre e o turno em andamento mantém o produto com que foi enviado; só enviar nova pergunta fica bloqueado, como hoje. A detecção que chegar depois de a pessoa tirar o aparelho com a mão é descartada e a pergunta segue com o estado atual da página (AC-17).

Dá para tirar o aparelho a qualquer hora e citar outro modelo depois, na pergunta seguinte.

**API surface**:
| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| /products/{code} | GET | code:str (path, 1 a 40 caracteres) | manual_id, brand, category, model_codes | pública | 404 código fora do registro ou com caractere inválido, 422 código vazio ou longo |
| /products/detect | POST | text:str (1 a 1000 caracteres) | matches:[{code, matched, product:{manual_id, brand, category, model_codes}}], unrecognized:[str], only_codes:bool | pública | 422 texto vazio ou longo |
| /ask | POST | question:str (req), manual_id:str \| null (opt, não vazio), model_code:str \| null (opt, só com manual_id) | answer, refused, citations | pública | 404 manual_id fora do registro, 422 manual_id vazio, model_code sem manual_id ou de outro manual, pergunta inválida, 502/503 como hoje |
| /api/products/[code] (web, proxy) | GET | code:str (com `encodeURIComponent`) | repasse do corpo e do status da API | pública | 503 se a API não responder |
| /api/products/detect (web, proxy) | POST | repasse do corpo `{text}` | repasse do corpo e do status da API | pública | 503 se a API não responder |
| /api/ask (web, proxy) | POST | repasse do corpo, agora com manual_id e model_code opcionais | repasse | pública | como hoje |

Os proxies novos copiam o cabeçalho `x-vercel-protection-bypass` e o `cache: "no-store"` do proxy do `/ask`. A rota `app/api/products/detect/route.ts` é um segmento fixo e vence a dinâmica `[code]`. Assinaturas internas: `create_app(..., manuals)`, `detect_products(text, manuals)` no registro, `Asker.ask(question, manual=None, model_code=None)`, `VectorStore.query(embedding, k, manual_id=None)`, `Generator.generate(question, chunks, model_code=None)`.

**Value sourcing**:
| Action | Value produced / displayed | Source |
|---|---|---|
| GET /products | manual_id, brand, category, model_codes | o `Manual` achado em `by_code`, vindo do `manuals.yaml`, sem transformar |
| GET /products | texto do 404 | constante "Não achei esse código nos manuais que conheço." na API |
| /ask com manual_id | trechos do manual escolhido | filtro `where manual_id == valor` na consulta ao Chroma, com o `manual_id` vindo do corpo |
| /ask com manual_id | validade do id | consulta a `by_id`; fora dele, 404 com a constante "Produto não encontrado." |
| /ask com manual_id | nome do produto na recusa | `CATEGORY_LABEL[category]` e `brand` do `Manual` achado em `by_id` |
| /ask com model_code | dica para o gerador | `model_code` do corpo, aceito só se, normalizado, estiver em `by_code` e apontar para o mesmo `manual_id` |
| /ask com manual_id | citações do resultado | trechos recuperados, descartando por segurança qualquer um com `manual_id` diferente |
| Detecção | aparelhos achados e `only_codes` | `detect_products(texto)` sobre `by_code`: trechos de 1 a 3 palavras seguidas (separadas só por espaço ou hífen), normalizados, com ao menos uma letra e um número; trecho mais longo vence; um item por manual, o primeiro código citado |
| Detecção | `code` de cada item | o código do registro, guardado em `by_code` junto do `Manual` |
| Detecção | `matched` de cada item | o trecho do texto, como está escrito, com `trim` |
| Detecção | `unrecognized` | tokens do texto que começam com letra, têm algum número, 3 a 15 caracteres e não foram consumidos por um código |
| Escolha entre aparelhos | botões e rótulo | `matches` da detecção: `code`, `category` e `brand` do `Manual` |
| Barra | título, subtítulo e placeholder | constantes na interface (um modo só) |
| Chip da interface | código exibido e `model_code` | o `code` do registro do item achado (ou do botão escolhido), guardado no estado da página |
| Chip da interface | "categoria marca" | `category` e `brand` de `product` na resposta da detecção |
| Aviso "Troquei para …" | código, categoria e marca | o novo item achado; só quando o manual difere do produto atual |
| Aviso "Não reconheci …" | {X} e o código do chip | o primeiro item de `unrecognized`; o código vem do estado da página quando há produto |
| Pergunta enviada | manual_id e model_code | estado da página; o turno guarda o produto com que foi enviado, e o "Tentar de novo" usa esse |

**Key invariants**:
- Um código normalizado aponta para um único manual.
- Com `manual_id`, toda citação devolvida pertence a esse manual.
- `manual_id` desconhecido nunca vira busca geral.
- O limiar de similaridade e o `top_k` continuam os de hoje.
- `model_code` só chega ao prompt depois de validado contra o manual escolhido.
- A detecção nunca bloqueia nem atrasa uma resposta por erro: falhou, a pergunta segue.
- Vários aparelhos de manuais diferentes nunca viram resposta: a Manu pergunta qual é o da pessoa.
- A comparação do texto é exata e determinística; o texto da pergunta não vai a nenhum modelo de linguagem nessa etapa.

**Security model**: os endpoints são públicos e não há dado pessoal. O código digitado não é gravado. `manual_id` e `model_code` do cliente são validados contra o registro antes de entrar na consulta ou no prompt; o `model_code` só aceita `[A-Za-z0-9 -]`, então o prompt nunca recebe texto livre por esse campo. A categoria e a marca do texto de recusa vêm do registro, nunca do cliente. O `text` da detecção só é comparado com o registro e devolvido em forma de trecho achado: não é gravado nem enviado ao gerador, e `matched` e `unrecognized` saem do próprio texto, então a interface os mostra como texto puro, nunca como HTML.

**Configuration required**: nenhuma variável nova. O `vercel.json` troca a exclusão `data/**` por `data/{pdfs,chroma,extracted}/**`, mantendo `data/manuals.yaml` na função. O caminho padrão do registro passa a ser resolvido relativo ao pacote (`Path(__file__)`) quando `MANU_REGISTRY` não estiver definida, e a API falha na subida se o arquivo faltar.

**Critical test scenarios** (cada um mapeia a um critério de aceite):
- Happy path: perguntar citando um código do registro seleciona o produto e devolve citações só desse manual, verifica **AC-1**, **AC-4**, **AC-8**, **AC-10**.
- Normalização: `db44`, `DB 44` e `DB-44` dão o mesmo manual, verifica **AC-2**.
- Detecção: "minha DB44 está quente", "db 44", "DB-44?", "(DB44)" e "a DB44, a do fundo" acham o mesmo manual; "XDB44Y", "porta 44", "a 10" e "220V" não casam e uma pergunta sem código dá `matches` vazio; "DB44 ou G0045837" dá dois itens e `only_codes` verdadeiro; dois códigos do mesmo manual dão um item; um código inventado como "XY123" vai a `unrecognized` e "220V" não; todos os 73 códigos do registro acham o próprio manual quando escritos no meio de uma frase, verifica **AC-2**, **AC-15**, **AC-18**.
- Fluxo: abrir a página mostra a barra só de pergunta; perguntar citando o modelo mostra o chip e responde do manual dele; perguntar sem código segue sem produto; mandar só "DB44" escolhe sem perguntar; dois códigos mostram a escolha; com chip, citar outro manual troca e avisa; "Tirar aparelho" mantém a conversa; falha da detecção segue a pergunta; "Não reconheci" aparece com código errado; outro código do mesmo manual atualiza o `model_code` em silêncio; "Tentar de novo" usa o produto do envio; `?q=` passa pela detecção, verifica **AC-8**, **AC-9**, **AC-10**, **AC-14**, **AC-16**, **AC-17**, **AC-18**.
- Falha: `manual_id` inexistente no `/ask` devolve 404, não consulta o Chroma, e a interface limpa o produto, verifica **AC-6**, **AC-10**.
- Regressão: `/ask` sem `manual_id` devolve o mesmo que na Fase 1, e o eval chama sem `manual_id`, verifica **AC-5**.
- Recusa: com produto e trechos abaixo do limiar, após recusa do gerador e sem citação, a frase cita categoria e marca, verifica **AC-7**.
- Filtro: uma fixture com vários manuais mostra que só o manual escolhido volta, e um trecho de outro manual é descartado, verifica **AC-4**.
- Dica: `model_code` de outro manual ou sem `manual_id` dá 422; com dica válida o prompt recebe o código, verifica **AC-13**.
- Registro: códigos repetidos entre manuais ou dentro de um manual fazem o `manu-validate` falhar nomeando os dois lados, verifica **AC-11**.
- Deploy: `GET /products/DB44` responde 200 numa prévia da Vercel, a consulta filtrada funciona no Chroma Cloud, e a API falha na subida sem o registro, verifica **AC-12**.

## Build plan

Abordagem Tracer Bullet: primeiro um fio mínimo de ponta a ponta (código exato → API → busca filtrada → chip), depois engorda cada trecho.

1. `registry.py`: índices `by_code` e `by_id` com `find_by_code` e normalização simples, satisfies **AC-1**
2. `store.py`: `query` aceita `manual_id` opcional e filtra com `where`; `ask.py` repassa o filtro, satisfies **AC-4**, **AC-5**
3. `app.py` e `main.py`: carregar o registro na subida, `GET /products/{code}` e `manual_id` opcional no `/ask`, satisfies **AC-1**, **AC-4**
4. Web: proxy `app/api/products/[code]/route.ts` (com bypass e `no-store`), `lib/products.ts` com `encodeURIComponent` e `ask()` com `manualId` opcional, satisfies **AC-1**, **AC-10**
5. Web: chip simples com o produto; a entrada passa para a detecção na pergunta, tarefa 16, satisfies **AC-8**
6. Engordar a API: 404 para código e `manual_id` desconhecidos, filtro de caracteres, 422 para `manual_id` vazio, descarte defensivo de trechos de outro manual, satisfies **AC-3**, **AC-5**, **AC-6**
7. Normalização completa (caixa, espaços, hífen) e `manu-validate` falhando em código repetido, entre e dentro de manuais, satisfies **AC-2**, **AC-11**
8. Recusa que nomeia categoria e marca nos três caminhos quando há `manual_id`, satisfies **AC-7**
9. `model_code`: validação contra o manual, passagem ao `Generator` e ajuste do prompt em `claude.py`, satisfies **AC-13**
10. Interface da primeira versão (feita): 404 do `/ask` e estados de erro; o resto passa para a tarefa 16, satisfies **AC-10**
11. Deploy: glob do `vercel.json`, caminho do registro relativo ao pacote, falha na subida sem registro, e teste numa prévia incluindo a consulta filtrada no Chroma Cloud, satisfies **AC-12**
12. Testes em `api/tests/` com fixtures em `api/tests/fixtures/`, sem rede, garantindo que o eval segue chamando sem `manual_id`, e `npm run typecheck` no web, satisfies **AC-1** a **AC-13**
13. Web: barra única com dois modos (feita e já no código, ainda sem commit). **Substituída pela tarefa 16**: o modo aparelho, "Procurar código", "Perguntar sem aparelho" e "Escolher aparelho" saem. O `GET /products/{code}` (AC-1) continua na API, mas o chat deixa de usá-lo
14. API: `by_code` guarda o código do registro; `detect_products(text, manuals)` no registro com as regras do AC-15 (tokens, janelas de 1 a 3, varredura da esquerda para a direita, token de uma letra não se junta, um item por manual, `unrecognized`, `only_codes`) e `POST /products/detect` no `app.py`, satisfies **AC-15**, **AC-18**
15. Web: proxy `app/api/products/detect/route.ts` (com bypass e `no-store`) e `detectProducts(text)` em `lib/products.ts`, que devolve `matches: []`, `unrecognized: []` e `only_codes: false` se a chamada falhar, satisfies **AC-9**, **AC-15**
16. Web: uma função pura em `web/lib/` decide a ação a partir da tabela de transições. Depois, o `chat.tsx` perde o modo da barra, o campo de código e os botões "Procurar código", "Perguntar sem aparelho" e "Escolher aparelho"; cada pergunta passa pela detecção e segue a tabela de transições (AC-8, AC-9, AC-14, AC-16, AC-17); chip com "Tirar aparelho", avisos "Troquei para …" e "Não reconheci …", turno de escolha entre aparelhos com o resultado no mesmo turno, "Tentar de novo" com o produto do envio, `?q=` pela detecção, descarte de resultado quando a pessoa mexe no aparelho durante a detecção, foco e região `aria-live`. O título, o subtítulo e os exemplos voltam ao estado sem produto. Conferir no navegador, com e sem cursor, e `npm run typecheck`, satisfies **AC-8**, **AC-9**, **AC-10**, **AC-14**, **AC-16**, **AC-17**, **AC-18**
17. Testes da detecção em `api/tests/` (casos da seção Critical test scenarios, sem rede), satisfies **AC-2**, **AC-15**, **AC-18**

## Consequences

**Positive**:
- Respostas saem só do manual do aparelho, sem competir com trechos de outros modelos, e escritas para o código dele.
- Nenhuma reindexação, tabela ou variável de ambiente nova.
- `/ask` sem os campos novos fica idêntico, então a avaliação da Fase 1 segue válida como base de comparação.
- O endpoint de resolução já serve às fatias 2 e 3.
- A pessoa não precisa saber que existe um passo de aparelho: citar o modelo basta, e quem não cita pergunta como sempre.

**Negative / tradeoffs**:
- O cliente escolhe `manual_id` e `model_code`, então a API valida os dois a cada chamada.
- Sem prefixo, quem digita o código completo da etiqueta (com sufixo) leva um 404 até a fatia 2.
- A recusa cita categoria e marca, não o código digitado.
- A escolha se perde ao recarregar a página.
- Cada pergunta faz uma chamada a mais (a detecção, em memória) antes da resposta; se ela falhar, a pergunta segue sem ela, então o aparelho pode não ser reconhecido sem a pessoa ver erro.
- Quem nunca cita o modelo nunca ganha o chip e continua com a busca geral da Fase 1.
- O produto achado vale até a pessoa tirá-lo ou citar outro: uma pergunta sobre outro aparelho, sem código, cai no manual do chip e pode receber a recusa (que nomeia categoria e marca, o que ajuda a perceber).
- A detecção é exata: um código com sufixo, escrito fora do registro ou com erro de digitação não é reconhecido até a fatia 2 (prefixo); o aviso "Não reconheci …" cobre os que têm cara de código, mas não os escritos de outro jeito.
- A conferência de AC-8, AC-9, AC-10, AC-14, AC-16, AC-17 e AC-18 é manual, no navegador, porque o web não tem testes; só o `npm run typecheck` é automático.
- O prompt do gerador muda, então a qualidade das respostas com produto precisa ser conferida na fatia 4.

**Neutral**:
- O registro em memória é montado na subida da função; o `manuals.yaml` passa a ir para a Vercel.
- `/ask` sem produto continua buscando em todos os manuais, como na Fase 1.

## Follow-up

- [x] Limitar a taxa dos endpoints públicos (`/ask`, `/products`, `/products/detect`): feito em 2026-10-08 em `api/manu/ratelimit.py` (por IP, 20/min no `/ask` e 60/min nos outros, em memória por instância; o web repassa o IP em `x-manu-client-ip`). Um limite de borda no Firewall da Vercel continua sendo decisão de quem administra o projeto na Vercel. O `/ask` já está sem limite hoje; vale decidir isso à parte.
- [x] Fatia 4: recalibrar o limiar com a busca restrita, conferir o prompt com `model_code` e comparar com os 93% de acerto da Fase 1. Feito na spec 0004: 100% de acerto com produto contra 93%, limiar mantido em 0,5.
- [x] Atualizar o `CONTEXT.md` ("Produto selecionado" passa a existir de fato) e o `PRODUCT.md`, que já pode citar o código do modelo na interface.
- [x] Atualizar `.claude/rules/api.md` com a nota sobre `data/manuals.yaml` na função e o novo endpoint, quando a fatia for construída.
- [x] Fatia 2: estender a detecção no texto ao prefixo com cuidado (um prefixo curto dentro de texto livre aumenta os falsos positivos).
