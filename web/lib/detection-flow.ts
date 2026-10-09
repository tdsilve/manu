import type { Detection, SelectedProduct } from "@/lib/products";

export type Notice = { kind: "switched" | "unrecognized" | "prefix"; text: string };

// O que o chat faz com uma pergunta depois da detecção (spec 0001, tabela de transições).
export type Action =
  | { kind: "ask"; product: SelectedProduct | null; notice: Notice | null }
  | { kind: "select"; product: SelectedProduct; notice: Notice | null }
  | { kind: "choose"; options: SelectedProduct[]; onlyCodes: boolean };

export function productLabel({ product, code }: SelectedProduct): string {
  return `${code} · ${product.category} ${product.brand}`;
}

// Um aparelho achado entra no lugar do atual: outro manual avisa; o mesmo manual só atualiza o código.
export function applyFound(
  current: SelectedProduct | null,
  found: SelectedProduct,
): { product: SelectedProduct; notice: Notice | null } {
  if (current && current.product.manual_id !== found.product.manual_id) {
    return {
      product: found,
      notice: { kind: "switched", text: `Troquei para ${found.code}, ${found.product.category} ${found.product.brand}.` },
    };
  }
  return { product: found, notice: null };
}

export function decide(detection: Detection, current: SelectedProduct | null): Action {
  const found = detection.matches.map((m) => ({ product: m.product, code: m.code }));

  if (found.length === 0) {
    const [unknown] = detection.unrecognized;
    const notice: Notice | null = unknown
      ? {
          kind: "unrecognized",
          text: current
            ? `Não reconheci ${unknown}; respondi com o manual de ${current.code}.`
            : `Não reconheci ${unknown}; respondi com todos os manuais.`,
        }
      : null;
    return { kind: "ask", product: current, notice };
  }

  if (found.length > 1) return { kind: "choose", options: found, onlyCodes: detection.only_codes };

  const [match] = detection.matches;
  const applied = applyFound(current, found[0]);
  const { product } = applied;
  // Achado pelo começo do código: mostra o que foi entendido, a menos que já haja o aviso de troca.
  const notice: Notice | null =
    applied.notice ??
    (match.approximate
      ? { kind: "prefix", text: `Achei ${match.matched} pelo modelo ${match.code}.` }
      : null);
  return detection.only_codes ? { kind: "select", product, notice } : { kind: "ask", product, notice };
}
