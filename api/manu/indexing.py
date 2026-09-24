"""Indexação: registro de manuais → extração → embeddings → ChromaDB."""

import logging
from pathlib import Path

from manu.embedder import Embedder
from manu.extraction import extract_pages
from manu.registry import load_manuals
from manu.store import PageChunk, VectorStore

log = logging.getLogger(__name__)


def index_manuals(registry_path: Path, pdf_dir: Path, embedder: Embedder, store: VectorStore) -> None:
    total_indexed = total_discarded = 0
    for manual in load_manuals(registry_path):
        extraction = extract_pages(pdf_dir / manual.file)
        chunks = [
            PageChunk(
                manual_id=manual.id,
                brand=manual.brand,
                model=manual.models_label,
                category=manual.category,
                page=page.number,
                text=page.text,
            )
            for page in extraction.pages
        ]
        store.upsert(chunks, embedder.embed([c.text for c in chunks]))
        log.info("%s: %d páginas indexadas, %d descartadas", manual.id, len(chunks), extraction.discarded)
        total_indexed += len(chunks)
        total_discarded += extraction.discarded
    log.info("Total: %d páginas indexadas, %d descartadas", total_indexed, total_discarded)


def main() -> None:
    from manu.config import Settings
    from manu.embedder import OllamaEmbedder

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = Settings.from_env()
    index_manuals(
        settings.registry_path,
        settings.pdf_dir,
        OllamaEmbedder(settings.ollama_url, settings.embedding_model),
        VectorStore(settings.chroma_dir),
    )


if __name__ == "__main__":
    main()
