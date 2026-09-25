const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function ask(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as AskResponse;
}
