# Scope: Manu, Fase 2 (identificação por código digitado)

A Manu responde dúvidas sobre eletrodomésticos só com o manual oficial, citando a página. Esta fatia faz a pessoa dizer qual é o produto digitando o código do modelo, e a busca passa a olhar só o manual dele.

**Build approach:** Tracer Bullet (cada fatia atravessa registro, API e interface funcionando, só que estreita, e depois engorda um trecho de cada vez).
**Workflow:** Beta (depois do `/develop` rodam `/check verify` e `/test`). É o nível padrão do projeto. `/architect` é a parada recomendada para uma feature com decisão real, mas você pode pular se já sabe como construir. Qualquer feature pode ter a sua própria tag (por exemplo `· GA`).

_Isto são recomendações para manter a construção em ordem, não exigências. Pule o que não servir: se você já sabe como construir uma feature, use `/develop` e pule `/architect`. Você decide quando uma feature está `done`._

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| A | Pipeline e base de manuais | Fase 1 | existing |
| B | Pergunta e resposta com página citada | Fase 1 | existing |
| C | Avaliação com gabarito | Fase 1 | existing |
| D | Interface de chat | Fase 1 | existing |
| 1 | Produto selecionado por código exato | Slice 1 | in-progress |
| 2 | Correspondência por prefixo e escolha entre candidatos | Slice 2 | planned |
| 3 | Modelo sem manual registrado | Slice 3 | planned |
| 4 | Avaliação da busca restrita ao produto | Slice 4 | planned |
| 5 | Nova conversa e logo | Slice 1 | in-progress |

## Já existe (Fase 1)

### A. Pipeline e base de manuais · existing
Extração dos PDFs, indexação e o registro `manuals.yaml` com 17 manuais e seus `model_codes`. code in `api/manu/`, `api/data/`

### B. Pergunta e resposta com página citada · existing
`POST /ask` com limiar de similaridade, recusa quando o manual não traz a resposta e citações. Hoje a Manu escolhe o modelo sozinha quando a pergunta não diz qual é. A Fase 2 troca isso pela escolha explícita da pessoa. code in `api/manu/ask.py`

### C. Avaliação com gabarito · existing
`manu-eval` mede a busca contra o gabarito dos 17 manuais (93% de acerto de busca ao fechar a Fase 1). code in `api/eval/`, `api/manu/evaluation.py`

### D. Interface de chat · existing
Chat em Next.js que conversa com a API. code in `web/`

## Slice 1: Produto selecionado por código exato

### 1. Produto selecionado por código exato · in-progress
O fio mais fino que atravessa tudo: a pessoa digita um código que está no registro, a API acha o manual e a busca olha só aquele manual. A interface mostra o produto selecionado e deixa trocar de produto. Este é o walking skeleton da fase.
**Done when:** digitar um código exato do registro seleciona o produto, as perguntas seguintes são respondidas só com o manual dele, a interface mostra qual produto está selecionado e permite trocá-lo, e código desconhecido não quebra o fluxo.
- [x] Design it (spec): `/architect produto selecionado por código exato`
- [x] Build it: `/develop produto selecionado por código exato`
   - [x] Fio mínimo de ponta a ponta: registro, `GET /products`, busca filtrada, campo e chip simples (AC-1, AC-4, AC-8)
   - [x] API completa: normalização, 404 e 422, validação de duplicados no `manu-validate`, `model_code` no prompt (AC-2, AC-3, AC-5, AC-6, AC-11, AC-13)
   - [x] Recusa com produto e interface completa: Trocar, estados de erro e carregando (AC-7, AC-9, AC-10)
   - [x] Barra única com modo aparelho (feita; substituída pelo próximo item)
   - [x] A Manu identifica o modelo sozinha: detecta o código no texto da pergunta (`POST /products/detect`), escolhe entre vários aparelhos e sem botão "Procurar código" (AC-8, AC-9, AC-10, AC-14 a AC-18)
   - [x] Deploy: `vercel.json`, caminho do registro, API e web em produção na Vercel, consulta filtrada no Chroma Cloud conferida (AC-12)
