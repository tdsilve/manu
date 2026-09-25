import type { ReactNode } from "react";
import { Icons } from "@/components/icons";
import { Button } from "@/components/ui/button";
import type { AskResponse } from "@/lib/ask";
import { cn } from "@/lib/utils";

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
    <article data-slot="chat-message" className="mb-12 flex animate-settle flex-col gap-[18px]">
      <p className="max-w-[80%] self-end rounded-[20px_20px_6px_20px] bg-ink px-[18px] py-[11px] whitespace-pre-wrap text-on-ink">
        {turn.question}
      </p>
      <div className="grid grid-cols-[22px_1fr] gap-3 md:grid-cols-[28px_1fr] md:gap-4">
        <Icons.logo className="mt-0.5 size-[22px] md:size-[26px]" />
        <div className="min-w-0">
          <ChatReply turn={turn} onRetry={onRetry} busy={busy} />
        </div>
      </div>
    </article>
  );
}

const noteClass = "max-w-[62ch] rounded-slip px-[18px] py-4 shadow-hairline";
const noteTitleClass = "mb-1 text-[1.0625rem] font-medium tracking-[-0.015em]";

function ChatReply({ turn, onRetry, busy }: ChatMessageProps) {
  if (turn.status === "loading") {
    return (
      <p className="mt-1 inline-flex items-center gap-3" role="status">
        <span
          aria-hidden="true"
          className="relative h-5 w-4 rounded-[2px] shadow-[inset_0_0_0_1.5px_currentColor] perspective-[60px] after:absolute after:inset-y-0 after:right-0 after:left-1/2 after:origin-left after:animate-thumb after:bg-current after:opacity-55 after:content-['']"
        />
        Procurando nos manuais…
      </p>
    );
  }

  if (turn.status === "error" || !turn.result) {
    return (
      <div className={noteClass} role="alert">
        <p className={cn(noteTitleClass, "text-alert")}>Não consegui consultar os manuais.</p>
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
        <p className={noteTitleClass}>Isso não está nos manuais.</p>
        <p className="leading-normal">{result.answer}</p>
      </div>
    );
  }

  const terms = questionTerms(turn.question);
  return (
    <>
      <p className="max-w-[62ch] text-[1.0625rem] leading-normal tracking-[-0.015em] whitespace-pre-wrap text-pretty md:text-[1.1875rem]">
        {result.answer}
      </p>
      {result.citations.length > 0 && (
        <ol className="mt-[26px] -ml-11 grid gap-3.5 md:-ml-[60px]" aria-label="Fontes">
          {result.citations.map((c) => (
            <li
              key={`${c.manual_id}:${c.page}`}
              className="grid grid-cols-[30px_1fr] items-start gap-3 md:grid-cols-[44px_1fr] md:gap-4"
            >
              <p
                className="flex flex-col items-end pt-2.5 text-[1.375rem] leading-none font-light tracking-[-0.04em] tabular-nums md:text-[1.75rem]"
                aria-label={`Página ${c.page}`}
              >
                <span className="mb-1 text-[0.5625rem] font-[450] tracking-[0.1em] uppercase">pág.</span>
                {c.page}
              </p>
              <div className="rounded-slip bg-paper px-[18px] pt-4 pb-3 text-paper-ink shadow-float">
                <p className="mb-2 text-[0.6875rem] tracking-[0.08em] text-paper-muted uppercase">
                  {c.brand} · {c.model}
                </p>
                <p className="text-[0.9375rem] leading-[1.55]">{highlight(c.excerpt, terms)}</p>
                <details className="mt-2.5 text-xs text-paper-muted">
                  <summary className="w-fit">Detalhes</summary>
                  Manual {c.manual_id} · similaridade {c.similarity.toFixed(2).replace(".", ",")}
                </details>
              </div>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
