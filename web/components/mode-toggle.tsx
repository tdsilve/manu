"use client";

import { useEffect, useState } from "react";
import { cva } from "class-variance-authority";
import { Icons } from "@/components/icons";
import { parseTheme, Theme, THEME_COOKIE } from "@/lib/theme";
import { cn } from "@/lib/utils";

function currentTheme(): Theme {
  const chosen = parseTheme(document.documentElement.dataset.theme);
  if (chosen) return chosen;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "night" : "day";
}

const segment = cva("", {
  variants: {
    size: {
      default: "h-8 w-[38px]",
      sm: "h-7 w-8",
    },
  },
  defaultVariants: { size: "default" },
});

export function ModeToggle({ className, size = "default" }: { className?: string; size?: "default" | "sm" }) {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    setTheme(currentTheme());
  }, []);

  function choose(next: Theme) {
    document.documentElement.dataset.theme = next;
    document.cookie = `${THEME_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    setTheme(next);
  }

  const item = cn(
    segment({ size }),
    "relative z-10 grid place-items-center rounded-full transition-colors duration-300",
  );

  return (
    <div
      data-slot="mode-toggle"
      className={cn("relative inline-grid grid-cols-2 rounded-full p-[3px] shadow-hairline", className)}
      role="group"
      aria-label="Tema"
    >
      <span
        aria-hidden="true"
        className={cn(
          segment({ size }),
          "absolute top-[3px] left-[3px] rounded-full bg-ink transition-transform duration-[420ms] ease-out night:translate-x-full",
        )}
      />
      <button
        type="button"
        aria-label="Dia"
        aria-pressed={theme === "day"}
        onClick={() => choose("day")}
        className={cn(item, "text-on-ink night:text-ink")}
      >
        <Icons.sun />
      </button>
      <button
        type="button"
        aria-label="Noite"
        aria-pressed={theme === "night"}
        onClick={() => choose("night")}
        className={cn(item, "text-ink night:text-on-ink")}
      >
        <Icons.moon />
      </button>
    </div>
  );
}
