import type { SelectedProduct } from "@/lib/products";

export type Citation = {
  manual_id: string;
  brand: string;
  model: string;
  page: number;
  excerpt: string;
  similarity: number;
};

export type AskResponse = {
  answer: string;
  refused: boolean;
  citations: Citation[];
};

export class AskError extends Error {
  // retryAfter: segundos de espera do Retry-After (só no 429); null quando a resposta não trouxe um valor válido.
  constructor(
    readonly status: number,
    readonly retryAfter: number | null = null,
  ) {
    super(`HTTP ${status}`);
  }
}

// Com produto selecionado, a busca olha só o manual dele; sem produto, todos os manuais.
export async function ask(question: string, selected: SelectedProduct | null = null): Promise<AskResponse> {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      selected ? { question, manual_id: selected.product.manual_id, model_code: selected.code } : { question },
    ),
  });
  if (!response.ok) {
    const seconds = Number(response.headers.get("Retry-After"));
    throw new AskError(response.status, Number.isInteger(seconds) && seconds > 0 ? seconds : null);
  }
  return (await response.json()) as AskResponse;
}
