"use client";

// O Manu em imagens: as camadas em public/manu foram renderizadas do próprio Manu 3D
// (manu-3d.tsx), então a aparência é a mesma, sem WebGL e sem three.js.
// Usado em aparelhos de toque e como imagem provisória enquanto o 3D carrega.
//
// Camadas (1000×1000, fundo transparente, mesma câmera): arm-left, arm-right, body, whites,
// pupils, brows, mouth; full.png é o Manu inteiro. Exportadas em pose neutra com a câmera
// SPRITE_CAMERA (lib/manu-framing.ts). Se o modelo 3D mudar, exporte de novo;
// manifest.json guarda ombros, olhos e boca em % da imagem.
// Com `framing`, a imagem é posicionada no palco exatamente onde o 3D apareceria.
//
// Sem laço de animação: respiração e piscada são CSS; olhar, pulo e cutucada só mexem em
// transform quando algo acontece.

import { useEffect, useRef, useState } from "react";
import { type Framing, spriteBox } from "@/lib/manu-framing";
import manifest from "@/public/manu/manifest.json";
import { cn } from "@/lib/utils";

type Gaze = { x: number; y: number } | null;

const M = manifest;
const [shoulderL, shoulderR] = M.shoulders;
const [eyeL, eyeR] = M.eyes;
const eyeY = eyeL.y;

const css = `
.ms { --gx: 0; --gy: 0; }
.ms-box { position: absolute; }
.ms-layer { position: absolute; inset: 0; width: 100%; height: 100%; user-select: none; -webkit-user-drag: none; }
.ms .pupil { transform: translate(calc(var(--gx) * ${M.pupilReach}%), calc(var(--gy) * -${M.pupilReach}%)); transition: transform 200ms cubic-bezier(.2,.8,.2,1); }
.ms .lean { transform-origin: 50% ${M.ground.y}%; transform: translateX(calc(var(--gx) * 1%)) rotate(calc(var(--gx) * 2deg)); transition: transform 700ms cubic-bezier(.2,.8,.2,1); }
.ms .rise { transition: transform 450ms cubic-bezier(.16,1,.3,1); }
.ms.excited .rise { transform: translateY(-3%); }
.ms .breathe { transform-origin: 50% ${M.ground.y}%; animation: ms-breathe 3.4s ease-in-out infinite; }
@keyframes ms-breathe { 0%,100% { transform: scale(1,1); } 50% { transform: scale(1.008,.99); } }
.ms .eyes { transform-origin: 50% ${eyeY}%; animation: ms-blink 5.2s infinite; }
@keyframes ms-blink { 0%,93%,100% { transform: scaleY(1); } 95.5% { transform: scaleY(.1); } }
.ms .eyes, .ms .happy { transition: opacity 120ms; }
.ms .happy { opacity: 0; }
.ms.joy .happy { opacity: 1; }
.ms.joy .eyes { opacity: 0; }
.ms .brows { transition: transform 300ms; }
.ms.excited .brows, .ms.joy .brows { transform: translateY(-${M.browLift}%); }
.ms .mouth { transform-origin: ${M.mouth.x}% ${M.mouth.y}%; transition: transform 300ms; }
.ms.excited .mouth, .ms.joy .mouth { transform: scale(1.15, 1.5); }
.ms .arm { transition: transform 420ms cubic-bezier(.16,1,.3,1); }
.ms .arm.l { transform-origin: ${shoulderL.x}% ${shoulderL.y}%; animation: ms-arm-l 3.4s ease-in-out infinite; }
.ms .arm.r { transform-origin: ${shoulderR.x}% ${shoulderR.y}%; animation: ms-arm-r 3.4s ease-in-out infinite; }
@keyframes ms-arm-l { 50% { transform: rotate(2.3deg); } }
@keyframes ms-arm-r { 50% { transform: rotate(-2.3deg); } }
.ms.excited .arm.l { animation: none; transform: rotate(14deg); }
.ms.excited .arm.r { animation: none; transform: rotate(-14deg); }
.ms.joy .arm.l { animation: none; transform: rotate(66deg); }
.ms.joy .arm.r { animation: none; transform: rotate(-66deg); }
@media (prefers-reduced-motion: reduce) { .ms *, .ms { animation: none !important; transition: none !important; } }
`;

