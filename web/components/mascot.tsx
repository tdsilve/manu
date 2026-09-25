"use client";

import { useEffect, useRef } from "react";
import type * as THREE_NS from "three";
import { cn } from "@/lib/utils";

type Props = {
  // Muda a cada troca de exemplo: o mascote dá um pulinho com giro.
  bump?: number;
  className?: string;
};

type Rig = {
  render: () => void;
  hop: () => void;
  dispose: () => void;
};

// Cores vêm das variáveis --mascot-* do globals.css; estes valores são só o fallback.
const FALLBACK = {
  cover: "#fbfaf6",
  spine: "#ece8de",
  pages: "#efe8d6",
  pageLine: "#ddd4bd",
  limb: "#1f3350",
  eye: "#171b26",
  blush: "#f3a3a6",
  mouth: "#3b1d2a",
  tongue: "#ef7f8c",
  glove: "#ffffff",
  sole: "#b9bfcc",
  ribbon: "#f2d65c",
};

type Palette = typeof FALLBACK;

const kebab = (key: string) => key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);

function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement);
  const palette = { ...FALLBACK };
  for (const key of Object.keys(FALLBACK) as (keyof Palette)[]) {
    const value = css.getPropertyValue(`--mascot-${kebab(key)}`).trim();
    if (value) palette[key] = value;
  }
  return palette;
}


