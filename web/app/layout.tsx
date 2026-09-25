import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import { cookies } from "next/headers";
import { parseTheme, THEME_COOKIE } from "@/lib/theme";
import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "Manu",
  description: "Dúvidas sobre o seu eletrodoméstico, respondidas pelo manual oficial, com a página citada.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#7391c2" },
    { media: "(prefers-color-scheme: dark)", color: "#111a30" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Tema escolhido pela pessoa; sem cookie, o CSS segue o sistema.
  const theme = parseTheme((await cookies()).get(THEME_COOKIE)?.value);
  return (
    <html lang="pt-BR" className={sans.variable} data-theme={theme}>
      <body>{children}</body>
    </html>
  );
}
