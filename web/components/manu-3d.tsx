"use client";

// O Manu 3D: manual com abas que segue o cursor com os olhos. Só é baixado em aparelhos
// com cursor (ver components/manu.tsx). Pausa fora da tela e com a aba escondida;
// avisa com onReady quando o primeiro quadro está pronto (até lá aparecem as imagens do Manu).

import { useEffect, useRef } from "react";
import type * as THREE_NS from "three";
import { display } from "@/lib/fonts";
import { FOV, frame as frameCamera, type Framing } from "@/lib/manu-framing";
import { cn } from "@/lib/utils";

const INK = "#1d1733";
const PAPER = "#fbf8f1";
const PAGES = "#efe6d2";
const SPINE = "#e2d6bf";
const COVER_SHADE = "#ece3d1";
const MARK = "#f8e38a";

const RISE = 0.1;

type G = CanvasRenderingContext2D;
const font = (px: number, weight = 700) => `${weight} ${Math.round(px)}px ${display.style.fontFamily}`;

// Folha de papel com grão, desenhada em canvas para virar textura.
function sheet(wu: number, hu: number, draw: (g: G, W: number, H: number) => void, bg = PAPER) {
  const W = 1024;
  const H = Math.round((W * hu) / wu);
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const g = c.getContext("2d")!;
  g.fillStyle = bg;
  g.fillRect(0, 0, W, H);
  for (let i = 0; i < 5000; i++) {
    g.fillStyle = `rgba(70,50,30,${Math.random() * 0.04})`;
    g.fillRect(Math.random() * W, Math.random() * H, 2, 2);
  }
  g.lineCap = "round";
  g.lineJoin = "round";
  draw(g, W, H);
  return c;
}

function fridge(g: G, x: number, y: number, w: number, h: number) {
  g.strokeStyle = INK;
  g.lineWidth = w * 0.07;
  g.beginPath();
  g.roundRect(x, y, w, h, w * 0.14);
  g.moveTo(x, y + h * 0.36);
  g.lineTo(x + w, y + h * 0.36);
  g.moveTo(x + w * 0.78, y + h * 0.12);
  g.lineTo(x + w * 0.78, y + h * 0.26);
  g.moveTo(x + w * 0.78, y + h * 0.46);
  g.lineTo(x + w * 0.78, y + h * 0.64);
  g.stroke();
}

type Rig = { hop: () => void; setExcited: (v: boolean) => void; dispose: () => void };

