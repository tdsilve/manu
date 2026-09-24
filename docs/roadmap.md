# Roadmap do Manu

## Visão do produto

Assistente que ajuda o usuário a saber se um problema em um eletrodoméstico está coberto pela garantia, respondendo com base no manual oficial do fabricante, com citação da página. Na visão completa, o usuário envia a foto da etiqueta do produto (para extrair o modelo) e descreve o problema ou envia a foto do defeito.

Escopo do MVP: geladeiras e micro-ondas, marcas Electrolux e Brastemp, 15 a 20 manuais.

## Fases

1. RAG básico ([spec](fases/fase-1/spec.md))
2. Citações
3. Benchmark e avaliação
4. Chunking e retrieval
5. Knowledge base e metadados
6. Memória de conversa
7. LLM + SQL
8. RAG + SQL + APIs + agente

## Melhorias já identificadas

- **Extração de PDF:** pdfplumber → avaliar OCR ou modelo de visão (Fase 4).
- **Chunking:** por página → comparar com tamanho fixo (com sobreposição) e divisão por seção ou parágrafo (Fase 4).
- **Retrieval:** top-k = 3 fixo → reranking ou método mais avançado (Fase 4).
- **Avaliação (execução):** script manual → GitHub Actions (fase intermediária).
- **Avaliação (julgamento):** manual → LLM como juiz quando o gabarito crescer.
- **Gabarito:** escrito à mão → expandido com ajuda de LLM, com revisão da autora.
- **Geração:** Claude → comparar com modelo local via Ollama, como experimento medido (Fase 4/5).
- **Interface:** simples na Fase 1 → identidade visual de produto nas fases finais.
- **Busca de manuais:** pré-indexação manual → busca no site do fabricante como fallback quando o manual não estiver indexado (Fase 8, agente).

## Riscos e cuidados

- Se no futuro houver upload de nota fiscal (para validar a garantia), mascarar o CPF.
- O risco de responsabilidade é baixo neste domínio: um erro leva, no pior caso, a uma ligação desnecessária para a assistência técnica, sem prejuízo financeiro direto nem consequência jurídica.
- Termos de uso dos fabricantes: ver [ADR 0006](adr/0006-manuais-fora-do-repositorio.md).
