"use client";

import { useSyncExternalStore } from "react";

// Aparelho com cursor (mouse ou trackpad), independente do tamanho da tela.
// Celulares e tablets respondem false: o toque não tem cursor para seguir.
const FINE = "(hover: hover) and (pointer: fine)";

const subscribe = (cb: () => void) => {
  const mq = window.matchMedia(FINE);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
};

// null no servidor e antes da hidratação.
export function useFinePointer(): boolean | null {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(FINE).matches,
    () => null,
  );
}
