# 0002. Correspondência por prefixo e escolha entre candidatos

**Date**: 2026-10-08
**Status**: Accepted

## Summary

Códigos de etiqueta costumam trazer sufixos que o manual não lista ("DB44SX" para o manual da "DB44"). A detecção do modelo passa a achar o manual também quando o código escrito começa com um código do registro, e, quando mais de um manual combina, a Manu pergunta qual é o da pessoa, com os mesmos botões da escolha entre aparelhos. O que não combina com nada continua indo para o aviso "Não reconheci" (e, na fatia 3, para o registro de modelos sem manual).

## Context

A fatia 1 só reconhece código exato (spec 0001). Os 73 códigos do registro têm de 3 a 7 caracteres, todos com letra e número, e o prefixo dentro de texto livre aumenta o risco de falso positivo (um "IB7" casaria com "IB70", que é outro modelo).

## Requirements

**User stories**:
- Como pessoa com o código completo da etiqueta, quero ser reconhecida mesmo com o sufixo que o manual não lista.
- Como pessoa cujo código combina com mais de um manual, quero escolher o meu.

**Acceptance criteria**:
- **AC-1**: Sem correspondência exata, um token que começa com um código do registro e termina com 1 a 3 caracteres, o primeiro deles uma letra, é reconhecido como esse código ("DB44SX" acha "DB44S"; "TF38X" acha "TF38").
- **AC-2**: O sufixo que começa com número não vale ("IB70" não acha "IB7").
- **AC-3**: Só entram tokens que começam com letra, têm algum número e 5 ou mais caracteres; a correspondência exata sempre vence a de prefixo.
- **AC-4**: Dentro de um manual vale o prefixo mais longo; quando manuais diferentes combinam, cada um vira um item, e a interface mostra a escolha entre aparelhos (spec 0001, AC-16).
- **AC-5**: Cada item da detecção traz `approximate` (verdadeiro quando veio por prefixo); o `code` é o do registro e `matched` é o que a pessoa escreveu.
- **AC-6**: Um aparelho achado por prefixo mostra o aviso "Achei {escrito} pelo modelo {código}." no chat, a menos que haja o aviso de troca.
- **AC-7**: O texto achado por prefixo também sai da busca (spec 0004, AC-1) e não conta como `unrecognized`.

## Decision

Prefixo só em tokens únicos, com sufixo curto que começa com letra, no mesmo `ProductRegistry.detect`; a escolha entre candidatos reaproveita o turno de escolha existente.

## Rationale

Sufixos de etiqueta são letras curtas (cor, versão, mercado); número depois do código quase sempre é outro modelo, por isso a regra do AC-2. Um único passo na detecção mantém uma fonte de verdade e a interface quase não muda. Decisões minhas (RECOMMEND): sufixo de no máximo 3 caracteres e token de pelo menos 5; só detecção no texto, o `GET /products/{código}` segue exato (AC-1 da spec 0001).

## Feature design

**Value sourcing**:
| Valor | Fonte |
|---|---|
| `code` do item | o código do registro que é prefixo do token, de `canonical_code` |
| `approximate` | verdadeiro quando não houve correspondência exata |
| Candidatos | um item por manual, o prefixo mais longo de cada um |
| Aviso do chat | `matched` e `code` do item |

**Key invariants**: exata vence prefixo; sufixo que começa com número nunca casa; vários manuais nunca viram resposta sem a pessoa escolher.

## Build plan

1. `registry.py`: prefixo no `_scan`, `approximate` no item, satisfies **AC-1** a **AC-5**, **AC-7**
2. `app.py`: `approximate` na resposta, satisfies **AC-5**
3. Web: tipo, aviso "Achei … pelo modelo …" em `detection-flow`, satisfies **AC-6**
4. Testes, satisfies **AC-1** a **AC-7**

## Consequences

- Positivo: quem digita o código completo da etiqueta é reconhecido.
- Negativo: sufixos de mais de 3 caracteres, ou que começam com número, seguem sem reconhecimento.
- O aviso mostra o que foi achado, para a pessoa corrigir se estiver errado ("Tirar aparelho").

## Follow-up

- [ ] Medir quantos códigos reais de etiqueta o prefixo cobre, quando houver registro de modelos sem manual (spec 0003).
