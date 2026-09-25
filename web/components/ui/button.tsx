import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full text-[0.9375rem] transition-[background-color,color,box-shadow,transform] duration-200 ease-out active:not-disabled:translate-y-px disabled:cursor-not-allowed disabled:opacity-45 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-ink text-on-ink shadow-button hover:not-disabled:shadow-button-hover",
        outline: "bg-transparent shadow-hairline hover:not-disabled:bg-ink-hair hover:not-disabled:shadow-hairline-strong",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-[34px] px-3.5 text-[0.8125rem]",
        icon: "size-10",
        "icon-lg": "size-11 md:size-12",
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
