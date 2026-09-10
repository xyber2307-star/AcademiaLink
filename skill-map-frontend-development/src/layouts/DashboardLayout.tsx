import { useState } from "react";
import { Navigate, Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "../components/layout/Sidebar";
import { Topbar } from "../components/layout/Topbar";
import { useAuth } from "../hooks/useAuth";
import type { UserRole } from "../types";

export function DashboardLayout({ role }: { role: UserRole }) {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  if (!user) return <Navigate to="/login" replace />;
  if (!user.verified) return <Navigate to="/verify-email" replace />;
  if (user.role !== role) return <Navigate to={`/${user.role}`} replace />;

  const handleLogout = () => { logout(); navigate("/"); };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar role={role} open={open} onClose={() => setOpen(false)} onLogout={handleLogout} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar user={user} onMenu={() => setOpen(true)} onLogout={handleLogout} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8"><div className="mx-auto max-w-7xl"><Outlet /></div></main>
      </div>
    </div>
  );
}
