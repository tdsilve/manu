import type { SVGProps } from "react";
import { cn } from "@/lib/utils";

type IconProps = SVGProps<SVGSVGElement>;

const stroke = {
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const base = (size: number): IconProps => ({
  width: size,
  height: size,
  viewBox: "0 0 16 16",
  fill: "none",
  "aria-hidden": true,
});

export const Icons = {
  // Símbolo A da marca: a Manu em miniatura (mesmo desenho de app/icon.svg).
  logo: ({ className, ...props }: IconProps) => (
    <svg className={cn("size-8 shrink-0", className)} viewBox="0 0 64 64" fill="none" aria-hidden="true" {...props}>
      <rect x="47" y="13" width="9" height="10" rx="3" fill="#f2a07b" />
      <rect x="47" y="25" width="9" height="10" rx="3" fill="#f3b93a" />
      <rect x="47" y="37" width="9" height="10" rx="3" fill="#9fdcc4" />
      <rect x="7" y="7" width="12" height="51" rx="5" fill="#e2d6bf" />
      <rect x="12" y="7" width="40" height="50" rx="7" fill="#fdfaf2" stroke="#1d1733" strokeOpacity=".12" />
      <ellipse cx="25" cy="29" rx="4.6" ry="5" fill="#1d1733" />
      <ellipse cx="39" cy="29" rx="4.6" ry="5" fill="#1d1733" />
      <circle cx="26.4" cy="27.3" r="1.4" fill="#fff" />
      <circle cx="40.4" cy="27.3" r="1.4" fill="#fff" />
      <ellipse cx="19.5" cy="37" rx="3.4" ry="2" fill="#f59bb5" opacity=".6" />
      <ellipse cx="44.5" cy="37" rx="3.4" ry="2" fill="#f59bb5" opacity=".6" />
      <path d="M27.5 37.5a4.5 4.5 0 0 0 9 0z" fill="#4a1f3a" />
    </svg>
  ),
  arrowRight: (props: IconProps) => (
    <svg {...base(16)} {...props}>
      <path d="M3 8h10M9 4l4 4-4 4" {...stroke} />
    </svg>
  ),
  arrowLeft: (props: IconProps) => (
    <svg {...base(16)} {...props}>
      <path d="M13 8H3M7 4 3 8l4 4" {...stroke} />
    </svg>
  ),
  arrowUpRight: (props: IconProps) => (
    <svg {...base(14)} {...props}>
      <path d="M5 11l6-6M6 5h5v5" {...stroke} />
    </svg>
  ),
  arrowUp: (props: IconProps) => (
    <svg {...base(18)} {...props}>
      <path d="M8 13V3M4 7l4-4 4 4" {...stroke} strokeWidth={1.6} />
    </svg>
  ),
  plus: (props: IconProps) => (
    <svg {...base(14)} {...props}>
      <path d="M8 3v10M3 8h10" {...stroke} />
    </svg>
  ),
  retry: (props: IconProps) => (
    <svg {...base(14)} {...props}>
      <path d="M2.75 8a5.25 5.25 0 1 0 1.6-3.77M2.75 2.5v2.75H5.5" {...stroke} />
    </svg>
  ),
};
