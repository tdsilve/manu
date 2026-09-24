"""Configuração por variáveis de ambiente (com leitura opcional de um arquivo .env)."""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Carrega KEY=valor de um .env sem sobrescrever o que já está no ambiente."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    registry_path: Path
    pdf_dir: Path
    chroma_dir: Path
    ollama_url: str
    embedding_model: str
    anthropic_api_key: str | None
    claude_model: str
    top_k: int
    similarity_threshold: float
    cors_origin: str

    @classmethod
    def from_env(cls, dotenv: Path = Path(".env")) -> "Settings":
        _load_dotenv(dotenv)
        env = os.environ.get
        return cls(
            registry_path=Path(env("MANU_REGISTRY", "data/manuals.yaml")),
            pdf_dir=Path(env("MANU_PDF_DIR", "data/pdfs")),
            chroma_dir=Path(env("MANU_CHROMA_DIR", "data/chroma")),
            ollama_url=env("OLLAMA_URL", "http://localhost:11434"),
            embedding_model=env("EMBEDDING_MODEL", "bge-m3"),
            anthropic_api_key=env("ANTHROPIC_API_KEY") or None,
            claude_model=env("CLAUDE_MODEL", "claude-sonnet-5"),
            top_k=int(env("TOP_K", "3")),
            similarity_threshold=float(env("SIMILARITY_THRESHOLD", "0.5")),
            cors_origin=env("CORS_ORIGIN", "http://localhost:3000"),
        )
