export type Theme = "day" | "night";

export const THEME_COOKIE = "manu-theme";

export function parseTheme(value: string | undefined): Theme | undefined {
  return value === "day" || value === "night" ? value : undefined;
}
