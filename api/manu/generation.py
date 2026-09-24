"""Contrato do gerador: o que a orquestração espera do "cliente do Claude"."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    """Uma página recuperada da base de manuais."""

    chunk_id: str  # "<manual_id>:<página>"
    manual_id: str
    brand: str
    model: str  # códigos do modelo cobertos pelo manual, separados por vírgula
    page: int
    text: str
    similarity: float  # 0 a 1, maior = mais parecido com a pergunta


@dataclass(frozen=True)
class Generation:
    answer: str
    refused: bool  # os trechos não bastam para responder
    used_chunk_ids: list[str]


class GenerationError(Exception):
    """Falha ao gerar (rede, timeout, erro da API, resposta mal formada)."""


class Generator(Protocol):
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> Generation: ...
