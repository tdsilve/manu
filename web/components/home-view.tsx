"use client";

// Home: o Manu em evidência. O nome "manu." grande e centralizado, o botão para o chat
// logo abaixo e o mascote enorme ocupando a parte de baixo da tela, cortado na borda.
// Um layout só, que se ajusta à largura. Qual Manu aparece (3D ou imagens) depende do
// aparelho: ver components/manu.tsx.

import Link from "next/link";
import { useState } from "react";
import { Icons } from "@/components/icons";
import { Manu } from "@/components/manu";

export function HomeView() {
  const [eager, setEager] = useState(false);
  const [pokes, setPokes] = useState(0);
  const on = () => setEager(true);
  const off = () => setEager(false);

  return (
    <div className="relative h-dvh overflow-hidden stage">
      <Manu framing="giant" excited={eager} pokes={pokes} className="absolute inset-0" />

      {/* Toque no Manu (celular): brincadeira visual, fora da leitura de tela e do teclado. */}
      <button
        type="button"
        tabIndex={-1}
        aria-hidden="true"
        onClick={() => setPokes((n) => n + 1)}
        className="absolute inset-x-[20%] top-[46%] bottom-0"
      />

      {/* Cantos (desktop), como etiquetas de capa. */}
      <p className="absolute top-8 left-(--gutter) z-10 hidden max-w-[240px] font-display text-[22px] leading-[1.05] font-extrabold tracking-[-0.03em] md:block">
        A Manu responde.
        <br />
        <span className="text-accent">Direto da fonte.</span>
      </p>
      <div className="absolute top-8 right-(--gutter) z-10 hidden max-w-[260px] text-right md:block">
        <p className="label">Como funciona</p>
        <p className="mt-2 text-[15px] leading-snug">Pergunte do seu jeito. A resposta vem do manual oficial.</p>
      </div>

      <main className="pointer-events-none relative z-10 flex flex-col items-center px-(--gutter) pt-[7vh] text-center md:pt-[9vh]">
        <h1 className="font-display text-[clamp(88px,17vw,208px)] leading-[0.8] font-extrabold tracking-[-0.07em]">
          manu<span className="text-gold">.</span>
          <span className="sr-only">: responde direto da fonte.</span>
        </h1>
        <p className="mt-3 font-display text-[19px] leading-tight font-bold tracking-[-0.02em] md:hidden">
          A Manu responde. <span className="text-accent">Direto da fonte.</span>
        </p>
        <Link
          href="/chat"
          onPointerEnter={on}
          onPointerLeave={off}
          onFocus={on}
          onBlur={off}
          className="group pointer-events-auto mt-6 inline-flex h-14 items-center gap-2.5 rounded-full bg-ink px-7 font-display text-[17px] font-bold text-white shadow-bar transition-colors hover:bg-[#2c2447] md:mt-8"
        >
          Converse com a Manu
          <Icons.arrowRight className="transition-transform duration-300 group-hover:translate-x-[3px]" />
        </Link>
      </main>
    </div>
  );
}