async function build(canvas: HTMLCanvasElement, framing: Framing, reduced: boolean, onReady: () => void): Promise<Rig> {
  const THREE = await import("three");
  const { RoundedBoxGeometry: RB } = await import("three/addons/geometries/RoundedBoxGeometry.js");
  await document.fonts.load(font(40)).catch(() => {});

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 60);

  scene.add(new THREE.HemisphereLight("#ffffff", "#b7a9e6", 1.9));
  const key = new THREE.DirectionalLight("#fff3e4", 2.2);
  key.position.set(-2.5, 4, 5);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.radius = 8;
  key.shadow.bias = -0.0005;
  key.shadow.normalBias = 0.03;
  scene.add(key);
  const rim = new THREE.DirectionalLight("#e4dcff", 1.6);
  rim.position.set(3, 2.5, -3);
  scene.add(rim);

  const textures: THREE_NS.Texture[] = [];
  const materials: THREE_NS.Material[] = [];
  const keep = <M extends THREE_NS.Material>(m: M) => (materials.push(m), m);
  const solid = (color: string, roughness = 0.8) => keep(new THREE.MeshStandardMaterial({ color, roughness }));
  const mesh = (geo: THREE_NS.BufferGeometry, m: THREE_NS.Material, cast = true, receive = true) => {
    const o = new THREE.Mesh(geo, m);
    o.castShadow = cast;
    o.receiveShadow = receive;
    return o;
  };
  // Arte impressa: plano na frente da superfície, com polygonOffset para não tremer.
  const decal = (wu: number, hu: number, art: HTMLCanvasElement) => {
    const t = new THREE.CanvasTexture(art);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    textures.push(t);
    const material = new THREE.MeshStandardMaterial({
      map: t,
      roughness: 0.85,
      polygonOffset: true,
      polygonOffsetFactor: -4,
      polygonOffsetUnits: -4,
    });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(wu, hu), keep(material));
    m.receiveShadow = true;
    return m;
  };

  const rig = new THREE.Group();
  const body = new THREE.Group();
  rig.add(body);
  scene.add(rig);

  // Livro: contracapa, miolo, capa e lombada (maior que as capas: sem faces no mesmo plano).
  const back = mesh(new RB(1.72, 2.12, 0.12, 4, 0.05), solid(COVER_SHADE, 0.85));
  back.position.z = -0.25;
  const pages = mesh(new RB(1.6, 2.02, 0.42, 3, 0.04), solid(PAGES, 0.95));
  pages.position.x = 0.04;
  const front = mesh(new RB(1.72, 2.12, 0.12, 4, 0.05), solid(PAPER, 0.85));
  front.position.z = 0.25;
  const spine = mesh(new RB(0.26, 2.15, 0.68, 4, 0.1), solid(SPINE, 0.85));
  spine.position.x = -0.76;
  body.add(back, pages, front, spine);

  for (const [y, color] of [
    [0.66, "#f2a07b"],
    [0.3, "#f3b93a"],
    [-0.06, "#f59bb5"],
    [-0.42, "#9fdcc4"],
  ] as const) {
    const tab = mesh(new RB(0.26, 0.22, 0.03, 2, 0.012), solid(color, 0.7));
    tab.position.set(0.88, y, 0.05 - (y + 0.5) * 0.08);
    body.add(tab);
  }

  const cover = decal(1.46, 1.96, sheet(1.46, 1.96, (g, W, H) => fridge(g, W * 0.07, H * 0.84, W * 0.1, H * 0.11)));
  cover.position.set(0.06, 0, 0.316);
  body.add(cover);

  const note = decal(
    0.44,
    0.44,
    sheet(
      0.44,
      0.44,
      (g, W, H) => {
        g.save();
        g.translate(W * 0.5, H * 0.55);
        g.rotate(-0.08);
        g.font = font(W * 0.24);
        g.fillStyle = INK;
        g.textAlign = "center";
        g.fillText("pág. 5", 0, 0);
        g.restore();
        g.strokeStyle = INK;
        g.lineWidth = W * 0.035;
        g.beginPath();
        g.moveTo(W * 0.3, H * 0.72);
        g.quadraticCurveTo(W * 0.5, H * 0.8, W * 0.72, H * 0.7);
        g.stroke();
      },
      MARK,
    ),
  );
  note.position.set(0.5, -0.66, 0.326);
  note.rotation.z = -0.14;
  body.add(note);

  // Rosto.
  const face = new THREE.Group();
  face.position.set(0.02, 0.08, 0.32);
  face.scale.setScalar(0.9);
  body.add(face);
  const sclera = keep(new THREE.MeshPhysicalMaterial({ color: "#ffffff", roughness: 0.3, clearcoat: 0.8 }));
  const pupilMat = keep(new THREE.MeshPhysicalMaterial({ color: "#15121f", roughness: 0.1, clearcoat: 1 }));
  const shineMat = keep(new THREE.MeshBasicMaterial({ color: "#ffffff" }));
  const inkMat = solid(INK, 0.7);
  const blushMat = keep(new THREE.MeshBasicMaterial({ color: "#f59bb5", transparent: true, opacity: 0.55 }));

  const eyes: THREE_NS.Group[] = [];
  const pupils: THREE_NS.Group[] = [];
  const brows: THREE_NS.Mesh[] = [];
  for (const side of [-1, 1]) {
    const eye = new THREE.Group();
    eye.position.set(side * 0.3, 0.14, 0);
    const white = mesh(new THREE.SphereGeometry(0.21, 40, 28), sclera, true, false);
    white.scale.set(1, 1.08, 0.55);
    const pupil = new THREE.Group();
    const ball = mesh(new THREE.SphereGeometry(0.115, 32, 24), pupilMat, false, false);
    ball.scale.set(1, 1.08, 0.5);
    const shine = mesh(new THREE.SphereGeometry(0.03, 16, 12), shineMat, false, false);
    shine.position.set(0.04, 0.045, 0.05);
    pupil.add(ball, shine);
    pupil.position.z = 0.085;
    eye.add(white, pupil);
    face.add(eye);
    eyes.push(eye);
    pupils.push(pupil);

    const brow = mesh(new THREE.TorusGeometry(0.11, 0.022, 12, 28, Math.PI * 0.6), inkMat, true, false);
    brow.position.set(side * 0.3, 0.44, 0);
    brow.rotation.z = Math.PI * 0.2 + side * 0.12;
    face.add(brow);
    brows.push(brow);

    const blush = mesh(new THREE.CircleGeometry(0.1, 32), blushMat, false, false);
    blush.position.set(side * 0.55, -0.12, 0.005);
    blush.scale.set(1.3, 0.75, 1);
    face.add(blush);
  }
  const mouth = new THREE.Group();
  mouth.position.set(0, -0.14, 0.005);
  mouth.add(mesh(new THREE.CircleGeometry(0.13, 36, Math.PI, Math.PI), solid("#4a1f3a", 0.9), false, false));
  const tongue = mesh(new THREE.CircleGeometry(0.075, 28, Math.PI, Math.PI), solid("#f07f9a", 0.8), false, false);
  tongue.position.set(0, -0.055, 0.002);
  tongue.scale.set(1, 0.75, 1);
  mouth.add(tongue);
  face.add(mouth);

  // Braços finos com luvas brancas.
  const glove = solid("#ffffff", 0.8);
  const arms: THREE_NS.Group[] = [];
  for (const side of [-1, 1]) {
    const shoulder = new THREE.Group();
    shoulder.position.set(side * 0.86, -0.1, 0.05);
    const arm = mesh(new THREE.CapsuleGeometry(0.05, 0.32, 8, 16), inkMat);
    arm.position.y = -0.2;
    const hand = mesh(new THREE.SphereGeometry(0.14, 28, 20), glove);
    hand.position.y = -0.45;
    hand.scale.set(1, 1.05, 0.85);
    const thumb = mesh(new THREE.SphereGeometry(0.06, 16, 12), glove);
    thumb.position.set(-side * 0.11, -0.38, 0.05);
    shoulder.add(arm, hand, thumb);
    shoulder.rotation.z = side * 0.5;
    body.add(shoulder);
    arms.push(shoulder);
  }

  const resize = () => {
    const { clientWidth: w, clientHeight: h } = canvas;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    const aspect = w / h;
    const { H, yc } = frameCamera(framing, aspect);
    camera.aspect = aspect;
    camera.position.set(0, yc, H / Math.tan((FOV / 2) * (Math.PI / 180)));
    camera.lookAt(0, yc, 0);
    camera.updateProjectionMatrix();
  };
  const sizeWatch = new ResizeObserver(() => {
    resize();
    renderer.render(scene, camera);
  });
  sizeWatch.observe(canvas);
  resize();

  const mouse = { x: window.innerWidth / 2, y: window.innerHeight * 0.3 };
  const look = { x: 0, y: 0 };
  const tmp = new THREE.Vector3();
  let excited = 0;
  let excitedTarget = 0;
  let hopAt = -10;
  let blinkAt = -10;
  let nextBlink = 1.2;
  const timer = new THREE.Timer();

  const pose = (t: number, k = 0.14) => {
    // Olhos miram o cursor a partir da posição real do rosto na tela.
    face.getWorldPosition(tmp).project(camera);
    const r = canvas.getBoundingClientRect();
    const dx = mouse.x - (r.left + ((tmp.x + 1) / 2) * r.width);
    const dy = mouse.y - (r.top + ((1 - tmp.y) / 2) * r.height);
    const dist = Math.hypot(dx, dy) || 1;
    const reach = Math.min(1, dist / 280);
    look.x += ((dx / dist) * reach - look.x) * k;
    look.y += ((-dy / dist) * reach - look.y) * k;
    for (const p of pupils) p.position.set(look.x * 0.08, look.y * 0.08, 0.085);

    excited += (excitedTarget - excited) * 0.08;
    rig.rotation.y += (look.x * 0.22 - rig.rotation.y) * 0.06;
    rig.rotation.x += (-look.y * 0.08 - rig.rotation.x) * 0.06;
    rig.rotation.z = Math.sin(t * 1.1) * 0.02;
    body.scale.set(1, 1 + Math.sin(t * 2) * 0.01, 1);

    const hp = (t - hopAt) / 0.6;
    rig.position.y = excited * RISE + (hp >= 0 && hp < 1 ? Math.sin(hp * Math.PI) * 0.16 : 0);

    for (const b of brows) b.position.y = 0.44 + excited * 0.06;
    mouth.scale.set(1 + excited * 0.15, 1 + excited * 0.5, 1);
    const sway = Math.sin(t * 2 + 1) * 0.04;
    arms[0].rotation.z = -0.5 - sway - excited * 0.25;
    arms[1].rotation.z = 0.5 + sway + excited * 0.25;

    if (t > nextBlink) {
      blinkAt = t;
      nextBlink = t + 2.4 + Math.random() * 3;
    }
    const bp = (t - blinkAt) / 0.16;
    const lid = bp >= 0 && bp < 1 ? 1 - Math.sin(bp * Math.PI) * 0.9 : 1;
    for (const e of eyes) e.scale.y = lid;
  };

  const draw = (t: number, k?: number) => {
    pose(t, k);
    renderer.render(scene, camera);
  };

  const onPointer = (e: PointerEvent) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    if (reduced) draw(0, 1);
  };
  window.addEventListener("pointermove", onPointer);

  // Laço só enquanto o palco está visível e a aba está aberta.
  let frame = 0;
  let visible = true;
  const loop = () => {
    frame = requestAnimationFrame(loop);
    timer.update();
    draw(timer.getElapsed());
  };
  const sync = () => {
    cancelAnimationFrame(frame);
    frame = 0;
    if (!reduced && visible && !document.hidden) loop();
  };
  const viewWatch = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    sync();
  });
  viewWatch.observe(canvas);
  document.addEventListener("visibilitychange", sync);

  draw(0, 1);
  onReady();
  sync();

  return {
    hop: () => {
      if (!reduced) hopAt = timer.getElapsed();
    },
    setExcited: (v) => {
      excitedTarget = v ? 1 : 0;
      if (reduced) {
        excited = excitedTarget;
        draw(0, 1);
      }
    },
    dispose: () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", sync);
      viewWatch.disconnect();
      sizeWatch.disconnect();
      scene.traverse((o) => (o as THREE_NS.Mesh).geometry?.dispose());
      materials.forEach((m) => m.dispose());
      textures.forEach((t) => t.dispose());
      timer.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}

