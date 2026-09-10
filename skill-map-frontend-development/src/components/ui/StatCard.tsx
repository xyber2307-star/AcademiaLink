import type { ReactNode } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "../../utils/cn";
import { Card } from "./Card";

export function StatCard({ label, value, icon, delta, hint, accent = "indigo" }: { label: string; value: string | number; icon: ReactNode; delta?: number; hint?: string; accent?: "indigo" | "emerald" | "amber" | "rose" | "sky" | "violet" }) {
  const accents = {
    indigo: "bg-indigo-50 text-indigo-600", emerald: "bg-emerald-50 text-emerald-600", amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600", sky: "bg-sky-50 text-sky-600", violet: "bg-violet-50 text-violet-600",
  };
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
        </div>
        <span className={cn("flex h-10 w-10 items-center justify-center rounded-xl", accents[accent])}>{icon}</span>
      </div>
      {(delta !== undefined || hint) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {delta !== undefined && (
            <span className={cn("inline-flex items-center gap-1 font-semibold", delta >= 0 ? "text-emerald-600" : "text-rose-600")}>
              {delta >= 0 ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
              {delta >= 0 ? "+" : ""}{delta}%
            </span>
          )}
          {hint && <span className="text-slate-500">{hint}</span>}
        </div>
      )}
    </Card>
  );
}
