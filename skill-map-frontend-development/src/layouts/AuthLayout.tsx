import { Link, Outlet } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import { Logo } from "../components/ui/Logo";

const points = ["AI-driven skill mapping against industry benchmarks", "Verified evidence portfolio trusted by recruiters", "Personalised learning paths & mentor guidance", "One marketplace for internships and placements"];

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-slate-950 lg:block">
        <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-indigo-600/40 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-violet-600/40 blur-3xl" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Link to="/"><Logo light /></Link>
          <div>
            <h2 className="text-4xl font-bold leading-tight text-white">Bridge the gap between <span className="bg-gradient-to-r from-indigo-300 to-violet-300 bg-clip-text text-transparent">campus and career.</span></h2>
            <p className="mt-4 max-w-md text-slate-300">AcademiaLink connects students, faculty, institutions and industry on one platform for skill mapping, internships and placements.</p>
            <ul className="mt-8 space-y-3">
              {points.map((p) => <li key={p} className="flex items-center gap-3 text-sm text-slate-200"><CheckCircle2 className="h-5 w-5 text-emerald-400" />{p}</li>)}
            </ul>
          </div>
          <p className="text-xs text-slate-500">Smart India Hackathon · PS ID SIH26044</p>
        </div>
      </div>
      <div className="flex flex-col bg-white">
        <div className="flex items-center justify-between p-6 lg:hidden"><Link to="/"><Logo /></Link></div>
        <div className="flex flex-1 items-center justify-center px-6 py-8 sm:px-12"><div className="w-full max-w-md"><Outlet /></div></div>
      </div>
    </div>
  );
}
