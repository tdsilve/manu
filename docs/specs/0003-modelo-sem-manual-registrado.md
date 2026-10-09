# 0003. Modelo sem manual registrado

**Date**: 2026-10-08
**Status**: In Progress

## Summary

Quando a pergunta cita algo com cara de código de modelo e o registro não tem esse manual, a Manu diz com clareza que não tem o manual desse modelo, responde com o que conhece e anota o código, sem dado pessoal, para quem mantém a base saber quais manuais adicionar. Um comando lê essa lista.

## Context

A detecção (specs 0001 e 0002) já devolve `unrecognized` com os tokens que parecem códigos e não casaram com nada. A fatia 3 do roadmap pede registrar esses modelos e mostrar uma mensagem honesta. A API roda como função sem disco gravável; o Chroma Cloud do projeto já guarda os trechos dos manuais e pode guardar também a lista de modelos sem manual.

## Requirements

**User stories**:
- Como pessoa com um modelo sem manual na base, quero saber que a Manu não tem esse manual, e não achar que a resposta é do meu aparelho.
- Como quem mantém a base, quero ver quais modelos as pessoas citam e a Manu não tem, do mais citado para o menos.

**Acceptance criteria**:
- **AC-1**: `POST /products/detect` grava, para cada item de `unrecognized` (no máximo 3 por chamada), o código normalizado, quantas vezes foi citado, a primeira e a última data; nada mais do texto, nenhum IP ou identificador da pessoa.
- **AC-2**: Se a gravação falhar, a detecção responde normalmente e o erro vai só para o log.
- **AC-3**: O aviso do chat para código sem manual diz "Não reconheci {X}; respondi com todos os manuais. Anotei o modelo para a base crescer." (ou "…respondi com o manual de {código do chip}. Anotei…" quando há aparelho escolhido).
- **AC-4**: `manu-missing` lista os modelos anotados, do mais citado para o menos, com a contagem e a última data, e aceita `--limit`.
- **AC-5**: Códigos achados (exatos ou por prefixo) e palavras sem cara de código nunca são gravados.

## Decision

Guardar numa coleção `missing_models` do mesmo Chroma (um registro por código normalizado, com contagem e datas nos metadados) e ler com o comando `manu-missing`.

## Rationale

O Chroma Cloud já está no projeto e na função, então não entra serviço novo. Gravar na própria chamada de detecção evita uma chamada a mais do navegador e funciona para qualquer cliente. A coleção usa um vetor fixo de 1 dimensão (a coleção não é buscada por similaridade). Decisões minhas (RECOMMEND): contagem por menção, sem deduplicar por pessoa (não há identidade); sem painel, só o comando; o limite de 3 códigos por chamada e o formato de código (3 a 15 caracteres) reduzem abuso, e um limite de taxa segue no follow up da spec 0001.

## Feature design

**Value sourcing**:
| Valor | Fonte |
|---|---|
| Código gravado | item de `unrecognized`, em maiúsculas |
| Contagem e datas | o registro existente na coleção mais a chamada atual |
| Texto do aviso | constante no web, com `unrecognized[0]` e o código do chip |
| Lista do comando | a coleção `missing_models`, ordenada pela contagem |

**Key invariants**: só entra o token com cara de código (começa com letra, tem número, 3 a 15 caracteres) que não casou com nada; nenhum dado pessoal; falha de gravação nunca derruba a detecção.

## Build plan

1. `missing.py`: `MissingModels.record` e `top`, satisfies **AC-1**, **AC-5**
2. `app.py` e `main.py`: gravar na detecção, falha só no log, satisfies **AC-1**, **AC-2**
3. `manu-missing` em `pyproject.toml`, satisfies **AC-4**
4. Web: texto do aviso, satisfies **AC-3**
5. Testes, satisfies **AC-1** a **AC-5**

## Consequences

- Positivo: a lista de manuais a adicionar nasce do uso real.
- Negativo: erros de digitação também entram na lista; a contagem ajuda a separar.
- A coleção cresce sem limite; vale limpar de vez em quando.

## Follow-up

- [ ] Limite de taxa nos endpoints públicos, que agora também gravam.
