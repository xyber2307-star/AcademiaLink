import { NavLink } from "react-router-dom";
import { LogOut, X } from "lucide-react";
import { Logo } from "../ui/Logo";
import { cn } from "../../utils/cn";
import { navByRole } from "./navConfig";
import type { UserRole } from "../../types";

interface Props { role: UserRole; open: boolean; onClose: () => void; onLogout: () => void }

export function Sidebar({ role, open, onClose, onLogout }: Props) {
  const sections = navByRole[role];
  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden" onClick={onClose} />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform duration-300 lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-100 px-5">
          <Logo />
          <button onClick={onClose} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"><X className="h-5 w-5" /></button>
        </div>
        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
          {sections.map((section, i) => (
            <div key={i}>
              {section.title && <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{section.title}</p>}
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to.split("/").length <= 2}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn("group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition", isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900")
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon className={cn("h-[18px] w-[18px]", isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-600")} />
                          <span className="flex-1">{item.label}</span>
                          {item.badge && <span className="rounded-full bg-indigo-600 px-2 py-0.5 text-[10px] font-semibold text-white">{item.badge}</span>}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        <div className="border-t border-slate-100 p-3">
          <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 p-4 text-white">
            <p className="text-xs font-semibold">Career Readiness</p>
            <p className="mt-1 text-2xl font-bold">68%</p>
            <p className="mt-1 text-[11px] text-indigo-100">+5% since last month. Keep going!</p>
          </div>
          <button onClick={onLogout} className="mt-3 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600">
            <LogOut className="h-[18px] w-[18px]" /> Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
