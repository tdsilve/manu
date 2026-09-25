# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Projeto de portfólio da autora, construído e apresentado como um produto real. A interface fala com quem tem uma geladeira ou um micro-ondas e está com uma dúvida sobre o aparelho, muitas vezes no meio do uso (barulho estranho, limpeza, temperatura, algo que parou de funcionar). Quem avalia o portfólio (recrutadores, pessoas técnicas) é quem de fato visita, mas avalia justamente o produto funcionando como produto: a interface não se dirige a essa pessoa nem vira página de "case".

## Product Purpose

Responder dúvidas sobre um eletrodoméstico com base no manual oficial do fabricante, mostrando o trecho e a página de onde a resposta veio. Sucesso: a pessoa resolve a dúvida sem procurar o PDF, e confia na resposta porque vê a fonte.

## Positioning

A resposta sai só do manual oficial, nunca de fórum ou do conhecimento geral de um modelo de linguagem, e sempre com a página citada. Quando os manuais não trazem a resposta, o Manu diz que não sabe em vez de inventar.

## Operating Context

- Duas páginas: home e chat. Não há outras rotas.
- O chat conversa com a API `POST /ask` (FastAPI), que devolve `answer`, `refused` e `citations` (manual, marca, modelo, página, trecho, similaridade).
- Cada pergunta é independente: ainda não há memória de conversa.

## Capabilities and Constraints

- Existe hoje (Fase 1): perguntas em texto sobre geladeiras e micro-ondas Electrolux e Brastemp; resposta com trecho, manual e página; recusa quando a similaridade fica abaixo do limiar.
- A interface cita apenas o que já existe. Nada de "em breve": identificação pela foto da etiqueta, código do modelo, mais marcas e memória de conversa não aparecem na interface enquanto não forem construídos.
- Terminologia do domínio em `CONTEXT.md` (Manual, Base de manuais, Código do modelo, Etiqueta de identificação).

## Brand Commitments

- O nome do produto é **Manu**.
- Referências visuais escolhidas pela autora para o redesign: https://lamp-studio-mateusz.kontakt167645.chatgpt.site/ e https://nextwork.ai/.

## Evidence on Hand

- Manuais listados em `api/data/manuals.yaml` (PDFs fora do repositório, ver ADR 0006).
- Não existem depoimentos, métricas de uso, número de usuários nem parcerias com fabricantes. Nada disso pode ser inventado.
- Marcas Electrolux e Brastemp aparecem só como texto: não usar logotipos dos fabricantes.

## Product Principles

1. A fonte é o produto: toda resposta mostra de onde veio.
2. Dizer "não sei" é parte da proposta, não um erro.
3. Linguagem do dia a dia na entrada; precisão do manual na saída.
4. Mostrar só o que existe.
