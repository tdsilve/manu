"use client";

// Home em telas estreitas: uma tela só, sem rolagem. Palco com o Manu em cima, exemplos
// em cartões de deslizar no meio, pergunta na zona do polegar.
// No celular o Manu é feito de imagens do 3D e tem olhar próprio: acompanha o cartão que desliza, olha para
// o campo quando a pessoa vai digitar e se alegra quando é tocado. Numa janela estreita de
// computador ele é o 3D, que segue o mouse.

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Honesty } from "@/components/honesty";
import { Icons } from "@/components/icons";
import { Manu } from "@/components/manu";
import { QUESTION_PLACEHOLDER, QuestionBar, questionFieldClass } from "@/components/question-bar";
import { Button } from "@/components/ui/button";
import { Wordmark } from "@/components/wordmark";
import { EXAMPLES, MANUAL } from "@/lib/examples";
import { cn } from "@/lib/utils";

const pad = (n: number) => String(n).padStart(2, "0");

export function HomeMobile() {
  const [index, setIndex] = useState(0);
  const [hops, setHops] = useState(0);
  const [pokes, setPokes] = useState(0);
  const [focused, setFocused] = useState(false);
  const [text, setText] = useState("");
  const [glance, setGlance] = useState<{ x: number; y: number } | null>(null);
  const railRef = useRef<HTMLDivElement>(null);
  const lastLeft = useRef(0);
  const settle = useRef<ReturnType<typeof setTimeout>>(undefined);
  const scrollFrame = useRef(0);

  useEffect(
    () => () => {
      clearTimeout(settle.current);
      cancelAnimationFrame(scrollFrame.current);
    },
    [],
  );

  // No máximo uma atualização por quadro enquanto desliza.
  function onScroll() {
    if (scrollFrame.current) return;
    scrollFrame.current = requestAnimationFrame(() => {
      scrollFrame.current = 0;
      const rail = railRef.current;
      if (!rail) return;
      // Deslizando: olha para o lado do movimento; parou: olha para o cartão e volta.
      const dir = Math.sign(rail.scrollLeft - lastLeft.current);
      lastLeft.current = rail.scrollLeft;
      if (dir) setGlance({ x: dir * 0.9, y: -0.35 });
      clearTimeout(settle.current);
      settle.current = setTimeout(() => {
        setGlance({ x: 0, y: -0.95 });
        settle.current = setTimeout(() => setGlance(null), 1100);
      }, 140);
      const i = Math.round(rail.scrollLeft / rail.clientWidth);
      if (i !== index) {
        setIndex(i);
        setHops((n) => n + 1);
      }
    });
  }

  function goTo(i: number) {
    const rail = railRef.current;
    rail?.scrollTo({ left: i * rail.clientWidth, behavior: "smooth" });
  }

  // Digitando: olha para o campo, bem embaixo.
  const gaze = focused ? { x: 0, y: -1 } : glance;

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <section className="relative mx-2 mt-2 h-[44dvh] shrink-0 overflow-hidden rounded-[28px] stage">
        <Manu
          bump={hops}
          pokes={pokes}
          gaze={gaze}
          excited={focused || text.length > 0}
          className="absolute inset-x-0 top-[112px] bottom-2"
        />
        {/* Toque no Manu: brincadeira visual, fora da leitura de tela e do teclado. */}
        <button
          type="button"
          tabIndex={-1}
          aria-hidden="true"
          onClick={() => setPokes((n) => n + 1)}
          className="absolute inset-x-[14%] top-[112px] bottom-0 rounded-t-[40px]"
        />
        <div className="relative flex items-start justify-between px-5 pt-4">
          <Wordmark className="text-[26px]" />
          <span className="pt-2 label tabular-nums">
            {pad(index + 1)} / {pad(EXAMPLES.length)}
          </span>
        </div>
        <h1 className="relative mt-3 px-5 font-display text-[30px] leading-[0.95] font-extrabold tracking-[-0.045em]">
          O manual responde.
          <br />
          <span className="text-accent">Com a página.</span>
        </h1>
      </section>

      <div
        ref={railRef}
        onScroll={onScroll}
        className="flex min-h-0 flex-1 snap-x snap-mandatory overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        aria-roledescription="carrossel"
        aria-label="Exemplos de perguntas"
      >
        {EXAMPLES.map((ex, i) => (
          <article
            key={ex.id}
            className="flex w-full shrink-0 snap-center flex-col overflow-y-auto px-5 pt-5"
            aria-label={`Exemplo ${i + 1} de ${EXAMPLES.length}`}
          >
            <p className="label">Você pergunta</p>
            <p className="mt-1 text-[18px] leading-snug font-semibold">{ex.question}</p>
            <p className="mt-3 text-[16px] leading-snug">{ex.answer}</p>
            <figure className="mt-3 grid grid-cols-[auto_1fr] items-start gap-3">
              <p className="text-right font-display leading-none" aria-label={`Página ${ex.page}`}>
                <span className="block label font-bold">pág.</span>
                <span className="text-[40px] font-extrabold tracking-[-0.05em]">{ex.page}</span>
              </p>
              <blockquote className="rounded-2xl bg-paper px-3.5 py-3 text-[14px] leading-relaxed shadow-card">
                <mark>{ex.excerpt}</mark>
                <footer className="mt-1.5 label">
                  Manual {MANUAL.brand} · {MANUAL.title}
                </footer>
              </blockquote>
            </figure>
            <Honesty className="mt-3" />
            <Link
              href={`/chat?q=${encodeURIComponent(ex.question)}`}
              className="mt-2 mb-2 inline-flex min-h-11 items-center gap-1.5 self-start text-[15px] font-medium underline decoration-line-strong underline-offset-4"
            >
              Perguntar isso no chat <Icons.arrowUpRight />
            </Link>
          </article>
        ))}
      </div>

      <div className="shrink-0 px-3 pt-1 pb-[max(12px,env(safe-area-inset-bottom))]">
        <div className="mb-2 flex justify-center gap-1" role="tablist" aria-label="Escolher exemplo">
          {EXAMPLES.map((ex, i) => (
            <button
              key={ex.id}
              type="button"
              role="tab"
              aria-selected={i === index}
              aria-label={ex.tab}
              onClick={() => goTo(i)}
              className="grid size-6 place-items-center"
            >
              <span
                className={cn(
                  "block h-1.5 rounded-full bg-ink transition-all duration-300",
                  i === index ? "w-4" : "w-1.5 opacity-30",
                )}
              />
            </button>
          ))}
        </div>
        <QuestionBar action="/chat">
          <label htmlFor="home-q-mobile" className="sr-only">
            Sua dúvida
          </label>
          <input
            id="home-q-mobile"
            name="q"
            required
            maxLength={1000}
            autoComplete="off"
            enterKeyHint="send"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={QUESTION_PLACEHOLDER}
            className={questionFieldClass}
          />
          <Button type="submit" size="icon" aria-label="Perguntar">
            <Icons.arrowUp />
          </Button>
        </QuestionBar>
      </div>
    </div>
  );
}
