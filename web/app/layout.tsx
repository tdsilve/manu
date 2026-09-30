import type { Metadata, Viewport } from "next";
import { display, sans } from "@/lib/fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "Manu",
  description: "Dúvidas sobre o seu eletrodoméstico, respondidas pelo manual oficial, com a página citada.",
  openGraph: {
    title: "Manu · o manual responde, direto da fonte",
    description: "Pergunte do seu jeito. A resposta vem do manual oficial, com o trecho e a página.",
    locale: "pt_BR",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#f8f6fc",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${sans.variable} ${display.variable}`}>
      <body>{children}</body>
    </html>
  );
}
