import { useEffect, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { MailCheck } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { useAuth } from "../../hooks/useAuth";

export default function VerifyEmailPage() {
  const { user, verifyEmail } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState<string[]>(Array(6).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timer, setTimer] = useState(45);
  const refs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => { if (timer <= 0) return; const t = setTimeout(() => setTimer((s) => s - 1), 1000); return () => clearTimeout(t); }, [timer]);

  if (!user) return <Navigate to="/register" replace />;
  if (user.verified) return <Navigate to={`/${user.role}`} replace />;

  const onChange = (i: number, v: string) => {
    const d = v.replace(/\D/g, "").slice(-1);
    const next = [...code]; next[i] = d; setCode(next);
    if (d && i < 5) refs.current[i + 1]?.focus();
  };
  const onKey = (i: number, e: React.KeyboardEvent<HTMLInputElement>) => { if (e.key === "Backspace" && !code[i] && i > 0) refs.current[i - 1]?.focus(); };
  const onPaste = (e: React.ClipboardEvent) => { const t = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6); if (t.length === 6) { setCode(t.split("")); refs.current[5]?.focus(); } };

  const submit = async () => {
    const c = code.join("");
    if (c.length < 6) { setError("Enter the 6-digit code."); return; }
    setError(null); setLoading(true);
    const u = await verifyEmail(c);
    setLoading(false);
    if (u) navigate(`/${u.role}`);
  };

  return (
    <div className="text-center">
      <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600"><MailCheck className="h-8 w-8" /></span>
      <h1 className="mt-5 text-2xl font-bold tracking-tight text-slate-900">Verify your email</h1>
      <p className="mt-2 text-sm text-slate-500">We sent a 6-digit code to <span className="font-semibold text-slate-800">{user.email}</span>. Enter it below to activate your account.</p>
      <div className="mt-8 flex justify-center gap-2 sm:gap-3" onPaste={onPaste}>
        {code.map((d, i) => (
          <input key={i} ref={(el) => { refs.current[i] = el; }} inputMode="numeric" value={d} onChange={(e) => onChange(i, e.target.value)} onKeyDown={(e) => onKey(i, e)}
            className="h-14 w-11 rounded-xl border border-slate-300 text-center text-xl font-bold text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-100 sm:w-12" />
        ))}
      </div>
      {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
      <Button size="lg" className="mt-6 w-full" onClick={submit} loading={loading}>Verify & continue</Button>
      <p className="mt-4 text-sm text-slate-500">
        Didn't receive it?{" "}
        {timer > 0 ? <span className="text-slate-400">Resend in {timer}s</span> : <button onClick={() => setTimer(45)} className="font-semibold text-indigo-600">Resend code</button>}
      </p>
      <p className="mt-6 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-500">Demo: any 6 digits will verify the account.</p>
    </div>
  );
}
