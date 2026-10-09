export type Product = {
  manual_id: string;
  brand: string;
  category: string;
  model_codes: string[];
};

// Produto escolhido: o que a API achou, mais o código do registro (vai de dica à resposta).
export type SelectedProduct = {
  product: Product;
  code: string;
};

export type DetectedProduct = {
  code: string;
  matched: string;
  product: Product;
};

export type Detection = {
  matches: DetectedProduct[];
  unrecognized: string[];
  only_codes: boolean;
};

const NO_DETECTION: Detection = { matches: [], unrecognized: [], only_codes: false };

// A detecção é uma ajuda: qualquer falha vira "nada achado" e a pergunta segue.
export async function detectProducts(text: string): Promise<Detection> {
  try {
    const response = await fetch("/api/products/detect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) return NO_DETECTION;
    return (await response.json()) as Detection;
  } catch {
    return NO_DETECTION;
  }
}
