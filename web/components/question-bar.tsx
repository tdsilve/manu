import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export const QUESTION_PLACEHOLDER = "Qual é a sua dúvida?";

// Barra de pergunta em pílula branca. O campo e o botão vão como filhos.
export function QuestionBar({ className, ...props }: ComponentProps<"form">) {
  return (
    <form
      data-slot="question-bar"
      className={cn(
        "flex min-h-14 w-full items-end gap-2 rounded-[28px] bg-paper py-1.5 pr-1.5 pl-5 shadow-bar transition-shadow focus-within:shadow-[0_0_0_2px_var(--ink),var(--shadow-bar)]",
        className,
      )}
      {...props}
    />
  );
}

export const questionFieldClass =
  "min-w-0 flex-1 self-center bg-transparent py-2.5 text-base leading-[1.4] outline-none placeholder:text-muted";
