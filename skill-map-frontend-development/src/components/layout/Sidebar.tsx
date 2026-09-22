import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { ChevronDown, LogOut, X } from "lucide-react";
import { Logo } from "../ui/Logo";
import { cn } from "../../utils/cn";
import { navByRole } from "./navConfig";
import { studentService } from "../../services/studentService";
import type { UserRole } from "../../types";

interface Props { role: UserRole; open: boolean; onClose: () => void; onLogout: () => void }

/** Real career readiness pulled from the authenticated student's own backend profile - never a fixed/fabricated figure. */
function ReadinessCard() {
  const [readiness, setReadiness] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    // Uses the deterministic role-benchmark endpoint (not the static profile.careerReadiness
    // field, which is written once at signup and never recalculated) so this always reflects
    // the student's current real skills.
    studentService.getRoleBenchmark()
      .then((b) => { if (active) setReadiness(b.careerReadiness ?? 0); })
      .catch(() => { if (active) setReadiness(null); });
    return () => { active = false; };
  }, []);

  if (readiness === null) return null;

  return (
    <div className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-100">
      <p className="text-xs font-semibold text-slate-600">Career Readiness</p>
      <p className="mt-1 text-2xl font-bold text-blue-600">{readiness}%</p>
      <p className="mt-1 text-xs text-slate-500">Based on your verified skills and benchmark coverage.</p>
    </div>
  );
}

export function Sidebar({ role, open, onClose, onLogout }: Props) {
  const sections = navByRole[role];
  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden" onClick={onClose} />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-100 px-5">
          <Logo />
          <button onClick={onClose} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"><X className="h-5 w-5" /></button>
        </div>
        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
          {sections.map((section, i) => {
            const list = (
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to.split("/").length <= 2}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn("group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition", isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900")
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon className={cn("h-[18px] w-[18px]", isActive ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600")} />
                          <span className="flex-1">{item.label}</span>
                          {item.badge && <span className="rounded-full bg-blue-600 px-2 py-0.5 text-[10px] font-semibold text-white">{item.badge}</span>}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            );
            return section.title ? (
              <details key={i} className="group" open>
                <summary className="mb-2 flex cursor-pointer select-none list-none items-center justify-between pl-[42px] pr-3 text-xs font-bold uppercase tracking-wider text-slate-500 marker:content-none [&::-webkit-details-marker]:hidden">
                  {section.title}
                  <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform group-open:rotate-180" />
                </summary>
                {list}
              </details>
            ) : (
              <div key={i}>{list}</div>
            );
          })}
        </nav>
        <div className="border-t border-slate-100 p-3">
          {role === "student" && <ReadinessCard />}
          <button onClick={onLogout} className="mt-3 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600">
            <LogOut className="h-[18px] w-[18px]" /> Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
