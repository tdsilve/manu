"use client";

import Link from "next/link";
import { KeyboardEvent as ReactKeyboardEvent, useCallback, useEffect, useState } from "react";
import { Brand } from "@/components/brand";
import { Icons } from "@/components/icons";
import { Mascot } from "@/components/mascot";
import { ModeToggle } from "@/components/mode-toggle";
import { QuestionDock, questionButtonClass, questionFieldClass } from "@/components/question-dock";
import { Button } from "@/components/ui/button";
import { EXAMPLES } from "@/lib/examples";
import { cn } from "@/lib/utils";

const pad = (n: number) => String(n).padStart(2, "0");

const copyClass = "animate-settle text-[1.1875rem] leading-[1.3] tracking-[-0.02em] text-balance";

export function HomeView() {
  const [index, setIndex] = useState(0);
  const [hops, setHops] = useState(0);
  const example = EXAMPLES[index];
  const total = EXAMPLES.length;

  const go = useCallback(
    (to: number) => {
      setIndex((to + total) % total);
      setHops((n) => n + 1);
    },
    [total],
  );

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const el = event.target as HTMLElement;
      if (el.closest("input, textarea")) return;
      if (event.key === "ArrowRight") go(index + 1);
      if (event.key === "ArrowLeft") go(index - 1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, index]);

  function onTabsKey(event: ReactKeyboardEvent) {
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") event.stopPropagation();
  }

  return (
    <div className="flex min-h-dvh flex-col md:overflow-hidden">
      <header className="grid grid-cols-[1fr_auto] items-center gap-6 px-(--gutter) pt-5 md:pt-[26px] lg:grid-cols-[1fr_auto_1fr]">
        <Brand tagline="Respostas do manual oficial" />
        <nav className="hidden gap-7 lg:flex" aria-label="Exemplos" onKeyDown={onTabsKey}>
          {EXAMPLES.map((ex, i) => (
            <button
              key={ex.id}
              type="button"
              aria-pressed={i === index}
              onClick={() => i !== index && go(i)}
              className="border-b border-transparent py-1 text-sm transition-colors duration-[240ms] ease-out hover:border-ink-line aria-pressed:border-ink"
            >
              {ex.tab}
            </button>
          ))}
        </nav>
        <p className="hidden justify-self-end text-right text-xs leading-normal md:block">
          Pergunte do seu jeito.
          <br />
          Veja a página de onde veio.
        </p>
      </header>

      <section
        className="grid flex-1 grid-cols-1 px-(--gutter) pt-7 pb-2 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] md:grid-rows-[auto_1fr_auto] md:gap-x-8 md:pt-[2vh] md:pb-0"
        aria-roledescription="carrossel"
        aria-label="Exemplos de perguntas"
      >
        <h1 className="flex flex-col items-center text-center text-[clamp(3.25rem,17vw,5rem)] leading-[0.88] font-light tracking-[-0.055em] text-display md:col-span-full md:text-[clamp(3.5rem,min(11vw,15vh),9.5rem)]">
          <span>Pergunte</span>
          <span className="translate-x-[0.18em]">ao manual.</span>
        </h1>

        <div className="mt-3 flex items-center justify-center gap-1 md:col-start-2 md:row-start-2 md:mt-0 md:gap-[clamp(12px,3vw,48px)]">
          <Button variant="outline" size="icon-lg" aria-label="Exemplo anterior" onClick={() => go(index - 1)}>
            <Icons.arrowLeft />
          </Button>
          <Mascot bump={hops} className="aspect-[1.08] w-[min(58vw,260px)] md:w-[clamp(220px,min(28vw,44vh),440px)]" />
          <Button variant="outline" size="icon-lg" aria-label="Próximo exemplo" onClick={() => go(index + 1)}>
            <Icons.arrowRight />
          </Button>
        </div>

        <div
          className="mt-5 flex flex-col gap-3 md:col-start-1 md:row-start-2 md:mt-0 md:max-w-[300px] md:self-end md:justify-self-start md:pb-[4vh]"
          aria-live="polite"
        >
          <p className="micro">Pergunta</p>
          <p className={copyClass} key={`q-${example.id}`}>
            {example.question}
          </p>
          <Link
            href={`/chat?q=${encodeURIComponent(example.question)}`}
            className="mt-2 inline-flex items-center justify-between gap-10 self-start border-b border-ink-line pb-[7px] text-[0.8125rem] transition-colors duration-200 ease-out hover:border-ink"
          >
            Perguntar no chat <Icons.arrowUpRight />
          </Link>
        </div>

        <div
          className="mt-5 flex flex-col gap-3 border-t border-ink-hair pt-[18px] md:col-start-3 md:row-start-2 md:mt-0 md:max-w-[300px] md:items-end md:self-end md:justify-self-end md:border-t-0 md:pt-0 md:pb-[4vh] md:text-right"
          aria-live="polite"
        >
          <p className="micro">
            Nº {pad(index + 1)} / Página {example.page}
          </p>
          <p className={copyClass} key={`a-${example.id}`}>
            {example.answer}
          </p>
          <figure
            className="mt-2 animate-settle rounded-slip bg-paper px-3.5 pt-3 pb-2.5 text-left text-paper-ink shadow-float"
            key={`e-${example.id}`}
          >
            <blockquote className="text-[0.8125rem] leading-normal">
              <mark>{example.excerpt}</mark>
            </blockquote>
            <figcaption className="mt-2 text-[0.625rem] tracking-[0.08em] text-paper-muted uppercase">
              Manual Electrolux · Refrigeradores
            </figcaption>
          </figure>
        </div>

        <div className="mt-6 flex flex-col items-center gap-2.5 pb-2 md:col-span-full md:row-start-3 md:mt-0 md:pb-0">
          <ModeToggle />
          <p className="hidden text-xs whitespace-nowrap md:block">Trechos reais do manual oficial.</p>
        </div>
      </section>

      <QuestionDock
        action="/chat"
        className="sticky bottom-3 z-10 max-w-[680px] px-(--gutter) pt-[22px] md:static"
      >
        <label htmlFor="home-q" className="sr-only">
          Sua dúvida
        </label>
        <input
          id="home-q"
          name="q"
          maxLength={1000}
          autoComplete="off"
          placeholder="Descreva sua dúvida…"
          className={questionFieldClass}
        />
        <Button type="submit" className={cn(questionButtonClass, "max-md:px-3.5")}>
          Iniciar chat <Icons.arrowRight className="transition-transform duration-300 ease-out group-hover/button:translate-x-[3px]" />
        </Button>
      </QuestionDock>

      <footer className="flex justify-between gap-4 px-(--gutter) pt-[18px] pb-5 text-xs">
        <span className="inline-flex items-center gap-2 before:size-[5px] before:rounded-full before:bg-current before:content-['']">
          Só manuais oficiais
        </span>
        <span className="hidden md:inline">
          {index + 1} de {total}: {example.tab}
        </span>
      </footer>
    </div>
  );
}
