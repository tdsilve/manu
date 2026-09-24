"use client";

import { FormEvent, ReactNode, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Citation = {
  manual_id: string;
  brand: string;
  model: string;
  page: number;
  excerpt: string;
  similarity: number;
};

type AskResponse = {
  answer: string;
  refused: boolean;
  citations: Citation[];
};

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "done"; question: string; result: AskResponse };

// Palavras da pergunta com 4+ letras, para destacar no trecho citado.
function questionTerms(question: string): string[] {
  const words = question.toLowerCase().match(/[\p{L}\p{N}]{4,}/gu) ?? [];
  return [...new Set(words)];
}

function highlight(text: string, terms: string[]): ReactNode {
  if (terms.length === 0) return text;
  const escaped = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const parts = text.split(new RegExp(`(${escaped.join("|")})`, "giu"));
  return parts.map((part, i) =>
    i % 2 === 1 ? <mark key={i}>{part}</mark> : part,
  );
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  const loading = state.kind === "loading";
  const canSubmit = question.trim().length > 0 && !loading;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    const asked = question.trim();
    setState({ kind: "loading" });
    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: asked }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = (await response.json()) as AskResponse;
      setState({ kind: "done", question: asked, result });
    } catch {
      setState({ kind: "error" });
    }
  }

  return (
    <main>
      <h1>Manu</h1>
      <p className="subtitle">
        Pergunte sobre a sua geladeira ou micro-ondas. As respostas vêm dos manuais oficiais
        Electrolux e Brastemp.
      </p>

      <form onSubmit={onSubmit}>
        <label htmlFor="question" className="panel-title">
          Sua dúvida
        </label>
        <textarea
          id="question"
          value={question}
          maxLength={1000}
          placeholder="Ex.: a geladeira está fazendo barulho de água"
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" disabled={!canSubmit}>
          {loading ? "Consultando…" : "Perguntar"}
        </button>
      </form>

      {loading && (
        <p className="status" role="status">
          Consultando os manuais…
        </p>
      )}

      {state.kind === "error" && (
        <section className="panel error" role="alert">
          <p className="panel-title">Erro</p>
          <p className="answer">Algo deu errado ao consultar os manuais. Tente de novo.</p>
        </section>
      )}

      {state.kind === "done" && state.result.refused && (
        <section className="panel refused">
          <p className="panel-title">Não encontrei nos manuais</p>
          <p className="answer">{state.result.answer}</p>
        </section>
      )}

      {state.kind === "done" && !state.result.refused && (
        <section className="panel">
          <p className="panel-title">Resposta</p>
          <p className="answer">{state.result.answer}</p>
          {state.result.citations.length > 0 && (
            <div className="citations">
              {state.result.citations.map((c) => (
                <article key={`${c.manual_id}:${c.page}`} className="citation">
                  <p className="citation-source">
                    {c.brand} {c.model} · página {c.page}
                  </p>
                  <p className="citation-excerpt">
                    {highlight(c.excerpt, questionTerms(state.question))}
                  </p>
                  <details>
                    <summary>ver detalhes</summary>
                    Manual: {c.manual_id} · similaridade {c.similarity.toFixed(2)}
                  </details>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
