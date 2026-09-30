import { cn } from "@/lib/utils";

// A promessa do produto: se não está no manual, a Manu diz que não sabe.
export function Honesty({ className }: { className?: string }) {
  return (
    <p className={cn("flex items-center gap-2 text-[13px] text-muted", className)}>
      <svg viewBox="0 0 16 16" className="size-4 shrink-0" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="6.25" stroke="currentColor" strokeWidth="1.4" />
        <path d="M5.6 8.2 7.3 9.8l3.1-3.4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Não está no manual? A Manu diz que não sabe.
    </p>
  );
}
