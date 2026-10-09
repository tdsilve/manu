"""Cliente HTTP mínimo do Chroma Cloud (API v2), só com o que a Manu usa.

Em produção a API fala só com o Chroma Cloud. O pacote `chromadb` completo traz ~250 MB de
dependências (onnxruntime, kubernetes, grpc) que a função na Vercel não usa e que estouravam o disco
na partida; este cliente usa só o `httpx`, que já é dependência. O `chromadb` completo fica no extra
`local`, para o modo local e os testes.
"""

import os
from collections.abc import Sequence
from typing import Any

import httpx

DEFAULT_HOST = "api.trychroma.com"
TIMEOUT_SECONDS = 30.0


class ChromaHttpError(RuntimeError):
    pass


class HttpCollection:
    """Os métodos de `chromadb.Collection` que a Manu chama, sobre HTTP."""

    def __init__(self, http: httpx.Client, base: str, collection_id: str) -> None:
        self._http = http
        self._url = f"{base}/collections/{collection_id}"

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        response = self._http.request(method, f"{self._url}/{path}", json=body)
        if response.status_code >= 400:
            raise ChromaHttpError(f"Chroma Cloud {method} {path}: HTTP {response.status_code} {response.text[:200]}")
        return response.json()

    def upsert(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str] | None = None,
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        self._call(
            "POST",
            "upsert",
            {"ids": list(ids), "embeddings": [list(e) for e in embeddings], "documents": documents, "metadatas": metadatas},
        )

    def query(
        self,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int,
        where: dict[str, Any] | None = None,
        include: Sequence[str] = ("documents", "metadatas", "distances"),
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "query_embeddings": [list(e) for e in query_embeddings],
            "n_results": n_results,
            "include": list(include),
        }
        if where:
            body["where"] = where
        result: dict[str, Any] = self._call("POST", "query", body)
        return result

    def get(self, ids: Sequence[str] | None = None, include: Sequence[str] = ("metadatas", "documents")) -> dict[str, Any]:
        body: dict[str, Any] = {"include": list(include)}
        if ids is not None:
            body["ids"] = list(ids)
        result: dict[str, Any] = self._call("POST", "get", body)
        return result

    def delete(self, ids: Sequence[str]) -> None:
        self._call("POST", "delete", {"ids": list(ids)})

    def count(self) -> int:
        return int(self._call("GET", "count"))


class HttpChromaClient:
    def __init__(
        self,
        api_key: str,
        tenant: str,
        database: str,
        host: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        host = host or os.environ.get("CHROMA_HOST") or DEFAULT_HOST
        self._base = f"https://{host}/api/v2/tenants/{tenant}/databases/{database}"
        self._http = httpx.Client(headers={"x-chroma-token": api_key}, timeout=TIMEOUT_SECONDS, transport=transport)

    def get_or_create_collection(
        self, name: str, configuration: dict[str, Any] | None = None, embedding_function: object = None
    ) -> HttpCollection:
        body: dict[str, Any] = {"name": name, "get_or_create": True}
        if configuration:
            body["configuration"] = configuration
        response = self._http.post(f"{self._base}/collections", json=body)
        if response.status_code >= 400:
            raise ChromaHttpError(f"Chroma Cloud criar/obter coleção {name}: HTTP {response.status_code} {response.text[:200]}")
        return HttpCollection(self._http, self._base, response.json()["id"])
