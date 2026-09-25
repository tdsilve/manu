"""Gerador real: responde com o Claude, restrito aos trechos recuperados."""

import logging

import anthropic
from pydantic import BaseModel, ValidationError

from manu.generation import Generation, GenerationError, RetrievedChunk

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Você é o Manu, um assistente que responde dúvidas sobre eletrodomésticos usando \
exclusivamente trechos de manuais oficiais dos fabricantes.

Regras:
- Responda só com o que está escrito nos trechos fornecidos. Não use conhecimento \
próprio, não complete lacunas e não suponha informações de outros modelos.
- Responda em português do Brasil, de forma curta e direta, em linguagem simples.
- Em used_chunk_ids, liste os IDs exatos dos trechos que embasam a resposta.
- Se os trechos não bastarem para responder com segurança, marque refused como true, \
deixe answer vazio e used_chunk_ids vazio.
"""

# Saída estruturada: a orquestração nunca interpreta texto livre.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "refused": {"type": "boolean"},
        "used_chunk_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "refused", "used_chunk_ids"],
    "additionalProperties": False,
}

# Modelos que aceitam o fallback de servidor quando os classificadores de
# segurança recusam o pedido.
FALLBACK_MODELS = {"claude-opus-5", "claude-fable-5-1"}


class _Output(BaseModel):
    answer: str
    refused: bool
    used_chunk_ids: list[str]


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f'<trecho id="{c.chunk_id}" manual="{c.manual_id}" marca="{c.brand}" '
        f'modelos="{c.model}" pagina="{c.page}">\n{c.text}\n</trecho>'
        for c in chunks
    )


class ClaudeGenerator:
    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> Generation:
        content = f"Trechos dos manuais:\n\n{_format_context(chunks)}\n\nPergunta: {question}"
        use_fallback = self._model in FALLBACK_MODELS
        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            response = client.beta.messages.create(
                model=self._model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
                betas=["server-side-fallback-2026-07-01"] if use_fallback else anthropic.omit,
                fallbacks="default" if use_fallback else anthropic.omit,
            )
        # TypeError: o SDK não encontrou nenhuma credencial (ex.: ANTHROPIC_API_KEY ausente).
        except (anthropic.AnthropicError, TypeError) as error:
            raise GenerationError(f"Claude ({self._model}): {type(error).__name__}: {error}") from error

        if response.stop_reason == "refusal":
            # Recusa dos classificadores de segurança: tratada como "não sei responder".
            log.warning("Claude recusou o pedido (request_id=%s)", response._request_id)
            return Generation(answer="", refused=True, used_chunk_ids=[])
        if response.stop_reason != "end_turn":
            raise GenerationError(f"Claude parou com stop_reason={response.stop_reason}")

        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            output = _Output.model_validate_json(text)
        except ValidationError as error:
            raise GenerationError(f"Resposta mal formada do Claude: {error}") from error

        known = {c.chunk_id for c in chunks}
        used = [i for i in output.used_chunk_ids if i in known]  # descarta IDs inventados
        return Generation(answer=output.answer, refused=output.refused, used_chunk_ids=used)
