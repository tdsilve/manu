import type { ReactNode } from "react";
import { Icons } from "@/components/icons";
import { Button } from "@/components/ui/button";
import type { AskResponse } from "@/lib/ask";

export type Turn = {
  id: number;
  question: string;
  status: "loading" | "error" | "done";
  result?: AskResponse;
};

type ChatMessageProps = {
  turn: Turn;
  onRetry: () => void;
  busy: boolean;
};

// Palavras da pergunta com 4+ letras, para destacar no trecho citado.
function questionTerms(question: string): string[] {
  const words = question.toLowerCase().match(/[\p{L}\p{N}]{4,}/gu) ?? [];
  return [...new Set(words)];
}

function highlight(text: string, terms: string[]): ReactNode {
  if (terms.length === 0) return text;
  const escaped = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const parts = text.split(new RegExp(`(${escaped.join("|")})`, "giu"));
  return parts.map((part, i) => (i % 2 === 1 ? <mark key={i}>{part}</mark> : part));
}

export function ChatMessage({ turn, onRetry, busy }: ChatMessageProps) {
  return (
    <article data-slot="chat-message" className="mb-12 flex animate-settle flex-col gap-5">
      <p className="max-w-[85%] self-end rounded-[22px_22px_6px_22px] bg-ink px-[18px] py-3 whitespace-pre-wrap text-white">
        {turn.question}
      </p>
      <div className="grid grid-cols-[32px_1fr] gap-3 md:gap-4">
        <Icons.logo className="mt-0.5" />
        <div className="min-w-0">
          <p className="label">O Manu responde</p>
          <div className="mt-1.5">
            <ChatReply turn={turn} onRetry={onRetry} busy={busy} />
          </div>
        </div>
      </div>
    </article>
  );
}

const noteClass = "max-w-[62ch] rounded-2xl bg-paper px-[18px] py-4 shadow-card";
const noteTitleClass = "mb-1 font-display text-[18px] font-bold tracking-[-0.02em]";

function ChatReply({ turn, onRetry, busy }: ChatMessageProps) {
  if (turn.status === "loading") {
    return (
      <p className="inline-flex items-center gap-2.5 text-muted" role="status">
        <span aria-hidden="true" className="flex gap-1">
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              className="size-1.5 animate-pulse rounded-full bg-accent"
              style={{ animationDelay: `${delay}ms`, animationDuration: "900ms" }}
            />
          ))}
        </span>
        Procurando no manual…
      </p>
    );
  }

  if (turn.status === "error" || !turn.result) {
    return (
      <div className={noteClass} role="alert">
        <p className={`${noteTitleClass} text-alert`}>Não consegui consultar o manual.</p>
        <p className="leading-normal">A conexão com o servidor falhou. Sua pergunta continua aqui.</p>
        <Button variant="outline" size="sm" className="mt-3.5" onClick={onRetry} disabled={busy}>
          <Icons.retry /> Tentar de novo
        </Button>
      </div>
    );
  }

  const { result } = turn;
  if (result.refused) {
    return (
      <div className={noteClass}>
        <p className={noteTitleClass}>Isso não está no manual.</p>
        <p className="leading-normal">{result.answer}</p>
        <p className="mt-2 text-[13px] text-muted">Prefiro dizer que não sei a inventar uma resposta.</p>
      </div>
    );
  }

  const terms = questionTerms(turn.question);
  return (
    <>
      <p className="max-w-[62ch] text-[17px] leading-normal whitespace-pre-wrap text-pretty md:text-[19px]">
        {result.answer}
      </p>
      {result.citations.length > 0 && (
        <ol className="mt-5 grid gap-3.5" aria-label="Fontes">
          {result.citations.map((c) => (
            <li key={`${c.manual_id}:${c.page}`}>
              <figure className="grid grid-cols-[auto_1fr] items-start gap-3 md:gap-4">
                <p className="min-w-9 text-right font-display leading-none" aria-label={`Página ${c.page}`}>
                  <span className="block label font-bold">pág.</span>
                  <span className="text-[40px] font-extrabold tracking-[-0.05em] tabular-nums md:text-[48px]">{c.page}</span>
                </p>
                <blockquote className="rounded-2xl bg-paper px-4 py-3.5 shadow-card">
                  <p className="text-[15px] leading-relaxed">{highlight(c.excerpt, terms)}</p>
                  <footer className="mt-2 label">
                    Manual {c.brand} · {c.model}
                  </footer>
                  <details className="mt-2 text-xs text-muted">
                    <summary className="w-fit">Detalhes</summary>
                    Manual {c.manual_id} · similaridade {c.similarity.toFixed(2).replace(".", ",")}
                  </details>
                </blockquote>
              </figure>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
