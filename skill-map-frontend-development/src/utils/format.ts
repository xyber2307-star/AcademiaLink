import type { ApplicationStatus } from "../types";

export const statusColor: Record<ApplicationStatus, string> = {
  Applied: "bg-slate-100 text-slate-700 ring-slate-200",
  Shortlisted: "bg-sky-50 text-sky-700 ring-sky-200",
  Interview: "bg-amber-50 text-amber-700 ring-amber-200",
  Offered: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  Rejected: "bg-rose-50 text-rose-700 ring-rose-200",
};

export const priorityColor = {
  High: "bg-rose-50 text-rose-700 ring-rose-200",
  Medium: "bg-amber-50 text-amber-700 ring-amber-200",
  Low: "bg-emerald-50 text-emerald-700 ring-emerald-200",
} as const;

export function scoreColor(score: number) {
  if (score >= 75) return "text-emerald-600";
  if (score >= 55) return "text-amber-600";
  return "text-rose-600";
}

export function scoreBar(score: number) {
  if (score >= 75) return "bg-emerald-500";
  if (score >= 55) return "bg-amber-500";
  return "bg-rose-500";
}

export const initials = (name: string) => name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
