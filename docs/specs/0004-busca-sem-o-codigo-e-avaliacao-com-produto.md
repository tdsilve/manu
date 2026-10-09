# 0004. Busca sem o código na pergunta e avaliação com produto

**Date**: 2026-10-08
**Status**: Accepted

## Summary

Quando a pergunta cita o modelo ("Minha DB44: a lateral está quente"), o código atrapalha a busca, porque o manual já foi escolhido pelo filtro. A API passa a buscar com a pergunta sem o código e responde com a pergunta inteira. O `manu-eval` ganha um modo com produto, que mede o ganho contra os 93% da Fase 1, e o cartão de recusa do chat ganha uma dica de como perguntar melhor.

## Context

Medido em 2026-10-08 com o pipeline real: a mesma pergunta cai de 0,514 para 0,466 de similaridade só por trazer "Minha db44:", e a Manu a recusa porque o limiar é 0,5. Tirar o código devolve 0,523. Palavras diferentes das do manual ("esquenta" contra "quente") derrubam mais (0,345), e isso a API não conserta sozinha. A recusa da Fase 1 e da fatia 1 continua a mesma frase.

## Requirements

**User stories**:
- Como pessoa que cita o modelo na pergunta, quero a mesma resposta que teria sem citá-lo.
- Como mantenedora, quero medir o ganho da busca com produto contra a Fase 1.
- Como pessoa recusada, quero uma dica de como reformular.

**Acceptance criteria**:
- **AC-1**: Com `manual_id`, a busca vetorial usa a pergunta sem os códigos do registro citados nela; o gerador recebe a pergunta inteira.
- **AC-2**: Se a pergunta, sem os códigos, ficar com menos de 3 caracteres, a busca usa a pergunta original.
- **AC-3**: Sem `manual_id`, a busca usa a pergunta original, como na Fase 1.
- **AC-4**: `manu-eval --product` roda cada pergunta do gabarito com o manual esperado selecionado e o código do modelo escrito na pergunta, e o relatório compara com a busca sem produto (acerto de busca, recusa correta, recusa indevida e a tabela de limiares).
- **AC-5**: O limiar de similaridade só muda se o relatório mostrar ganho de recusa correta sem perder acerto; a decisão fica registrada nesta spec.
- **AC-6**: O cartão de recusa do chat mostra uma dica: descrever o sintoma com as palavras do manual (por exemplo "quente" em vez de "esquenta") e citar o modelo; a tela inicial traz a mesma orientação antes da primeira pergunta ("diga o que acontece, onde e quando, com as palavras do manual").

## Decision

Tirar o código só do texto da busca, dentro da API (`ProductRegistry.strip_codes`), e medir com um modo novo do `manu-eval`. A dica é texto fixo no cartão de recusa do web, sem mexer na frase da API (spec 0001, AC-7).

## Rationale

O filtro por manual já faz o trabalho do código, então ele só adiciona ruído ao vetor. Tirar na API mantém a regra num lugar só e serve a qualquer cliente. Reescrever a pergunta com um modelo de linguagem resolveria também o vocabulário, mas soma uma chamada por pergunta e mexe numa etapa que hoje é uma peça solta e medida; fica para depois dos números.

Decisões minhas (RECOMMEND): a avaliação com produto escreve o código na pergunta ("Na minha {código}, {pergunta}") para medir o fluxo real; para itens sem resposta usa o primeiro manual da mesma categoria; o limiar só muda com ganho medido.

## Feature design

**Value sourcing**:
| Valor | Fonte |
|---|---|
| Texto da busca | a pergunta sem os trechos consumidos por códigos, vindos de `ProductRegistry.detect` |
| Pergunta ao gerador | a original, sem mudança |
| Manual e código do eval | `expected[0].manual_id` do gabarito e o primeiro `model_code` desse manual; sem resposta: primeiro manual da categoria do item |
| Dica na recusa | constante no web |

**Key invariants**: o gerador nunca recebe a pergunta sem o código; sem `manual_id` nada muda.

## Build plan

1. `registry.py`: `strip_codes(text)`, satisfies **AC-1**, **AC-2**
2. `ask.py` e `app.py`: `search_text` opcional na busca, satisfies **AC-1**, **AC-3**
3. `evaluation.py`: `--product` com comparação, satisfies **AC-4**
4. Rodar o eval, decidir o limiar e registrar aqui, satisfies **AC-5**
5. Web: dica no cartão de recusa, satisfies **AC-6**
6. Testes em `api/tests/`, satisfies **AC-1** a **AC-4**

## Resultado da avaliação (2026-10-08, `manu-eval --product`, 35 itens: 31 com resposta e 4 sem, voyage-3.5, limiar 0,5, 0 falhas)

| Métrica | Sem produto (Fase 1) | Com produto, código na busca | Com produto, código fora da busca |
|---|---|---|---|
| Acerto de busca | 90% (28/31) | 100% (31/31) | 100% (31/31) |
| Recusa correta | 100% (4/4) | 100% (4/4) | 100% (4/4) |
| Recusa indevida | 10% (3/31) | 3% (1/31) | 0% (0/31) |

Decisão do AC-5: o limiar **continua em 0,5**. Subir para 0,6 recusa corretamente 75% das perguntas sem resposta (3/4), mas passa a recusar 19% das com resposta (6/31), e isso piora o uso real. As melhores similaridades das perguntas sem resposta (0,444 a 0,607) se misturam às das com resposta (0,520 a 0,765).

Reclassificação da q25 (2026-10-08): "dá pra controlar o micro-ondas pelo celular, pelo wi-fi?" passou a ter resposta no gabarito, porque sete micro-ondas (Brastemp BMS45 e BMG45, Electrolux MF33S, MGA42, MB38T, ME3EP e MTO30) trazem a frase de que o aparelho "não é destinado a ser operado por… controle remoto", e `manu-eval --check` confirma o texto nas páginas. Uma primeira medição, ainda com a q25 como "sem resposta", deu 93% de acerto sem produto; os números acima já usam o gabarito novo.

## Consequences

- Positivo: a pergunta com código recupera a similaridade do texto limpo.
- Negativo: "esquenta" contra "quente" segue sem solução automática; a dica só orienta.
- O eval com produto custa uma rodada a mais de chamadas ao Claude e à Voyage.

## Follow-up

- [x] Reescrita da pergunta com modelo de linguagem: adiada para a Fase 6 (retrieval), porque a busca com produto já chega a 100% de acerto.
- [x] Recusa correta em 80% (4 de 5, contra 100% na Fase 1): a única recusa a menos é a q25, que o manual responde de fato e foi reclassificada no gabarito; o limiar fica em 0,5 e volta na Fase 5 (benchmark). Repetir `manu-eval --product` com o gabarito novo está pendente.