- [ ] Verify it: `/check verify produto selecionado por código exato`
- [ ] Test it: `/test produto selecionado por código exato`
Spec [0001](../specs/0001-produto-selecionado-por-codigo.md) · code in `api/manu/`, `web/components/chat.tsx`, `web/lib/detection-flow.ts`, `web/app/api/products/`

### 5. Nova conversa e logo · in-progress
Quem já conversou precisa começar de novo sem recarregar a página. O botão "Nova conversa" (canto superior direito) limpa as mensagens e o aparelho e fica na tela de conversa; o logo volta à tela inicial. A API não guarda histórico, então só a tela é limpa. Sem decisão pendente: é interface sobre estado que já existe.
**Done when:** "Nova conversa" apaga as mensagens e o aparelho escolhido e deixa a barra de pergunta pronta, sem voltar à tela inicial; o logo leva à tela inicial com o mascote e os exemplos; uma resposta que ainda estava a caminho não reaparece na conversa nova.
- [x] Build it: `/develop nova conversa e logo` (já construído, sem spec: não há decisão em aberto)
- [ ] Verify it: `/check verify nova conversa e logo`
- [ ] Test it: `/test nova conversa e logo`
code in `web/components/chat.tsx`, `web/components/wordmark.tsx`

## Slice 2: Correspondência por prefixo

### 2. Correspondência por prefixo e escolha entre candidatos · needs a decision
Códigos de etiqueta costumam trazer sufixos que o manual não lista. A API compara pelo começo do código e, quando mais de um manual combina, a pessoa escolhe entre os candidatos.
**Done when:** um código com sufixo extra encontra o manual certo, um código ambíguo mostra os candidatos para escolha, e um código que não combina com nada cai no caso sem manual.
- [ ] Design it (spec): `/architect correspondência por prefixo`

## Slice 3: Modelo sem manual

### 3. Modelo sem manual registrado · needs a decision
Quando o código não tem manual na base, a Manu diz isso com clareza e registra o código para orientar quais manuais adicionar (e, no futuro, a busca de manual, ADR 0007).
**Done when:** um código sem manual gera uma mensagem honesta na interface, o código fica registrado sem dado pessoal, e o registro pode ser lido por quem mantém a base.
- [ ] Design it (spec): `/architect modelo sem manual registrado`

## Slice 4: Medir o ganho

### 4. Avaliação da busca restrita ao produto · needs a decision
Estender o gabarito e o `manu-eval` para medir a busca já com o produto selecionado, e comparar com os 93% da Fase 1.
**Done when:** `manu-eval` roda com o produto selecionado, o relatório compara com a busca sem filtro, e o limiar de similaridade segue calibrado.
- [ ] Design it (spec): `/architect avaliação com produto selecionado`

## Deferred
Fora desta fatia, mantido para o plano ficar honesto.
- **Identificação pela foto da etiqueta**: Claude com visão e confirmação do código lido · Fase 3 · needs a decision
- **Busca de manual no site do fabricante**: só quando o código não tem manual · Fase 9 · needs a decision

## Legend

**The decision box.** Toda feature tem exatamente um, o sub passo cujo rótulo termina com `(spec)`. Os outros boxes são de execução e o `/architect` nunca marca um deles.

**Feature lifecycle**:

| State | Set by | The feature shows |
|---|---|---|
| `planned` · needs a decision | `/scope` | um box: `Design it (spec): /architect <feature>` |
| `in-progress` (designed) | `/architect` ao capturar a spec | `Design it` marcado; spec linkada; `Build it: /develop <feature>` com 2 a 5 marcos; `Verify it` e `Test it` |
| `in-progress` (building) | `/develop` | marcos marcados um a um; caminho do código preenchido |
| `in-progress` (verified) | `/check verify` | `Build it` e marcos marcados; `Verify it` marcado |
| `done` | você, quando decidir | boxes rodados marcados; no Beta, depois de `/test` |

- **Next step** = o primeiro box sem marca.
- **needs a decision** = rode `/architect` primeiro; a tag some quando a spec é capturada.
- **Status**: `planned` → `in-progress` → `done`, mais `existing` (anterior ao fluxo) e `dropped`.
- **Workflow** (cabeçalho) é o padrão do projeto: Beta = `/check verify` e depois `/test`.
