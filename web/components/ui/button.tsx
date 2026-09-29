import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full text-[0.9375rem] transition-[background-color,color,box-shadow,transform] duration-200 ease-out active:not-disabled:translate-y-px disabled:cursor-not-allowed disabled:opacity-45 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-ink text-white hover:not-disabled:bg-[#2c2447]",
        outline:
          "bg-transparent shadow-[inset_0_0_0_1px_var(--line-strong)] hover:not-disabled:bg-ink hover:not-disabled:text-white hover:not-disabled:shadow-none",
        soft: "bg-paper/70 shadow-[inset_0_0_0_1px_var(--line)] hover:not-disabled:bg-paper",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-9 px-3.5 text-[0.8125rem]",
        icon: "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant,
  size,
  type = "button",
  ...props
}: ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return (
    <button
      type={type}
      data-slot="button"
      data-variant={variant ?? "default"}
      data-size={size ?? "default"}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
