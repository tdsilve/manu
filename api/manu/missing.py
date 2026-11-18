"""Modelos que as pessoas citam e o registro não tem: a lista de manuais a adicionar (spec 0003)."""

import argparse
import logging
import sys
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
        return self._all()[:limit]

    def last_seen_before(self, day: date) -> list[MissingModel]:
        """Os modelos citados pela última vez antes do dia; quem foi citado no próprio dia fica de fora."""
        cutoff = day.isoformat()  # os dias são gravados como AAAA-MM-DD, então comparar o texto compara os dias
        return [m for m in self._all() if m.last_seen < cutoff]

    def remove(self, codes: Iterable[str]) -> list[str]:
        """Apaga o registro de cada código que está na lista e devolve os códigos apagados."""
        wanted = list(dict.fromkeys(c.upper() for c in codes))
        if not wanted:
            return []
        found = list(self._collection.get(ids=wanted, include=["metadatas"])["ids"])
        if found:
            self._collection.delete(ids=found)
        return found

    def _all(self) -> list[MissingModel]:
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
        return sorted(models, key=lambda m: (-m.mentions, m.code))


def _day(value: str) -> date:
    try:
        # fromisoformat aceita outros formatos, como 20261001: só vale o dia que volta igual ao que foi escrito
        if date.fromisoformat(value).isoformat() == value:
            return date.fromisoformat(value)
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"data inválida: {value!r} (use AAAA-MM-DD)")


def _print_models(models: Sequence[MissingModel]) -> None:
    print("menções  último dia   modelo")
    for m in models:
        print(f"{m.mentions:>7}  {m.last_seen}  {m.code}")


def main() -> None:
    from manu.config import Settings
    from manu.wiring import build_store

    parser = argparse.ArgumentParser(
        description="Lista os modelos citados que não têm manual na base. Também tira um código da lista ou apaga os que não são citados desde uma data."
    )
    parser.add_argument("--limit", type=int, help="quantos modelos mostrar (padrão 20)")
    parser.add_argument("--remove", metavar="CÓDIGO", help="tira o código da lista, sem diferenciar maiúsculas de minúsculas")
    parser.add_argument(
        "--before",
        type=_day,
        metavar="AAAA-MM-DD",
        help="mostra os modelos citados pela última vez antes da data; só apaga com --yes",
    )
    parser.add_argument("--yes", action="store_true", help="com --before, apaga os modelos mostrados")
    args = parser.parse_args()

    if args.remove is not None and args.before is not None:
        parser.error("--remove e --before não podem ser usados juntos")
    if args.yes and args.before is None:
        parser.error("--yes só vale junto com --before")
    if args.limit is not None and (args.remove is not None or args.before is not None):
        parser.error("--limit só vale para a listagem, sem --remove nem --before")

    missing = MissingModels(build_store(Settings.from_env()).client)

    if args.remove is not None:
        removed = missing.remove([args.remove])
        if not removed:
            sys.exit(f"O código {args.remove.upper()} não está na lista de modelos sem manual. Nada foi apagado.")
        print(f"Código {removed[0]} removido da lista de modelos sem manual.")
        return

    if args.before is not None:
        old = missing.last_seen_before(args.before)
        if not old:
            print(f"Nenhum modelo com última citação antes de {args.before.isoformat()}: não há modelo para apagar.")
            return
        if not args.yes:
            _print_models(old)
            print(f"Nada foi apagado. Para apagar estes {len(old)}, repita o comando com --yes.")
            return
        removed = missing.remove(m.code for m in old)
        print(f"Modelos removidos da lista: {len(removed)} ({', '.join(removed)}).")
        return

    models = missing.top(20 if args.limit is None else args.limit)
    if not models:
        print("Nenhum modelo anotado ainda.")
        return
    _print_models(models)


if __name__ == "__main__":
    main()
