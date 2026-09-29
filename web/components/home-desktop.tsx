"use client";

// Home em telas largas: à esquerda a prova (pergunta, resposta, página e trecho grifado),
// à direita o palco com o Manu grande, que pula a cada exemplo (3D com cursor, imagens no toque).

import Link from "next/link";
import { useState } from "react";
import { Honesty } from "@/components/honesty";
import { Icons } from "@/components/icons";
import { Manu } from "@/components/manu";
import { QUESTION_PLACEHOLDER, QuestionBar, questionFieldClass } from "@/components/question-bar";
import { Button } from "@/components/ui/button";
import { Wordmark } from "@/components/wordmark";
import { EXAMPLES, MANUAL } from "@/lib/examples";

const pad = (n: number) => String(n).padStart(2, "0");

export function HomeDesktop() {
  const [index, setIndex] = useState(0);
  const [hops, setHops] = useState(0);
  const [typing, setTyping] = useState(false);
  const example = EXAMPLES[index];
  const go = (d: number) => {
    setIndex((i) => (i + d + EXAMPLES.length) % EXAMPLES.length);
    setHops((n) => n + 1);
  };

  return (
    <div className="grid h-dvh grid-cols-[minmax(0,1fr)_minmax(0,1fr)] overflow-hidden">
      <main className="flex min-h-0 flex-col px-(--gutter) py-9">
        <Wordmark />

        <h1 className="mt-[6vh] font-display text-[clamp(40px,4.6vw,68px)] leading-[0.95] font-extrabold tracking-[-0.045em]">
          O manual responde.
          <br />
          <span className="text-accent">Com a página.</span>
        </h1>

        <section
          key={example.id}
          className="mt-9 max-w-[540px] animate-settle"
          aria-live="polite"
          aria-label={`Exemplo ${index + 1} de ${EXAMPLES.length}`}
        >
          <p className="label">Você pergunta</p>
          <p className="mt-1.5 text-[19px] leading-snug font-medium">{example.question}</p>
          <p className="mt-5 label">O Manu responde</p>
          <p className="mt-1.5 text-[19px] leading-snug">{example.answer}</p>

          <figure className="mt-5 grid grid-cols-[auto_1fr] items-start gap-4">
            <p className="text-right font-display leading-none" aria-label={`Página ${example.page}`}>
              <span className="block label font-bold">pág.</span>
              <span className="text-[52px] font-extrabold tracking-[-0.05em]">{example.page}</span>
            </p>
            <blockquote className="rounded-2xl bg-paper px-4 py-3.5 text-[15px] leading-relaxed shadow-card">
              <mark>{example.excerpt}</mark>
              <footer className="mt-2 label">
                Manual {MANUAL.brand} · {MANUAL.title}
              </footer>
            </blockquote>
          </figure>
          <Honesty className="mt-4" />
        </section>

        <div className="mt-auto flex items-center gap-3 pt-6">
          <Button variant="outline" size="icon" aria-label="Exemplo anterior" onClick={() => go(-1)}>
            <Icons.arrowLeft />
          </Button>
          <Button variant="outline" size="icon" aria-label="Próximo exemplo" onClick={() => go(1)}>
            <Icons.arrowRight />
          </Button>
          <span className="text-[13px] text-muted tabular-nums">
            {index + 1} / {EXAMPLES.length}
          </span>
          <Link
            href={`/chat?q=${encodeURIComponent(example.question)}`}
            className="ml-auto inline-flex items-center gap-1.5 text-[14px] underline decoration-line-strong underline-offset-4 hover:decoration-ink"
          >
            Perguntar isso no chat <Icons.arrowUpRight />
          </Link>
        </div>

        <QuestionBar action="/chat" className="mt-5">
          <label htmlFor="home-q" className="sr-only">
            Sua dúvida
          </label>
          <input
            id="home-q"
            name="q"
            required
            maxLength={1000}
            autoComplete="off"
            placeholder={QUESTION_PLACEHOLDER}
            onFocus={() => setTyping(true)}
            onBlur={(e) => setTyping(e.currentTarget.value.length > 0)}
            onChange={(e) => setTyping(e.currentTarget.value.length > 0 || document.activeElement === e.currentTarget)}
            className={questionFieldClass}
          />
          <Button type="submit" className="group h-11 px-5 font-display font-bold">
            Perguntar
            <Icons.arrowRight className="transition-transform duration-300 group-hover:translate-x-[3px]" />
          </Button>
        </QuestionBar>
      </main>

      <section className="relative m-3 ml-0 overflow-hidden rounded-[32px] stage" aria-hidden="true">
        <Manu
          framing="hero"
          bump={hops}
          excited={typing}
          className="absolute inset-0"
        />
        <p className="absolute top-7 right-8 label">
          Nº {pad(index + 1)} · {example.tab}
        </p>
      </section>
    </div>
  );
}
