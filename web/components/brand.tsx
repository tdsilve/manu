import Link from "next/link";
import { Icons } from "@/components/icons";

export function Brand({ tagline }: { tagline?: string }) {
  return (
    <Link href="/" className="inline-flex items-center gap-3" aria-label="Manu, página inicial">
      <Icons.logo />
      <span>
        <span className="block text-lg leading-[1.1] tracking-[-0.025em]">Manu</span>
        {tagline && <span className="mt-[3px] block text-[0.625rem] font-[450] tracking-[0.08em] uppercase">{tagline}</span>}
      </span>
    </Link>
  );
}
