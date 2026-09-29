"use client";

// O Manu certo para cada aparelho, em qualquer tamanho de tela:
// - com cursor (computador, mesmo com a janela estreita): 3D que segue o mouse. Até o 3D
//   ficar pronto, ou se não houver WebGL, aparecem as imagens do Manu no mesmo lugar;
// - sem cursor (celular, tablet): as imagens do Manu (renderizadas do próprio 3D, mesma
//   aparência), leves, com olhar próprio e reação ao toque.
// As duas versões usam o mesmo enquadramento (lib/manu-framing.ts), então coincidem.

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { ManuSprite } from "@/components/manu-sprite";
import type { Framing } from "@/lib/manu-framing";
import { useFinePointer } from "@/lib/use-pointer";
import { cn } from "@/lib/utils";

const Manu3D = dynamic(() => import("@/components/manu-3d").then((m) => m.Manu3D), { ssr: false });

type Gaze = { x: number; y: number } | null;

export function Manu({
  framing = "compact",
  bump = 0,
  pokes = 0,
  gaze = null,
  excited = false,
  className,
}: {
  framing?: Framing;
  bump?: number;
  pokes?: number;
  gaze?: Gaze;
  excited?: boolean;
  // Posição do palco do Manu (ex.: "absolute inset-0").
  className?: string;
}) {
  const fine = useFinePointer();
  const [ready, setReady] = useState(false);
  const [posterGone, setPosterGone] = useState(false);

  // Some com as imagens depois do fade, para elas não ficarem rodando por baixo do 3D.
  useEffect(() => {
    if (!ready) return;
    const t = setTimeout(() => setPosterGone(true), 800);
    return () => clearTimeout(t);
  }, [ready]);

  if (fine === null) return null;

  if (!fine) {
    return <ManuSprite framing={framing} bump={bump} pokes={pokes} gaze={gaze} excited={excited} className={className} />;
  }

  return (
    <div className={cn("pointer-events-none", className)}>
      {!posterGone && (
        <ManuSprite
          followMouse
          framing={framing}
          bump={bump}
          gaze={gaze}
          excited={excited}
          className={cn("absolute inset-0 transition-opacity duration-700", ready && "opacity-0")}
        />
      )}
      <Manu3D
        framing={framing}
        bump={bump}
        excited={excited}
        onReady={() => setReady(true)}
        className="absolute inset-0"
      />
    </div>
  );
}
