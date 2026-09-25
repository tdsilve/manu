import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// Ensina ao tailwind-merge os tokens próprios, para não confundi-los com cores.
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      shadow: ["float", "hairline", "hairline-strong", "button", "button-hover"],
      radius: ["slip"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
