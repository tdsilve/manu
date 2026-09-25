import type { ComponentProps } from "react";
import { Icons } from "@/components/icons";
import { cn } from "@/lib/utils";

// Barra de pergunta flutuante: orbe com o rosto do Manu + campo em pílula.
export function QuestionDock({
  className,
  formClassName,
  children,
  ...props
}: ComponentProps<"form"> & { formClassName?: string }) {
  return (
    <div data-slot="question-dock" className={cn("mx-auto flex w-full items-end gap-3", className)}>
      <span
        aria-hidden="true"
        className="hidden size-13 shrink-0 place-items-center rounded-full bg-paper text-paper-ink shadow-float md:grid"
      >
        <Icons.logo className="size-6" />
      </span>
      <form
        className={cn(
          "flex min-h-13 min-w-0 flex-1 items-end gap-2 rounded-[26px] bg-paper py-1.5 pr-1.5 pl-5 text-paper-ink shadow-float focus-within:shadow-[0_0_0_2px_var(--ink),var(--elevation-float)]",
          formClassName,
        )}
        {...props}
      >
        {children}
      </form>
    </div>
  );
}

// Campo e botão dentro da barra: tinta escura fixa sobre o papel, nos dois temas.
export const questionFieldClass =
  "min-w-0 flex-1 bg-transparent py-2.5 leading-[1.4] text-paper-ink outline-none placeholder:text-paper-muted";
export const questionButtonClass = "bg-paper-ink text-paper";
