import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Briefcase, Building2, Eye, EyeOff, GraduationCap, Lock, Mail, ShieldCheck, Users } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { useAuth } from "../../hooks/useAuth";
import type { UserRole } from "../../types";
import { cn } from "../../utils/cn";

const roles: { value: UserRole; label: string; icon: typeof GraduationCap }[] = [
  { value: "student", label: "Student", icon: GraduationCap },
  { value: "faculty", label: "Faculty", icon: Users },
  { value: "recruiter", label: "Recruiter", icon: Briefcase },
  { value: "institution", label: "Institution", icon: Building2 },
  { value: "admin", label: "Admin", icon: ShieldCheck },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<UserRole>("student");
  const [email, setEmail] = useState("ananya.sharma@nitk.edu.in");
  const [password, setPassword] = useState("password123");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError("Please enter your email and password."); return; }
    setError(null); setLoading(true);
    try { const u = await login({ email, password, role }); navigate(`/${u.role}`); }
    catch { setError("Invalid credentials. Please try again."); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">Welcome back</h1>
      <p className="mt-1 text-sm text-slate-500">Sign in to continue to your SKILL MAP dashboard.</p>

      <div className="mt-6">
        <p className="mb-2 text-sm font-medium text-slate-700">I am a</p>
        <div className="grid grid-cols-5 gap-2">
          {roles.map((r) => (
            <button key={r.value} type="button" onClick={() => setRole(r.value)} className={cn("flex flex-col items-center gap-1 rounded-xl border px-1 py-2.5 text-[11px] font-medium transition", role === r.value ? "border-indigo-500 bg-indigo-50 text-indigo-700 ring-2 ring-indigo-100" : "border-slate-200 text-slate-600 hover:border-slate-300")}>
              <r.icon className="h-4 w-4" />{r.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <Input label="Email address" type="email" icon={<Mail className="h-4 w-4" />} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@institution.edu" />
        <div className="relative">
          <Input label="Password" type={show ? "text" : "password"} icon={<Lock className="h-4 w-4" />} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          <button type="button" onClick={() => setShow((v) => !v)} className="absolute right-3 top-[38px] text-slate-400 hover:text-slate-600">{show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
        </div>
        <div className="flex items-center justify-between text-sm">
          <label className="inline-flex items-center gap-2 text-slate-600"><input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" /> Remember me</label>
          <a href="#" className="font-medium text-indigo-600 hover:text-indigo-700">Forgot password?</a>
        </div>
        {error && <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <Button type="submit" size="lg" className="w-full" loading={loading}>Sign in</Button>
      </form>

      <div className="my-6 flex items-center gap-3 text-xs text-slate-400"><span className="h-px flex-1 bg-slate-200" />or continue with<span className="h-px flex-1 bg-slate-200" /></div>
      <div className="grid grid-cols-2 gap-3">
        <Button variant="outline" type="button">Google</Button>
        <Button variant="outline" type="button">DigiLocker</Button>
      </div>
      <p className="mt-6 text-center text-sm text-slate-600">New to SKILL MAP? <Link to="/register" className="font-semibold text-indigo-600 hover:text-indigo-700">Create an account</Link></p>
      <p className="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-center text-xs text-slate-500">Demo: any email/password works. Pick a role to preview its dashboard.</p>
    </div>
  );
}
