# Embeddings e base vetorial hospedados no deploy

O deploy público roda na Vercel, que não executa o Ollama e só enxerga o que está no git. Em produção, os embeddings vêm da Voyage AI (`voyage-3.5`, multilíngue) e a base fica no Chroma Cloud, indexada a partir da máquina da autora com `manu-index`. O desenvolvimento local continua com Ollama e ChromaDB em disco: a escolha é feita por variáveis de ambiente (`EMBEDDING_PROVIDER`, `CHROMA_API_KEY`), sem mudar o pipeline.

## Considered Options

- **Servidor próprio com Ollama:** mantém tudo local, mas exige uma VM com memória para o `bge-m3` e manutenção contínua.
- **Base vetorial no pacote da função:** esbarra no [ADR 0006](0006-manuais-fora-do-repositorio.md), porque um deploy pelo GitHub só leva o que está versionado.

## Consequences

- O limiar de similaridade é calibrado por modelo de embeddings: o valor do deploy não vale para o `bge-m3` local, e vice-versa.
- A API em produção cabe no limite de 500 MB da Vercel porque extração de PDF e `uvicorn` ficam no extra `local` do `pyproject.toml`.
