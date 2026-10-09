"""Limite de chamadas por pessoa nos endpoints públicos (spec 0001, Follow-up).

Janela deslizante em memória, por instância da função: segura abuso simples e erro de laço no
navegador, mas não substitui um limite de borda (Firewall da Vercel). O IP vem do cabeçalho que o
web repassa; quem forja o cabeçalho escapa do limite, por isso ele é a primeira defesa, não a única.
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable

CLIENT_IP_HEADER = "x-manu-client-ip"
RETRY_MESSAGE = "Muitas chamadas em pouco tempo. Tente de novo em instantes."

# Chamadas por minuto e por pessoa. O /ask é o mais caro (Voyage e Claude).
DEFAULT_LIMITS = {"ask": 20, "detect": 60, "product": 60}
WINDOW_SECONDS = 60.0
MAX_KEYS = 10_000  # teto de pessoas guardadas: passou disso, a janela mais antiga cai


def bucket_for(method: str, path: str) -> str | None:
    """Qual limite vale para a rota; None = sem limite (health e rotas desconhecidas)."""
    if method == "POST" and path == "/ask":
        return "ask"
    if method == "POST" and path == "/products/detect":
        return "detect"
    if method == "GET" and path.startswith("/products/"):
        return "product"
    return None


class RateLimiter:
    def __init__(
        self,
        limits: dict[str, int] | None = None,
        window: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limits = limits or DEFAULT_LIMITS
        self._window = window
        self._clock = clock
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def allow(self, bucket: str, client: str) -> float | None:
        """None quando a chamada passa; senão, quantos segundos faltam para liberar."""
        now = self._clock()
        hits = self._hits[(bucket, client)]
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limits[bucket]:
            return max(self._window - (now - hits[0]), 1.0)
        hits.append(now)
        if len(self._hits) > MAX_KEYS:
            oldest = min(self._hits, key=lambda k: self._hits[k][-1] if self._hits[k] else 0.0)
            del self._hits[oldest]
        return None
