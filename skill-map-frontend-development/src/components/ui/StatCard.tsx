import type { ReactNode, ComponentType } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "../../utils/cn";
import { Card } from "./Card";

export function StatCard({
  label,
  title,
  value,
  icon,
  delta,
  hint,
  subtitle,
  accent = "indigo",
}: {
  label?: string;
  title?: string;
  value: string | number;
  icon: ReactNode | ComponentType<{ className?: string }>;
  delta?: number;
  hint?: string;
  subtitle?: string;
  accent?: "indigo" | "emerald" | "amber" | "rose" | "sky" | "violet" | "slate";
}) {
  const accents = {
    indigo: "bg-indigo-50 text-indigo-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600",
    sky: "bg-sky-50 text-sky-600",
    violet: "bg-violet-50 text-violet-600",
    slate: "bg-slate-100 text-slate-600",
  };

  const displayLabel = label || title || "";
  const displayHint = hint || subtitle;

  const renderIcon = () => {
    if (!icon) return null;
    // Already-created elements (e.g. icon={<Star />}) have .type/.props and render as-is.
    // Component types - plain functions, or lucide-react icons which are React.forwardRef
    // objects (typeof "object", shaped {$$typeof, render}) - need to be instantiated as JSX,
    // otherwise React throws "Objects are not valid as a React child".
    const isElement = typeof icon === "object" && icon !== null && "type" in (icon as object) && "props" in (icon as object);
    if (!isElement && (typeof icon === "function" || typeof icon === "object")) {
      const IconComponent = icon as ComponentType<{ className?: string }>;
      return <IconComponent className="h-5 w-5" />;
    }
    return icon as ReactNode;
  };

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium tracking-wide text-slate-500">{displayLabel}</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
        </div>
        <span className={cn("flex h-10 w-10 items-center justify-center rounded-xl", accents[accent])}>
          {renderIcon()}
        </span>
      </div>
      {(delta !== undefined || displayHint) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {delta !== undefined && (
            <span
              className={cn(
                "inline-flex items-center gap-1 font-semibold",
                delta >= 0 ? "text-emerald-600" : "text-rose-600"
              )}
            >
              {delta >= 0 ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
              {delta >= 0 ? "+" : ""}
              {delta}%
            </span>
          )}
          {displayHint && <span className="text-slate-500">{displayHint}</span>}
        </div>
      )}
    </Card>
  );
}
