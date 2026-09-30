"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useFinePointer } from "@/lib/use-pointer";
import { ChatMessage, Turn } from "@/components/chat-message";
import { Honesty } from "@/components/honesty";
import { Icons } from "@/components/icons";
import { Manu } from "@/components/manu";
import { QUESTION_PLACEHOLDER, QuestionBar, questionFieldClass } from "@/components/question-bar";
import { Button } from "@/components/ui/button";
import { Wordmark } from "@/components/wordmark";
import { ask } from "@/lib/ask";
import { EXAMPLES } from "@/lib/examples";
import { cn } from "@/lib/utils";

export function Chat({ initialQuestion }: { initialQuestion: string }) {
  const router = useRouter();
  const [draft, setDraft] = useState("");
  const [focused, setFocused] = useState(false);
  const finePointer = useFinePointer();
  const [turns, setTurns] = useState<Turn[]>([]);
  const nextId = useRef(0);
  const sentInitial = useRef(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const busy = turns.some((t) => t.status === "loading");
  const canSubmit = draft.trim().length > 0 && !busy;

  async function send(question: string, retryId?: number) {
    const id = retryId ?? nextId.current++;
    setTurns((prev) =>
      retryId === undefined
        ? [...prev, { id, question, status: "loading" }]
        : prev.map((t) => (t.id === id ? { ...t, status: "loading" } : t)),
    );
    try {
      const result = await ask(question);
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: "done", result } : t)));
    } catch {
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: "error" } : t)));
    }
  }

  // Pergunta vinda da home (?q=): envia uma vez e limpa a URL.
  useEffect(() => {
    if (sentInitial.current || !initialQuestion) return;
    sentInitial.current = true;
    send(initialQuestion);
    router.replace("/chat");
  }, [initialQuestion, router]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  function submit(question: string) {
    const asked = question.trim();
    if (!asked || busy) return;
    setDraft("");
    send(asked);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    submit(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit(draft);
    }
  }

  function reset() {
    setTurns([]);
    setDraft("");
    inputRef.current?.focus();
  }

  const empty = turns.length === 0;

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 flex items-center justify-between bg-linear-to-b from-bg from-60% to-transparent px-(--gutter) pt-5 pb-6">
        <Wordmark />
        <Button variant="outline" size="sm" onClick={reset} disabled={empty || busy}>
          <Icons.plus /> Nova conversa
        </Button>
      </header>

      <main className="mx-auto w-full max-w-[760px] flex-1 px-(--gutter) pb-[180px]">
        {empty ? (
          <div className="flex min-h-[64dvh] flex-col items-center justify-center text-center">
            <div className="relative mb-4 h-[216px] w-full max-w-[520px] overflow-hidden rounded-[28px] stage md:h-[236px]">
              <Manu
                gaze={focused ? { x: 0, y: -1 } : null}
                excited={focused || draft.length > 0}
                className="absolute inset-x-0 top-5 bottom-2"
              />
            </div>
            <h1 className="font-display text-[clamp(40px,7vw,72px)] leading-[0.95] font-extrabold tracking-[-0.045em] text-balance">
              Qual é a sua dúvida?
            </h1>
            <p className="mt-4 max-w-[44ch] text-[17px] leading-snug text-muted text-pretty">
              Pergunte do seu jeito. A resposta vem do manual oficial, com a página.
            </p>
            <div className="mt-7 flex max-w-[640px] flex-wrap justify-center gap-2" aria-label="Exemplos">
              {EXAMPLES.map((ex) => (
                <Button
                  key={ex.id}
                  variant="soft"
                  className="h-auto min-h-10 px-4 py-2 text-left text-sm whitespace-normal"
                  onClick={() => submit(ex.question)}
                >
                  {ex.question}
                </Button>
              ))}
            </div>
            <Honesty className="mt-6" />
          </div>
        ) : (
          <div aria-live="polite">
            {turns.map((turn) => (
              <ChatMessage key={turn.id} turn={turn} onRetry={() => send(turn.question, turn.id)} busy={busy} />
            ))}
          </div>
        )}
        <div ref={endRef} />
      </main>

      <div className="fixed inset-x-0 bottom-0 z-10 bg-linear-to-t from-bg from-60% to-transparent px-3 pt-10 pb-[max(14px,env(safe-area-inset-bottom))] md:px-(--gutter)">
        <QuestionBar className="mx-auto max-w-[760px]" onSubmit={onSubmit}>
          <label htmlFor="chat-q" className="sr-only">
            Sua dúvida
          </label>
          <textarea
            id="chat-q"
            ref={inputRef}
            rows={1}
            value={draft}
            maxLength={1000}
            autoFocus={finePointer === true}
            enterKeyHint="send"
            placeholder={QUESTION_PLACEHOLDER}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            className={cn(questionFieldClass, "field-sizing-content max-h-[200px] resize-none")}
          />
          <Button type="submit" size="icon" disabled={!canSubmit} aria-label="Perguntar">
            <Icons.arrowUp />
          </Button>
        </QuestionBar>
        <p className="mt-2.5 hidden text-center text-xs text-muted md:block">Enter envia · Shift + Enter quebra a linha</p>
      </div>
    </div>
  );
}
