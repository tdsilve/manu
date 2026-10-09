"""Modelos que as pessoas citam e o registro não tem: a lista de manuais a adicionar (spec 0003)."""

import argparse
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

log = logging.getLogger(__name__)

COLLECTION = "missing_models"
MAX_CODES_PER_CALL = 3
# A coleção não é buscada por similaridade: todo registro leva o mesmo vetor de 1 dimensão.
_NO_VECTOR: Sequence[float] = [0.0]


@dataclass(frozen=True)
class MissingModel:
    code: str
    mentions: int
    first_seen: str
    last_seen: str


class MissingModels:
    def __init__(self, client: Any) -> None:  # chromadb.ClientAPI ou HttpChromaClient
        self._collection = client.get_or_create_collection(COLLECTION, embedding_function=None)

    def record(self, codes: Iterable[str], today: date | None = None) -> None:
        """Soma uma menção por código. Só o código é gravado, nunca o texto da pergunta."""
        day = (today or date.today()).isoformat()
        for raw in list(dict.fromkeys(c.upper() for c in codes))[:MAX_CODES_PER_CALL]:
            existing = self._collection.get(ids=[raw], include=["metadatas"])
            metadatas = existing["metadatas"] or []
            previous = metadatas[0] if metadatas else None
            mentions = int(previous["mentions"]) + 1 if previous else 1
            first = str(previous["first_seen"]) if previous else day
            self._collection.upsert(
                ids=[raw],
                embeddings=[_NO_VECTOR],
                documents=[raw],
                metadatas=[{"mentions": mentions, "first_seen": first, "last_seen": day}],
            )

    def top(self, limit: int = 20) -> list[MissingModel]:
        found = self._collection.get(include=["metadatas"])
        models = [
            MissingModel(
                code=code,
                mentions=int(meta["mentions"]),
                first_seen=str(meta["first_seen"]),
                last_seen=str(meta["last_seen"]),
            )
            for code, meta in zip(found["ids"], found["metadatas"] or [])
        ]
        return sorted(models, key=lambda m: (-m.mentions, m.code))[:limit]


def main() -> None:
    from manu.config import Settings
    from manu.wiring import build_store

    parser = argparse.ArgumentParser(description="Lista os modelos citados que não têm manual na base.")
    parser.add_argument("--limit", type=int, default=20, help="quantos modelos mostrar (padrão 20)")
    args = parser.parse_args()

    models = MissingModels(build_store(Settings.from_env()).client).top(args.limit)
    if not models:
        print("Nenhum modelo anotado ainda.")
        return
    print("menções  último dia   modelo")
    for m in models:
        print(f"{m.mentions:>7}  {m.last_seen}  {m.code}")


if __name__ == "__main__":
    main()
