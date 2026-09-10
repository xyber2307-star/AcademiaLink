import { CheckCircle2 } from "lucide-react";
import { cn } from "../../utils/cn";

export function SkillBadge({ name, score, verified, className }: { name: string; score?: number; verified?: boolean; className?: string }) {
  const tone = score === undefined ? "bg-slate-100 text-slate-700" : score >= 75 ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : score >= 55 ? "bg-amber-50 text-amber-700 ring-amber-200" : "bg-rose-50 text-rose-700 ring-rose-200";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium ring-1 ring-inset ring-slate-200", tone, className)}>
      {verified && <CheckCircle2 className="h-3.5 w-3.5" />}
      {name}
      {score !== undefined && <span className="rounded-md bg-white/70 px-1.5 py-px text-[10px] font-semibold">{score}</span>}
    </span>
  );
}
