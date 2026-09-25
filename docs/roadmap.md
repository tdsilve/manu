# Roadmap do Manu

## Visão do produto

Assistente que responde dúvidas sobre um eletrodoméstico com base no manual oficial do modelo, com citação da página. O produto é identificado pela foto da etiqueta de identificação (ou pelo código do modelo digitado) e a pessoa descreve a dúvida em texto. A garantia é um dos assuntos possíveis, não um requisito: o produto não precisa estar na garantia.

Escopo do MVP: geladeiras e micro-ondas, marcas Electrolux e Brastemp, 15 a 20 manuais.

## Fases

1. RAG básico ([spec](fases/fase-1/spec.md))
2. Identificação por código digitado: registro com os códigos de modelo cobertos por cada manual, correspondência por prefixo (com escolha entre candidatos), busca restrita ao produto selecionado e registro de modelos sem manual
3. Identificação pela foto da etiqueta: Claude com visão, confirmação do código lido, gabarito com fotos de etiquetas
4. Citações
5. Benchmark e avaliação
6. Chunking e retrieval
7. Memória de conversa
8. LLM + SQL
9. RAG + SQL + APIs + agente, incluindo a busca de manual ([ADR 0007](adr/0007-busca-de-manual-apenas-como-fallback.md))

## Melhorias já identificadas

- **Extração de PDF:** pdfplumber → avaliar OCR ou modelo de visão (Fase 6).
- **Chunking:** por página → comparar com tamanho fixo (com sobreposição) e divisão por seção ou parágrafo (Fase 6).
- **Retrieval:** top-k = 3 fixo → reranking ou método mais avançado (Fase 6).
- **Avaliação (execução):** script manual → GitHub Actions (fase intermediária).
- **Avaliação (julgamento):** manual → LLM como juiz quando o gabarito crescer.
- **Gabarito:** escrito à mão → expandido com ajuda de LLM, com revisão da autora.
- **Geração:** Claude → comparar com modelo local via Ollama, como experimento medido (Fase 6).
- **Interface:** simples na Fase 1 → identidade visual de produto nas fases finais.
- **Busca de manual:** base montada à mão → busca no site do fabricante só quando o código do modelo não tiver manual na base (Fase 9, agente). Ver [ADR 0007](adr/0007-busca-de-manual-apenas-como-fallback.md).

## Riscos e cuidados

- Se no futuro houver upload de nota fiscal (para validar a garantia), mascarar o CPF.
- O risco de responsabilidade é baixo neste domínio: um erro leva, no pior caso, a uma ligação desnecessária para a assistência técnica, sem prejuízo financeiro direto nem consequência jurídica.
- Termos de uso dos fabricantes: ver [ADR 0006](adr/0006-manuais-fora-do-repositorio.md).
