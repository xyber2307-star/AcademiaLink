import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Building2, Lock, Mail, User } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Input, Select } from "../../components/ui/Input";
import { useAuth } from "../../hooks/useAuth";
import type { UserRole } from "../../types";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "", role: "student" as UserRole, institution: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value });

  const strength = Math.min(4, [form.password.length >= 8, /[A-Z]/.test(form.password), /\d/.test(form.password), /[^\w]/.test(form.password)].filter(Boolean).length);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = "Full name is required";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) errs.email = "Enter a valid email";
    if (form.password.length < 8) errs.password = "Minimum 8 characters";
    if (form.password !== form.confirm) errs.confirm = "Passwords do not match";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setLoading(true);
    try {
      const u = await register(form);
      navigate(`/${u.role}`);
    } catch (err: any) {
      const message: string = err?.message || "";
      const friendly =
        message === "Failed to fetch" || message.includes("NetworkError")
          ? "Could not reach the server. Please check your connection or try again shortly."
          : message.includes("auth/email-already-in-use")
          ? "An account with this email already exists. Try signing in instead."
          : message.includes("auth/") || message
          ? message.replace(/^Firebase:\s*/, "")
          : "Registration failed. Please try again.";
      setErrors({ email: friendly });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">Create your account</h1>
      <p className="mt-1 text-sm text-slate-500">Start mapping your skills in under two minutes.</p>
      <form onSubmit={submit} className="mt-6 space-y-4">
        <Input label="Full name" icon={<User className="h-4 w-4" />} value={form.name} onChange={set("name")} error={errors.name} placeholder="Ananya Sharma" />
        <Input label="Email address" type="email" icon={<Mail className="h-4 w-4" />} value={form.email} onChange={set("email")} error={errors.email} placeholder="you@institution.edu" hint="Use your institutional email for auto-verification." />
        <div className="grid gap-4 sm:grid-cols-2">
          <Select label="Register as" value={form.role} onChange={set("role")} options={[{ value: "student", label: "Student" }, { value: "faculty", label: "Faculty" }, { value: "recruiter", label: "Recruiter" }, { value: "institution", label: "Institution" }]} />
          <Input label="Institution / Company" icon={<Building2 className="h-4 w-4" />} value={form.institution} onChange={set("institution")} placeholder="NIT Karnataka" />
        </div>
        <div>
          <Input label="Password" type="password" icon={<Lock className="h-4 w-4" />} value={form.password} onChange={set("password")} error={errors.password} placeholder="At least 8 characters" />
          <div className="mt-2 grid grid-cols-4 gap-1">{[0, 1, 2, 3].map((i) => <span key={i} className={`h-1 rounded-full ${i < strength ? (strength <= 1 ? "bg-rose-500" : strength <= 2 ? "bg-amber-500" : "bg-emerald-500") : "bg-slate-200"}`} />)}</div>
        </div>
        <Input label="Confirm password" type="password" icon={<Lock className="h-4 w-4" />} value={form.confirm} onChange={set("confirm")} error={errors.confirm} placeholder="Re-enter password" />
        <label className="flex items-start gap-2 text-sm text-slate-600"><input type="checkbox" required className="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600" /> I agree to the <a href="#" className="font-medium text-indigo-600">Terms</a> and <a href="#" className="font-medium text-indigo-600">Privacy Policy</a>.</label>
        <Button type="submit" size="lg" className="w-full" loading={loading}>Create account</Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-600">Already have an account? <Link to="/login" className="font-semibold text-indigo-600 hover:text-indigo-700">Sign in</Link></p>
    </div>
  );
}
