"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Brand } from "@/components/brand";
import { ChatMessage, Turn } from "@/components/chat-message";
import { Icons } from "@/components/icons";
import { Mascot } from "@/components/mascot";
import { ModeToggle } from "@/components/mode-toggle";
import { QuestionDock, questionButtonClass, questionFieldClass } from "@/components/question-dock";
import { Button } from "@/components/ui/button";
import { ask } from "@/lib/ask";
import { EXAMPLES } from "@/lib/examples";
import { cn } from "@/lib/utils";

export function Chat({ initialQuestion }: { initialQuestion: string }) {
  const router = useRouter();
  const [draft, setDraft] = useState("");
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

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 flex items-center justify-between bg-linear-to-b from-field-top from-55% to-transparent px-(--gutter) py-[18px]">
        <Brand />
        <div className="flex items-center gap-3">
          <ModeToggle size="sm" className="max-md:hidden" />
          <Button variant="outline" size="sm" onClick={reset} disabled={turns.length === 0 || busy}>
            <Icons.plus /> Nova conversa
          </Button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[780px] flex-1 px-(--gutter) pt-3 pb-[180px]">
        {turns.length === 0 ? (
          <div className="flex min-h-[62dvh] flex-col items-center justify-center text-center">
            <Mascot className="mb-1 aspect-[1.08] w-[200px]" />
            <h1 className="text-[clamp(3rem,9vw,6rem)] leading-[0.92] font-light tracking-[-0.05em] text-balance text-display">
              Qual é a sua dúvida?
            </h1>
            <p className="mt-[22px] mb-[30px] max-w-[44ch] text-[1.0625rem] leading-[1.45] text-pretty">
              Pergunte do seu jeito sobre a geladeira ou o micro-ondas. A resposta vem do manual oficial, com a
              página.
            </p>
            <div className="flex max-w-[640px] flex-wrap justify-center gap-2" aria-label="Exemplos">
              {EXAMPLES.map((ex) => (
                <Button
                  key={ex.id}
                  variant="outline"
                  className="h-auto px-4 py-[9px] text-sm whitespace-normal"
                  onClick={() => submit(ex.question)}
                >
                  {ex.question}
                </Button>
              ))}
            </div>
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

      <div className="fixed inset-x-0 bottom-0 z-10 bg-linear-to-t from-field-bottom from-55% to-transparent px-(--gutter) pt-9 pb-3.5">
        <QuestionDock className="max-w-[780px]" onSubmit={onSubmit}>
          <label htmlFor="chat-q" className="sr-only">
            Sua dúvida
          </label>
          <textarea
            id="chat-q"
            ref={inputRef}
            rows={1}
            value={draft}
            maxLength={1000}
            autoFocus
            placeholder="Descreva sua dúvida…"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            className={cn(questionFieldClass, "field-sizing-content max-h-[200px] resize-none")}
          />
          <Button type="submit" size="icon" className={questionButtonClass} disabled={!canSubmit} aria-label="Perguntar">
            <Icons.arrowUp />
          </Button>
        </QuestionDock>
        <p className="mt-2.5 hidden text-center text-[0.6875rem] md:block">Enter envia · Shift + Enter quebra a linha</p>
      </div>
    </div>
  );
}