// Monta o livrinho com primitivas. Tudo em unidades da cena: o livro tem 1,86 de altura.
async function buildScene(canvas: HTMLCanvasElement, reduced: boolean): Promise<Rig> {
  const THREE = await import("three");
  const { RoundedBoxGeometry } = await import("three/addons/geometries/RoundedBoxGeometry.js");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  camera.position.set(0, 0.15, 7.4);
  camera.lookAt(0, -0.2, 0);

  const hemi = new THREE.HemisphereLight("#ffffff", "#7391c2", 1.5);
  scene.add(hemi);
  const key = new THREE.DirectionalLight("#fff4e2", 2.2);
  key.position.set(-3.2, 4.5, 3.4);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.radius = 6;
  key.shadow.camera.left = -3;
  key.shadow.camera.right = 3;
  key.shadow.camera.top = 3;
  key.shadow.camera.bottom = -3;
  scene.add(key);
  const rim = new THREE.DirectionalLight("#c9d6ff", 1.1);
  rim.position.set(3, 2, -3);
  scene.add(rim);

  const clay = (color: string, roughness = 0.78) =>
    new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });

  const mat = {
    cover: clay(FALLBACK.cover),
    spine: clay(FALLBACK.spine),
    pages: clay(FALLBACK.pages, 0.95),
    pageLine: clay(FALLBACK.pageLine, 0.95),
    limb: clay(FALLBACK.limb, 0.7),
    eye: new THREE.MeshStandardMaterial({ color: FALLBACK.eye, roughness: 0.15 }),
    shine: new THREE.MeshBasicMaterial({ color: "#ffffff" }),
    blush: new THREE.MeshBasicMaterial({ color: FALLBACK.blush, transparent: true, opacity: 0.75 }),
    mouth: clay(FALLBACK.mouth, 0.5),
    tongue: clay(FALLBACK.tongue, 0.6),
    glove: clay(FALLBACK.glove, 0.85),
    sole: clay(FALLBACK.sole, 0.9),
    ribbon: clay(FALLBACK.ribbon, 0.6),
  };

  const mesh = (geometry: THREE_NS.BufferGeometry, material: THREE_NS.Material, shadow = true) => {
    const m = new THREE.Mesh(geometry, material);
    m.castShadow = shadow;
    return m;
  };

  // rig: pulo e giro. body: respiração. face: olha para o cursor.
  const rig = new THREE.Group();
  const body = new THREE.Group();
  rig.add(body);
  scene.add(rig);

  // Livro: capa de trás, miolo, capa da frente, lombada.
  const back = mesh(new RoundedBoxGeometry(1.38, 1.86, 0.1, 4, 0.05), mat.cover);
  back.position.z = -0.21;
  const block = mesh(new RoundedBoxGeometry(1.28, 1.76, 0.34, 2, 0.03), mat.pages);
  block.position.set(0.04, 0, 0);
  const front = mesh(new RoundedBoxGeometry(1.38, 1.86, 0.1, 4, 0.05), mat.cover);
  front.position.z = 0.21;
  const spine = mesh(new RoundedBoxGeometry(0.2, 1.86, 0.52, 4, 0.09), mat.spine);
  spine.position.x = -0.62;
  body.add(back, block, front, spine);

  // Riscas das folhas na borda do miolo.
  for (const z of [-0.1, 0, 0.1]) {
    const line = mesh(new THREE.BoxGeometry(0.012, 1.7, 0.012), mat.pageLine, false);
    line.position.set(0.685, 0, z);
    body.add(line);
  }

  // Fitinha de marcador saindo por cima, caída para trás.
  const ribbon = mesh(new RoundedBoxGeometry(0.1, 0.46, 0.02, 2, 0.008), mat.ribbon);
  ribbon.position.set(0.32, 1.08, -0.08);
  ribbon.rotation.x = -0.5;
  body.add(ribbon);

  // Rosto na capa.
  const face = new THREE.Group();
  face.position.z = 0.262;
  body.add(face);

  const eyes: THREE_NS.Group[] = [];
  for (const side of [-1, 1]) {
    const eye = new THREE.Group();
    eye.position.set(side * 0.25, 0.12, 0);
    const ball = mesh(new THREE.SphereGeometry(0.13, 32, 24), mat.eye, false);
    ball.scale.set(1, 1.22, 0.42);
    const shine = mesh(new THREE.SphereGeometry(0.038, 16, 12), mat.shine, false);
    shine.position.set(0.045, 0.06, 0.05);
    const shine2 = mesh(new THREE.SphereGeometry(0.018, 12, 8), mat.shine, false);
    shine2.position.set(-0.04, -0.05, 0.05);
    eye.add(ball, shine, shine2);
    face.add(eye);
    eyes.push(eye);

    const brow = mesh(new THREE.TorusGeometry(0.085, 0.014, 8, 24, Math.PI * 0.55), mat.limb, false);
    brow.position.set(side * 0.25 - 0.004, 0.33, 0);
    brow.rotation.z = Math.PI * 0.22;
    face.add(brow);

    const blush = mesh(new THREE.CircleGeometry(0.085, 32), mat.blush, false);
    blush.position.set(side * 0.44, -0.1, 0.002);
    blush.scale.set(1.25, 0.8, 1);
    face.add(blush);
  }

  const mouth = mesh(new THREE.CircleGeometry(0.1, 32, Math.PI, Math.PI), mat.mouth, false);
  mouth.position.set(0, -0.11, 0.003);
  mouth.scale.set(1, 0.95, 1);
  const tongue = mesh(new THREE.CircleGeometry(0.055, 24, Math.PI, Math.PI), mat.tongue, false);
  tongue.position.set(0, -0.155, 0.005);
  tongue.scale.set(1, 0.7, 1);
  face.add(mouth, tongue);

  // Braços com luvas. O pivô fica no ombro.
  const makeArm = (side: number) => {
    const shoulder = new THREE.Group();
    shoulder.position.set(side * 0.72, 0.05, 0.02);
    const arm = mesh(new THREE.CapsuleGeometry(0.065, 0.34, 8, 16), mat.limb);
    arm.position.y = -0.22;
    const hand = mesh(new THREE.SphereGeometry(0.13, 24, 16), mat.glove);
    hand.position.y = -0.47;
    hand.scale.set(1, 1.05, 0.85);
    const thumb = mesh(new THREE.SphereGeometry(0.055, 16, 12), mat.glove);
    thumb.position.set(-side * 0.1, -0.4, 0.06);
    shoulder.add(arm, hand, thumb);
    shoulder.rotation.z = side * 0.42;
    body.add(shoulder);
    return shoulder;
  };
  const armL = makeArm(-1);
  const armR = makeArm(1);

  // Pernas e tênis.
  for (const side of [-1, 1]) {
    const leg = mesh(new THREE.CapsuleGeometry(0.07, 0.24, 8, 16), mat.limb);
    leg.position.set(side * 0.28, -1.1, -0.02);
    const shoe = mesh(new THREE.SphereGeometry(0.17, 32, 16), mat.glove);
    shoe.scale.set(1.05, 0.62, 1.45);
    shoe.position.set(side * 0.3, -1.32, 0.07);
    const sole = mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.04, 32), mat.sole);
    sole.scale.set(1.05, 1, 1.45);
    sole.position.set(side * 0.3, -1.4, 0.07);
    rig.add(leg, shoe, sole);
  }

  // Chão que só recebe a sombra.
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(12, 12),
    new THREE.ShadowMaterial({ color: "#16283a", opacity: 0.22 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -1.42;
  ground.receiveShadow = true;
  scene.add(ground);

  // Tema: à noite a luz fica mais fria e baixa.
  // Tema e paleta: relê as variáveis CSS e ajusta luz e materiais.
  const applyTheme = () => {
    const palette = readPalette();
    for (const key of Object.keys(palette) as (keyof Palette)[]) mat[key].color.set(palette[key]);
    const root = document.documentElement.dataset.theme;
    const night =
      root === "night" || (!root && window.matchMedia("(prefers-color-scheme: dark)").matches);
    // À noite: luz fria e um pouco mais baixa, sem amarelar o papel.
    hemi.intensity = night ? 1.35 : 1.8;
    hemi.color.set(night ? "#dfe6ff" : "#ffffff");
    hemi.groundColor.set(night ? "#2a3558" : "#7391c2");
    key.intensity = night ? 2.2 : 2.6;
    key.color.set(night ? "#f4f1ff" : "#fff4e2");
    (ground.material as THREE_NS.ShadowMaterial).opacity = night ? 0.45 : 0.22;
    // Redesenha já: sem animação (movimento reduzido) nada mais atualizaria a tela.
    renderer.render(scene, camera);
  };
  applyTheme();
  const themeWatch = new MutationObserver(applyTheme);
  themeWatch.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme", "style", "class"],
  });

  // Tamanho segue o elemento.
  const resize = () => {
    const { clientWidth: w, clientHeight: h } = canvas;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  const sizeWatch = new ResizeObserver(() => {
    resize();
    if (reduced) renderer.render(scene, camera);
  });
  sizeWatch.observe(canvas);
  resize();

  // Cursor: o corpo vira na direção dele.
  const pointer = { x: 0, y: 0 };
  const onPointer = (e: PointerEvent) => {
    const r = canvas.getBoundingClientRect();
    pointer.x = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / (window.innerWidth / 2)));
    pointer.y = Math.max(-1, Math.min(1, (e.clientY - (r.top + r.height / 2)) / (window.innerHeight / 2)));
  };
  window.addEventListener("pointermove", onPointer);

  const timer = new THREE.Timer();
  const now = () => timer.getElapsed();
  let hopAt = -10;
  let waveAt = -10;
  let nextBlink = 1.5;
  let blinkAt = -10;
  const onEnter = () => (waveAt = now());
  canvas.addEventListener("pointerenter", onEnter);
  canvas.addEventListener("click", onEnter);

  const ease = (x: number) => 1 - Math.pow(1 - x, 3);

  const pose = (t: number) => {
    // Respira e balança.
    body.scale.set(1, 1 + Math.sin(t * 2.1) * 0.012, 1);
    rig.rotation.z = Math.sin(t * 1.2) * 0.025;

    // Olha para o cursor.
    const yaw = pointer.x * 0.5;
    const pitch = pointer.y * 0.18;
    rig.rotation.x += (pitch - rig.rotation.x) * 0.08;

    // Pulo com giro.
    const hp = (t - hopAt) / 0.7;
    if (hp >= 0 && hp < 1) {
      rig.position.y = Math.sin(hp * Math.PI) * 0.42;
      rig.rotation.y = yaw + ease(hp) * Math.PI * 2;
      const squash = hp > 0.85 ? 1 - Math.sin(((hp - 0.85) / 0.15) * Math.PI) * 0.06 : 1;
      body.scale.y *= squash;
    } else {
      rig.position.y = 0;
      rig.rotation.y += (yaw - (rig.rotation.y % (Math.PI * 2))) * 0.08;
    }

    // Braços: repouso ou aceno.
    const wp = (t - waveAt) / 1.8;
    const rest = Math.sin(t * 2.1 + 1) * 0.04;
    armL.rotation.z = -0.42 - rest;
    if (wp >= 0 && wp < 1) {
      const lift = Math.sin(Math.min(wp * 3, 1) * Math.PI * 0.5) * (1 - Math.max(0, wp - 0.8) * 5);
      armR.rotation.z = 0.42 + lift * 2.1 + Math.sin(wp * Math.PI * 8) * 0.28 * lift;
    } else {
      armR.rotation.z = 0.42 + rest;
    }

    // Piscada.
    if (t > nextBlink) {
      blinkAt = t;
      nextBlink = t + 2.2 + Math.random() * 3;
    }
    const bp = (t - blinkAt) / 0.16;
    const lid = bp >= 0 && bp < 1 ? 1 - Math.sin(bp * Math.PI) * 0.9 : 1;
    for (const eye of eyes) eye.scale.y = lid;
  };

  let frame = 0;
  let visible = true;
  const loop = () => {
    frame = requestAnimationFrame(loop);
    timer.update();
    if (!visible || document.hidden) return;
    pose(now());
    renderer.render(scene, camera);
  };
  const viewWatch = new IntersectionObserver(([entry]) => (visible = entry.isIntersecting));
  viewWatch.observe(canvas);

  // Primeiro quadro sempre, mesmo com a aba oculta.
  pose(0);
  renderer.render(scene, camera);
  if (!reduced) loop();

  return {
    render: () => renderer.render(scene, camera),
    hop: () => {
      if (!reduced) hopAt = now();
    },
    dispose: () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onPointer);
      canvas.removeEventListener("pointerenter", onEnter);
      canvas.removeEventListener("click", onEnter);
      themeWatch.disconnect();
      sizeWatch.disconnect();
      viewWatch.disconnect();
      scene.traverse((o) => {
        const m = o as THREE_NS.Mesh;
        m.geometry?.dispose();
      });
      Object.values(mat).forEach((m) => m.dispose());
      renderer.dispose();
      timer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}

