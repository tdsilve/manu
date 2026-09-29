"use client";

// Escolhe o layout da home pela largura da tela (duas colunas ou tela única). Qual Manu
// aparece (3D ou imagens) depende do aparelho, não da largura: ver components/manu.tsx.

import dynamic from "next/dynamic";
import { useSyncExternalStore } from "react";
import { HomeMobile } from "@/components/home-mobile";

const HomeDesktop = dynamic(() => import("@/components/home-desktop").then((m) => m.HomeDesktop), { ssr: false });

const WIDE = "(min-width: 768px)";
const subscribe = (cb: () => void) => {
  const mq = window.matchMedia(WIDE);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
};

export function HomeView() {
  const wide = useSyncExternalStore(
    subscribe,
    () => window.matchMedia(WIDE).matches,
    () => null,
  );
  if (wide === null) return <div className="min-h-dvh" />;
  return wide ? <HomeDesktop /> : <HomeMobile />;
}
