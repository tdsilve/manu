# Busca de manual só como fallback, sob demanda

O Manu identifica o produto pela foto da etiqueta e consulta o manual oficial daquele modelo. A base de manuais é montada à mão; a busca automática no site do fabricante é uma melhoria futura (fase 8) e só acontece quando o código do modelo identificado não tem manual na base, baixando apenas o manual desse modelo. Isso revê a regra anterior de "nenhum download automatizado", mantendo o espírito dela: um download por pedido real do usuário, igual ao que ele mesmo faria, sem varrer catálogos e sem redistribuir os PDFs ([ADR 0006](0006-manuais-fora-do-repositorio.md)).

## Considered Options

- **Só base manual, para sempre:** não cumpre a promessa de atender o modelo do usuário.
- **Scraping amplo do catálogo para pré-indexar tudo:** maior risco com os termos de uso e indexa manuais que ninguém pediu.

## Consequences

- Enquanto a busca não existe, um modelo sem manual recebe um aviso claro e o código fica registrado; esse registro guia quais manuais adicionar e, depois, dispara a busca.
