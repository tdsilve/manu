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


DEFAULT_EMBEDDING_MODEL = {"ollama": "bge-m3", "voyage": "voyage-3.5"}


@dataclass(frozen=True)
class Settings:
    registry_path: Path
    pdf_dir: Path
    chroma_dir: Path
    embedding_provider: str  # "ollama" (local) ou "voyage" (hospedado)
    ollama_url: str
    embedding_model: str
    voyage_api_key: str | None
    chroma_api_key: str | None  # definida: usa o Chroma Cloud em vez de chroma_dir
    chroma_tenant: str | None
    chroma_database: str | None
    anthropic_api_key: str | None
    claude_model: str
    top_k: int
    similarity_threshold: float
    cors_origins: list[str]

    @classmethod
    def from_env(cls, dotenv: Path = Path(".env")) -> "Settings":
        _load_dotenv(dotenv)
        env = os.environ.get
        provider = env("EMBEDDING_PROVIDER", "ollama")
        if provider not in DEFAULT_EMBEDDING_MODEL:
            raise ValueError(f"EMBEDDING_PROVIDER inválido: {provider}")
        return cls(
            registry_path=Path(env("MANU_REGISTRY", "data/manuals.yaml")),
            pdf_dir=Path(env("MANU_PDF_DIR", "data/pdfs")),
            chroma_dir=Path(env("MANU_CHROMA_DIR", "data/chroma")),
            embedding_provider=provider,
            ollama_url=env("OLLAMA_URL", "http://localhost:11434"),
            embedding_model=env("EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL[provider],
            voyage_api_key=env("VOYAGE_API_KEY") or None,
            chroma_api_key=env("CHROMA_API_KEY") or None,
            chroma_tenant=env("CHROMA_TENANT") or None,
            chroma_database=env("CHROMA_DATABASE") or None,
            anthropic_api_key=env("ANTHROPIC_API_KEY") or None,
            claude_model=env("CLAUDE_MODEL", "claude-opus-5"),
            top_k=int(env("TOP_K", "5")),
            similarity_threshold=float(env("SIMILARITY_THRESHOLD", "0.5")),
            # Várias origens separadas por vírgula (ex.: domínio de produção e localhost).
            cors_origins=[o.strip() for o in env("CORS_ORIGIN", "http://localhost:3000").split(",") if o.strip()],
        )
