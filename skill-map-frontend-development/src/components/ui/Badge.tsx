import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

type Tone = "indigo" | "emerald" | "amber" | "rose" | "slate" | "sky" | "violet";
const tones: Record<Tone, string> = {
  indigo: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  emerald: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  amber: "bg-amber-50 text-amber-700 ring-amber-200",
  rose: "bg-rose-50 text-rose-700 ring-rose-200",
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
  sky: "bg-sky-50 text-sky-700 ring-sky-200",
  violet: "bg-violet-50 text-violet-700 ring-violet-200",
};

export function Badge({
  tone = "slate",
  variant,
  className,
  children,
}: {
  tone?: Tone;
  variant?: string;
  className?: string;
  children: ReactNode;
}) {
  const effectiveTone: Tone = (variant && variant in tones ? (variant as Tone) : tone);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        tones[effectiveTone] || tones.slate,
        className
      )}
    >
      {children}
    </span>
  );
}