const layer = (name: string) => `/manu/${name}.webp`;
const LAYER_COUNT = 7;

export function ManuSprite({
  bump = 0,
  pokes = 0,
  excited = false,
  gaze = null,
  followMouse = false,
  framing = "compact",
  className,
}: {
  bump?: number;
  pokes?: number;
  excited?: boolean;
  gaze?: Gaze;
  // Desktop (imagem provisória do 3D): os olhos seguem o cursor o tempo todo.
  followMouse?: boolean;
  framing?: Framing;
  className?: string;
}) {
  const rootRef = useRef<HTMLDivElement>(null);
  const boxRef = useRef<HTMLDivElement>(null);
  const bobRef = useRef<HTMLDivElement>(null);
  const wiggleRef = useRef<HTMLDivElement>(null);
  const [joy, setJoy] = useState(false);
  // Só aparece com todas as camadas carregadas: numa rede lenta, sem "olhos flutuando".
  const [loaded, setLoaded] = useState(0);
  const ready = loaded >= LAYER_COUNT;
  const [box, setBox] = useState<{ left: number; top: number; size: number } | null>(null);

  // Posição e tamanho no palco, iguais aos do 3D com o mesmo enquadramento.
  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const fit = () => el.clientWidth && el.clientHeight && setBox(spriteBox(framing, el.clientWidth, el.clientHeight));
    const watch = new ResizeObserver(fit);
    watch.observe(el);
    fit();
    return () => watch.disconnect();
  }, [framing]);
  const gazeRef = useRef<Gaze>(gaze);
  const busyUntil = useRef(0); // até quando o olhar está "ocupado" pelo dedo ou pelo mouse
  const first = useRef({ bump, pokes });

  const look = (x: number, y: number) => {
    const el = rootRef.current;
    if (!el) return;
    el.style.setProperty("--gx", x.toFixed(3));
    el.style.setProperty("--gy", y.toFixed(3));
  };

  // Olhar vindo da interface (deslize, campo em foco).
  useEffect(() => {
    gazeRef.current = gaze;
    if (gaze) look(gaze.x, gaze.y);
  }, [gaze?.x, gaze?.y, gaze === null]);

  // Olhar passeando + dedo na tela (ou mouse). Sem laço contínuo: só timers e eventos.
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let visible = true;
    let timer: ReturnType<typeof setTimeout>;
    let frame = 0;
    const io = new IntersectionObserver(([e]) => (visible = e.isIntersecting));
    if (rootRef.current) io.observe(rootRef.current);

    const wander = () => {
      timer = setTimeout(wander, 1400 + Math.random() * 2600);
      if (reduced || !visible || document.hidden || gazeRef.current || Date.now() < busyUntil.current) return;
      if (Math.random() < 0.35) look(0, 0);
      else look((Math.random() * 2 - 1) * 0.8, (Math.random() * 2 - 1) * 0.55);
    };
    timer = setTimeout(wander, 900);

    // Mira a partir do meio dos olhos, na posição real da imagem na tela.
    const toward = (cx: number, cy: number) => {
      const box = boxRef.current?.getBoundingClientRect();
      if (!box) return;
      const dx = cx - (box.left + (box.width * (eyeL.x + eyeR.x)) / 200);
      const dy = cy - (box.top + (box.height * eyeY) / 100);
      const d = Math.hypot(dx, dy) || 1;
      const reach = Math.min(1, d / 220);
      look((dx / d) * reach, (-dy / d) * reach);
    };
    let pressed = false;
    const onDown = (e: PointerEvent) => {
      pressed = true;
      if (gazeRef.current) return;
      busyUntil.current = Date.now() + 1800;
      toward(e.clientX, e.clientY);
    };
    const onMove = (e: PointerEvent) => {
      const mouse = followMouse && e.pointerType === "mouse";
      if ((!pressed && !mouse) || gazeRef.current) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        busyUntil.current = Date.now() + 1800;
        toward(e.clientX, e.clientY);
      });
    };
    const onUp = () => (pressed = false);
    window.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      clearTimeout(timer);
      cancelAnimationFrame(frame);
      io.disconnect();
      window.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
  }, [followMouse]);

  const still = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Pulinho a cada exemplo.
  useEffect(() => {
    if (bump === first.current.bump || still()) return;
    bobRef.current?.animate(
      [
        { transform: "translateY(0) scale(1,1)" },
        { transform: "translateY(0) scale(1.03,.96)", offset: 0.15 },
        { transform: "translateY(-7%) scale(.99,1.02)", offset: 0.5 },
        { transform: "translateY(0) scale(1.02,.98)", offset: 0.85 },
        { transform: "translateY(0) scale(1,1)" },
      ],
      { duration: 620, easing: "ease-out" },
    );
  }, [bump]);

  // Cutucada: chacoalha e fecha os olhinhos de alegria.
  useEffect(() => {
    if (pokes === first.current.pokes) return;
    setJoy(true);
    const t = setTimeout(() => setJoy(false), 800);
    if (!still()) {
      wiggleRef.current?.animate(
        [0, -5, 4, -3, 2, -1, 0].map((deg) => ({ transform: `rotate(${deg}deg)` })),
        { duration: 700, easing: "ease-out" },
      );
    }
    return () => clearTimeout(t);
  }, [pokes]);

  const img = (name: string, extra?: string) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={layer(name)}
      alt=""
      draggable={false}
      decoding="async"
      // Imagem já em cache pode terminar antes da hidratação: conta também pelo ref.
      ref={(el) => {
        if (el?.complete && el.naturalWidth && !el.dataset.counted) {
          el.dataset.counted = "1";
          setLoaded((n) => n + 1);
        }
      }}
      onLoad={(e) => {
        if (e.currentTarget.dataset.counted) return;
        e.currentTarget.dataset.counted = "1";
        setLoaded((n) => n + 1);
      }}
      className={cn("ms-layer", extra)}
    />
  );

  return (
    <div
      ref={rootRef}
      aria-hidden="true"
      className={cn("ms pointer-events-none", excited && "excited", joy && "joy", className)}
    >
      <style>{css}</style>
      <div
        ref={boxRef}
        className={cn("ms-box transition-opacity duration-500", !ready && "opacity-0")}
        style={box ? { left: box.left, top: box.top, width: box.size, height: box.size } : { visibility: "hidden" }}
      >
        <div ref={bobRef} className="ms-layer" style={{ transformOrigin: `50% ${M.ground.y}%` }}>
          <div className="ms-layer rise">
            <div ref={wiggleRef} className="ms-layer" style={{ transformOrigin: `50% ${M.ground.y}%` }}>
              <div className="ms-layer lean">
                <div className="ms-layer breathe">
                  {img("arm-left", "arm l")}
                  {img("arm-right", "arm r")}
                  {img("body")}
                  <div className="ms-layer eyes">
                    {img("whites")}
                    {img("pupils", "pupil")}
                  </div>
                  {/* Olhinhos de alegria (^ ^) no lugar dos olhos durante a cutucada. */}
                  <svg viewBox="0 0 100 100" className="ms-layer happy" fill="none">
                    {[eyeL, eyeR].map((e) => (
                      <path
                        key={e.x}
                        d={`M${e.x - M.eyeRadius * 0.8} ${e.y + 1} Q${e.x} ${e.y - M.eyeRadius * 0.9} ${e.x + M.eyeRadius * 0.8} ${e.y + 1}`}
                        stroke="#1d1733"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                      />
                    ))}
                  </svg>
                  {img("brows", "brows")}
                  {img("mouth", "mouth")}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
