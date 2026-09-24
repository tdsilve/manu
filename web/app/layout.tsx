import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Manu",
  description: "Dúvidas sobre o seu eletrodoméstico, respondidas pelo manual oficial.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
