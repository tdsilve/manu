import { readFile } from "node:fs/promises";
import path from "node:path";
import { ImageResponse } from "next/og";

// Imagem de compartilhamento (WhatsApp, LinkedIn…): título + o Manu renderizado do 3D (public/manu/full.png).

export const alt = "Manu: o manual responde, direto da fonte.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INK = "#1d1733";

// Bricolage (500 e 800) do Google Fonts, em TTF, formato que o gerador aceita.
// Sem rede, a imagem sai com a fonte padrão.
async function loadFont(weight: 500 | 800): Promise<ArrayBuffer | null> {
  try {
    const css = await fetch(`https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@${weight}`, {
      headers: { "User-Agent": "Mozilla/5.0" },
    }).then((r) => r.text());
    const url = css.match(/src: url\((.+?)\) format\('(?:truetype|opentype)'\)/)?.[1];
    return url ? await fetch(url).then((r) => r.arrayBuffer()) : null;
  } catch {
    return null;
  }
}

export default async function OpengraphImage() {
  const [regular, bold] = await Promise.all([loadFont(500), loadFont(800)]);
  const fonts =
    regular && bold
      ? [
          { name: "Bricolage", data: regular, weight: 500 as const, style: "normal" as const },
          { name: "Bricolage", data: bold, weight: 800 as const, style: "normal" as const },
        ]
      : undefined;
  const heading = fonts ? { fontFamily: "Bricolage" } : {};
  const manu = await readFile(path.join(process.cwd(), "public", "manu", "full.png"));
  const src = `data:image/png;base64,${manu.toString("base64")}`;
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          background: "#f8f6fc",
          color: INK,
          padding: "0 72px",
          gap: 48,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
          <div style={{ ...heading, display: "flex", fontSize: 44, fontWeight: 800, letterSpacing: -2 }}>
            manu<span style={{ color: "#f3b93a" }}>.</span>
          </div>
          <div style={{ ...heading, marginTop: 56, fontSize: 76, fontWeight: 800, lineHeight: 1, letterSpacing: -3 }}>
            O manual responde.
          </div>
          <div style={{ ...heading, fontSize: 76, fontWeight: 800, lineHeight: 1.05, letterSpacing: -3, color: "#6b57c7" }}>
            Direto da fonte.
          </div>
          <div style={{ ...heading, marginTop: 36, fontSize: 28, fontWeight: 500, color: "#56516a" }}>
            Pergunte do seu jeito. A resposta vem do manual oficial.
          </div>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            width: 460,
            height: 520,
            borderRadius: 40,
            background: "radial-gradient(85% 65% at 50% 100%, #c9bcf2 0%, #ddd4f7 55%, #ebe6fa 100%)",
            overflow: "hidden",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={src} width={470} height={470} alt="" />
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
