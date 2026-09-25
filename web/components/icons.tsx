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
  // O rosto do mascote, um livrinho sorridente sem nada escrito.
  logo: ({ className, ...props }: IconProps) => (
    <svg className={cn("size-[30px] shrink-0", className)} viewBox="0 0 32 32" fill="none" aria-hidden="true" {...props}>
      <rect x="6" y="3.5" width="21" height="25" rx="4" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10.5 3.5v25" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="15.5" cy="14" r="1.6" fill="currentColor" />
      <circle cx="22" cy="14" r="1.6" fill="currentColor" />
      <path d="M16.3 18.6c.8 1.3 3.9 1.3 4.8 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
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
  sun: (props: IconProps) => (
    <svg {...base(16)} {...props}>
      <circle cx="8" cy="8" r="2.75" {...stroke} />
      <path
        d="M8 1.5v1.25M8 13.25v1.25M1.5 8h1.25M13.25 8h1.25M3.4 3.4l.9.9M11.7 11.7l.9.9M3.4 12.6l.9-.9M11.7 4.3l.9-.9"
        {...stroke}
      />
    </svg>
  ),
  moon: (props: IconProps) => (
    <svg {...base(16)} {...props}>
      <path d="M13.2 9.6A5.5 5.5 0 0 1 6.4 2.8a5.5 5.5 0 1 0 6.8 6.8Z" {...stroke} />
    </svg>
  ),
  retry: (props: IconProps) => (
    <svg {...base(14)} {...props}>
      <path d="M2.75 8a5.25 5.25 0 1 0 1.6-3.77M2.75 2.5v2.75H5.5" {...stroke} />
    </svg>
  ),
};