export function Manu3D({
  framing = "hero",
  bump = 0,
  excited = false,
  onReady,
  className,
}: {
  framing?: Framing;
  bump?: number;
  excited?: boolean;
  onReady?: () => void;
  className?: string;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const rigRef = useRef<Rig | null>(null);
  const firstBump = useRef(bump);
  const latest = useRef({ excited, onReady });
  latest.current = { excited, onReady };

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const canvas = document.createElement("canvas");
    host.appendChild(canvas);
    let cancelled = false;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const ready = () => {
      canvas.dataset.ready = "true";
      latest.current.onReady?.();
    };
    build(canvas, framing, reduced, ready)
      .then((rig) => {
        if (cancelled) return rig.dispose();
        rigRef.current = rig;
        rig.setExcited(latest.current.excited);
      })
      .catch(() => {
        // Sem WebGL: as imagens do Manu continuam no lugar.
        canvas.remove();
      });
    return () => {
      cancelled = true;
      rigRef.current?.dispose();
      rigRef.current = null;
    };
  }, [framing]);

  useEffect(() => {
    if (bump !== firstBump.current) rigRef.current?.hop();
  }, [bump]);

  useEffect(() => {
    rigRef.current?.setExcited(excited);
  }, [excited]);

  return (
    <div
      ref={hostRef}
      aria-hidden="true"
      className={cn(
        "pointer-events-none [&>canvas]:block [&>canvas]:size-full [&>canvas]:opacity-0 [&>canvas]:transition-opacity [&>canvas]:duration-700 [&>canvas[data-ready]]:opacity-100",
        className,
      )}
    />
  );
}
