import { Bricolage_Grotesque, Geist } from "next/font/google";

// Geist no texto corrido; Bricolage nos títulos, na marca e na arte do mascote.
export const sans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
export const display = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["500", "700", "800"],
  variable: "--font-bricolage",
});
