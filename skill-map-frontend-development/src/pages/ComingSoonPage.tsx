import { Link, useLocation } from "react-router-dom";
import { Construction } from "lucide-react";
import { Button } from "../components/ui/Button";

export default function ComingSoonPage({ title }: { title?: string }) {
  const { pathname } = useLocation();
  const name = title ?? pathname.split("/").filter(Boolean).pop()?.replace(/-/g, " ") ?? "This page";
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><Construction className="h-8 w-8" /></span>
      <h1 className="mt-5 text-xl font-bold capitalize text-slate-900">{name}</h1>
      <p className="mt-2 max-w-sm text-sm text-slate-500">This module is scheduled in the next build phase. The layout, navigation and data services are already wired for it.</p>
      <Link to="/student" className="mt-6"><Button variant="outline">Back to dashboard</Button></Link>
    </div>
  );
}
