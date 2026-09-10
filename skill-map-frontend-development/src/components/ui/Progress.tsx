import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

export function ProgressBar({ value, className, barClassName, size = "md" }: { value: number; className?: string; barClassName?: string; size?: "sm" | "md" }) {
  return (
    <div className={cn("w-full overflow-hidden rounded-full bg-slate-100", size === "sm" ? "h-1.5" : "h-2.5", className)}>
      <div className={cn("h-full rounded-full bg-indigo-600 transition-all duration-700", barClassName)} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  );
}

export function ProgressRing({ value, size = 96, stroke = 8, color = "#4f46e5", label, sub, labelClassName }: { value: number; size?: number; stroke?: number; color?: string; label?: ReactNode; sub?: string; labelClassName?: string }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#e2e8f0" strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset} className="transition-all duration-700" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("text-xl font-bold text-slate-900", labelClassName)}>{label ?? `${value}%`}</span>
        {sub && <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{sub}</span>}
      </div>
    </div>
  );
}
