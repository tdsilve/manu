import type { MouseEventHandler } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export function Wordmark({ className, onClick }: { className?: string; onClick?: MouseEventHandler<HTMLAnchorElement> }) {
  return (
    <Link
      href="/"
      onClick={onClick}
      aria-label="Manu, página inicial"
      className={cn("font-display text-[28px] leading-none font-extrabold tracking-[-0.06em]", className)}
    >
      manu<span className="text-gold">.</span>
    </Link>
  );
}
