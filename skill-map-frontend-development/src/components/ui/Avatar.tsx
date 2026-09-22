import { cn } from "../../utils/cn";
import { initials } from "../../utils/format";

export function Avatar({ src, name, size = "md", className }: { src?: string; name: string; size?: "sm" | "md" | "lg" | "xl"; className?: string }) {
  const s = { sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-14 w-14 text-base", xl: "h-24 w-24 text-2xl" }[size];
  return src ? (
    <img src={src} alt={name} className={cn("rounded-full object-cover ring-2 ring-white", s, className)} />
  ) : (
    <span className={cn("inline-flex items-center justify-center rounded-full bg-blue-100 font-semibold text-blue-700 ring-2 ring-white", s, className)}>{initials(name)}</span>
  );
}
