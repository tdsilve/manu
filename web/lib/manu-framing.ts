// Enquadramento do Manu, compartilhado pelo 3D (manu-3d.tsx) e pelas imagens (manu-sprite.tsx),
// para as duas versões aparecerem exatamente no mesmo lugar e tamanho.
//
// Unidades da cena: o livro vai de y=-1,06 a y=1,06. TOP inclui a folga acima dele.
// giant: a home, com o Manu enorme e cortado na borda de baixo, o topo do livro abaixo do nome.
// hero: grande, cortado embaixo (palco lateral). compact: o Manu inteiro (palcos pequenos).

export const FOV = 26;
const TOP = 1.22;

export const FRAMINGS = {
  giant: { top: 0.44, bottom: -0.3, minHalfWidth: 1.3 },
  hero: { top: 0.24, bottom: -0.7, minHalfWidth: 1.1 },
  compact: { top: 0.05, bottom: -0.9, minHalfWidth: 1.6 },
} as const;

export type Framing = keyof typeof FRAMINGS;

// Meia-altura visível (H) e centro vertical (yc) da câmera para um palco com essa proporção.
export function frame(framing: Framing, aspect: number) {
  const f = FRAMINGS[framing];
  let H = (TOP - f.bottom) / (2 * (1 - f.top));
  if (H * aspect < f.minHalfWidth) H = f.minHalfWidth / aspect;
  return { H, yc: TOP - H + 2 * H * f.top };
}

// Câmera usada para renderizar as camadas em public/manu (imagens quadradas).
export const SPRITE_CAMERA = { H: 1.45, yc: 0.1 };

// Onde colocar a imagem quadrada do Manu num palco w×h para coincidir com o 3D.
export function spriteBox(framing: Framing, w: number, h: number) {
  const { H, yc } = frame(framing, w / h);
  const size = (h * SPRITE_CAMERA.H) / H;
  const centerY = (h * (yc + H - SPRITE_CAMERA.yc)) / (2 * H);
  return { left: w / 2 - size / 2, top: centerY - size / 2, size };
}
