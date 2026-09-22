import { Map } from "lucide-react";
import { cn } from "../../utils/cn";

export function Logo({ className, light = false, compact = false }: { className?: string; light?: boolean; compact?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-sky-600 shadow-md shadow-blue-300/50">
        <Map className="h-5 w-5 text-white" />
      </span>
      {!compact && (
        <div className="leading-tight">
          <span className={cn("block text-base font-extrabold tracking-tight", light ? "text-white" : "text-slate-900")}>AcademiaLink</span>
          <span className={cn("block text-[10px] font-medium uppercase tracking-widest", light ? "text-blue-200" : "text-slate-500")}>SIH26044</span>
        </div>
      )}
    </div>
  );
}