// Manu, o mascote: um livrinho 3D sem nada escrito.
export function Mascot({ bump = 0, className }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const rigRef = useRef<Rig | null>(null);
  const firstBump = useRef(bump);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    // Um canvas por montagem: cada cena tem o próprio contexto WebGL.
    const canvas = document.createElement("canvas");
    host.appendChild(canvas);
    let cancelled = false;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    buildScene(canvas, reduced)
      .then((rig) => {
        if (cancelled) rig.dispose();
        else {
          rigRef.current = rig;
          canvas.dataset.ready = "true";
        }
      })
      .catch(() => {
        // Sem WebGL: o espaço fica vazio e o resto da página segue igual.
        canvas.remove();
      });
    return () => {
      cancelled = true;
      rigRef.current?.dispose();
      rigRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (bump !== firstBump.current) rigRef.current?.hop();
  }, [bump]);

  return (
    <div ref={hostRef} className={cn(
        "relative [&>canvas]:block [&>canvas]:size-full [&>canvas]:translate-y-3 [&>canvas]:scale-96 [&>canvas]:opacity-0 [&>canvas]:transition-[opacity,transform] [&>canvas]:duration-700 [&>canvas]:ease-out [&>canvas[data-ready]]:translate-y-0 [&>canvas[data-ready]]:scale-100 [&>canvas[data-ready]]:opacity-100",
        className,
      )} aria-hidden="true" />
  );
}
