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
  // O Manu em miniatura: manual com abas e rosto.
  logo: ({ className, ...props }: IconProps) => (
    <svg className={cn("size-8 shrink-0", className)} viewBox="0 0 32 32" fill="none" aria-hidden="true" {...props}>
      <rect x="24" y="7" width="4" height="5" rx="1.5" fill="#f2a07b" />
      <rect x="24" y="13" width="4" height="5" rx="1.5" fill="#f3b93a" />
      <rect x="24" y="19" width="4" height="5" rx="1.5" fill="#9fdcc4" />
      <rect x="3.5" y="4" width="5" height="25" rx="2" fill="#e2d6bf" />
      <rect x="6" y="4" width="20" height="24.5" rx="3" fill="#fffdf8" stroke="#1d1733" strokeOpacity=".14" />
      <circle cx="12.5" cy="14.5" r="2.4" fill="#1d1733" />
      <circle cx="19.5" cy="14.5" r="2.4" fill="#1d1733" />
      <path d="M13.8 19.2c1.2 1.5 3.3 1.5 4.5 0" stroke="#1d1733" strokeWidth="1.5" strokeLinecap="round" />
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
