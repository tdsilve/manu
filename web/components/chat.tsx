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
import { AskError, ask } from "@/lib/ask";
import { applyFound, decide, productLabel, type Notice } from "@/lib/detection-flow";
import { EXAMPLES } from "@/lib/examples";
import { detectProducts, type SelectedProduct } from "@/lib/products";
import { cn } from "@/lib/utils";

const GONE_NOTICE: Notice = {
  kind: "unrecognized",
  text: "Esse aparelho não foi encontrado. Cite o modelo de novo na pergunta ou siga sem aparelho.",
};

const isBusy = (t: Turn) => t.status === "detecting" || t.status === "loading" || t.status === "choosing";

const chosenText = (p: SelectedProduct) => `Aparelho escolhido: ${p.code}, ${p.product.category} ${p.product.brand}`;

export function Chat({ initialQuestion }: { initialQuestion: string }) {
  const router = useRouter();
  const [draft, setDraft] = useState("");
  const [focused, setFocused] = useState(false);
  const finePointer = useFinePointer();
  const [turns, setTurns] = useState<Turn[]>([]);
  // A tela inicial (mascote e exemplos) vale até a primeira pergunta; "Nova conversa" fica na tela de conversa.
  const [started, setStarted] = useState(Boolean(initialQuestion));
  const [selected, setSelected] = useState<SelectedProduct | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const selectedRef = useRef<SelectedProduct | null>(null);
  // Sobe quando a pessoa tira o aparelho com a mão: uma detecção que começou antes é descartada.
  const manualChanges = useRef(0);
  // Sobe a cada conversa nova: respostas e detecções de uma conversa antiga são descartadas.
  const conversation = useRef(0);
  const nextId = useRef(0);
  const sentInitial = useRef(false);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const busy = turns.some(isBusy);
  const canSubmit = draft.trim().length > 0 && !busy;

  function patchTurn(id: number, patch: Partial<Turn>) {
    setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)));
  }

  function setProduct(next: SelectedProduct | null) {
    selectedRef.current = next;
    setSelected(next);
  }

  function say(next: Notice | null, announce: string) {
    setNotice(next);
    if (announce) setAnnouncement(announce);
  }

  // Pergunta ao /ask com o produto dado. O turno guarda esse produto para o "Tentar de novo".
  async function answer(id: number, question: string, product: SelectedProduct | null) {
    patchTurn(id, { status: "loading", sentWith: product });
    const thisConversation = conversation.current;
    try {
      const result = await ask(question, product);
      patchTurn(id, { status: "done", result });
    } catch (error) {
      if (conversation.current !== thisConversation) return;
      // 404 com produto: a API não conhece mais esse manual. Só limpa se ele ainda for o do turno.
      if (product && error instanceof AskError && error.status === 404) {
        if (selectedRef.current?.product.manual_id === product.product.manual_id) {
          setProduct(null);
          say(GONE_NOTICE, GONE_NOTICE.text);
        }
      }
      patchTurn(id, { status: "error" });
    }
  }

  // Cada pergunta passa pela detecção do modelo antes de ser respondida.
  async function send(question: string) {
    const id = nextId.current++;
    setStarted(true);
    setTurns((prev) => [...prev, { id, question, status: "detecting" }]);

    const changesAtStart = manualChanges.current;
    const thisConversation = conversation.current;
    const detection = await detectProducts(question);
    if (conversation.current !== thisConversation) return;

    // A pessoa mexeu no aparelho durante a detecção: a pergunta segue com o estado atual.
    if (manualChanges.current !== changesAtStart) {
      answer(id, question, selectedRef.current);
      return;
    }

    const before = selectedRef.current;
    const action = decide(detection, before);

    if (action.kind === "choose") {
      patchTurn(id, { status: "choosing", options: action.options, onlyCodes: action.onlyCodes });
      return;
    }

    const next = action.product;
    const changed = next?.product.manual_id !== before?.product.manual_id || next?.code !== before?.code;
    if (changed) setProduct(next);
    // Um aparelho novo sem aviso de troca é anunciado como escolhido; troca e "não reconheci" têm texto próprio.
    say(action.notice, action.notice?.text ?? (next && (changed || action.kind === "select") ? chosenText(next) : ""));

    if (action.kind === "select") {
      // Só o código, sem pergunta: o aparelho fica escolhido e a conversa não ganha bolha (AC-14).
      setTurns((prev) => prev.filter((t) => t.id !== id));
      inputRef.current?.focus();
      return;
    }
    answer(id, question, next);
  }

  // Escolha entre aparelhos (AC-16): vale como se a detecção tivesse achado só esse.
  function choose(turn: Turn, option: SelectedProduct | null) {
    if (!option) {
      setProduct(null);
      say(null, "Sem aparelho");
      if (turn.onlyCodes) patchTurn(turn.id, { status: "closed", resolution: "Sem aparelho." });
      else {
        patchTurn(turn.id, { resolution: "Sem aparelho" });
        answer(turn.id, turn.question, null);
      }
      return;
    }
    const { product, notice: switched } = applyFound(selectedRef.current, option);
    setProduct(product);
    say(switched, switched?.text ?? chosenText(product));
    if (turn.onlyCodes) {
      patchTurn(turn.id, { status: "closed", resolution: `Aparelho escolhido: ${productLabel(product)}. Agora é só perguntar.` });
      inputRef.current?.focus();
    } else {
      patchTurn(turn.id, { resolution: `Escolhido: ${productLabel(product)}` });
      answer(turn.id, turn.question, product);
    }
  }

  // Conversa nova: sem mensagens nem aparelho. `home` volta à tela inicial; senão fica na tela de conversa.
  // Nada do que ainda estiver a caminho vale. A API não guarda histórico, então não há memória a limpar.
  function newChat(home: boolean) {
    conversation.current++;
    manualChanges.current++;
    setTurns([]);
    setStarted(!home);
    setProduct(null);
    setDraft("");
    setNotice(null);
    setAnnouncement("Nova conversa");
    inputRef.current?.focus();
    window.scrollTo({ top: 0 });
  }

  function clearProduct() {
    manualChanges.current++;
    setProduct(null);
    say(null, "Sem aparelho");
    inputRef.current?.focus();
  }

  // Pergunta vinda da URL (?q=): passa pela mesma detecção, envia uma vez e limpa a URL.
  useEffect(() => {
    if (sentInitial.current || !initialQuestion) return;
    sentInitial.current = true;
    send(initialQuestion);
    router.replace("/");
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

  const empty = !started;

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 flex items-center bg-linear-to-b from-bg from-60% to-transparent px-(--gutter) pt-5 pb-6">
        <Wordmark
          onClick={(event) => {
            // Na própria página o link não recarrega nada: o clique reinicia a conversa.
            event.preventDefault();
            newChat(true);
          }}
        />
        {(started || selected) && (
          <Button variant="outline" size="sm" className="ml-auto" onClick={() => newChat(false)}>
            <Icons.plus /> Nova conversa
          </Button>
        )}
      </header>

      <main className="mx-auto w-full max-w-[760px] flex-1 px-(--gutter) pb-[250px]">
        {empty ? (
          <div className="flex min-h-[64dvh] flex-col items-center justify-center text-center">
            <div className="relative mb-4 h-[216px] w-full max-w-[520px] overflow-hidden md:h-[236px]">
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
              Pergunte do seu jeito. Se citar o modelo, como DB44, a resposta vem só do manual dele.
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
              <ChatMessage
                key={turn.id}
                turn={turn}
                onRetry={() => answer(turn.id, turn.question, turn.sentWith ?? null)}
                onChoose={(option) => choose(turn, option)}
                busy={busy}
              />
            ))}
          </div>
        )}
        <div ref={endRef} />
      </main>

      <div className="fixed inset-x-0 bottom-0 z-10 bg-linear-to-t from-bg from-60% to-transparent px-3 pt-10 pb-[max(14px,env(safe-area-inset-bottom))] md:px-(--gutter)">
        <p className="sr-only" aria-live="polite">
          {announcement}
        </p>
        {(selected || notice) && (
          <div className="mx-auto mb-2 flex max-w-[760px] flex-wrap items-center gap-x-2 gap-y-1.5 px-2" data-slot="product-bar">
            {selected && (
              <>
                <p className="min-w-0 truncate rounded-full bg-paper px-3.5 py-1.5 text-sm shadow-card" data-slot="product-chip">
                  <span className="font-bold">{selected.code}</span>
                  <span className="text-muted">
                    {" "}
                    · {selected.product.category} {selected.product.brand}
                  </span>
                </p>
                <Button variant="outline" size="sm" onClick={clearProduct}>
                  Tirar aparelho
                </Button>
              </>
            )}
            {notice && (
              <p role="status" className="text-[13px] text-muted">
                {notice.text}
              </p>
            )}
          </div>
        )}
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
            onChange={(e) => {
              setDraft(e.target.value);
              setNotice(null);
            }}
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
