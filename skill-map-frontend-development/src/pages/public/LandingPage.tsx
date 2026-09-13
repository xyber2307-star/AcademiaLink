import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, Award, BarChart3, BookOpen, Briefcase, Building2, CheckCircle2, GitCompare, GraduationCap, Menu,
  ShieldCheck, Sparkles, UserCheck, Users, X,
} from "lucide-react";
import { Logo } from "../../components/ui/Logo";
import { Button } from "../../components/ui/Button";
import { ProgressRing } from "../../components/ui/Progress";
import { SkillBadge } from "../../components/ui/SkillBadge";

const features = [
  { icon: GitCompare, title: "Skill Gap Analysis", desc: "Compare student competencies against live industry benchmarks and identify exactly what to learn next." },
  { icon: BookOpen, title: "Personalised Learning", desc: "Auto-curated courses, projects and certifications mapped to each skill gap." },
  { icon: ShieldCheck, title: "Verified Evidence", desc: "Faculty-verified projects and certificates that recruiters can trust." },
  { icon: Briefcase, title: "Opportunity Marketplace", desc: "Internships, apprenticeships and placements ranked by skill match score." },
  { icon: UserCheck, title: "Mentor Network", desc: "Industry mentors and faculty give structured feedback tied to skills." },
  { icon: BarChart3, title: "Institutional Analytics", desc: "Placement, skill and industry collaboration insights for leadership." },
];

const roles = [
  { icon: GraduationCap, label: "Students", desc: "Map skills, close gaps, get placed" },
  { icon: Users, label: "Faculty", desc: "Track competencies & verify evidence" },
  { icon: Building2, label: "Institutions", desc: "Placement & skill analytics" },
  { icon: UserCheck, label: "Mentors", desc: "Guide with structured feedback" },
  { icon: Briefcase, label: "Recruiters", desc: "Hire on verified skills" },
  { icon: Award, label: "Industry", desc: "Shape curriculum with demand data" },
];

const steps = [
  { n: "01", title: "Build your skill profile", desc: "Take adaptive assessments and upload evidence — projects, certificates, internships." },
  { n: "02", title: "Discover your gaps", desc: "See how you compare against your target role and get a prioritised action plan." },
  { n: "03", title: "Learn & get verified", desc: "Follow a personalised path; faculty and mentors validate your progress." },
  { n: "04", title: "Get matched & placed", desc: "Recruiters find you through skill-match scores, not just résumés." },
];

export default function LandingPage() {
  const [menu, setMenu] = useState(false);
  return (
    <div className="min-h-screen bg-white text-slate-900">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Logo />
          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
            <a href="#features" className="hover:text-slate-900">Features</a>
            <a href="#roles" className="hover:text-slate-900">Who it's for</a>
            <a href="#how" className="hover:text-slate-900">How it works</a>
          </nav>
          <div className="hidden items-center gap-2 md:flex">
            <Link to="/login"><Button variant="ghost">Sign in</Button></Link>
            <Link to="/register"><Button icon={<ArrowRight className="h-4 w-4" />}>Get started</Button></Link>
          </div>
          <button className="rounded-lg p-2 md:hidden" onClick={() => setMenu((v) => !v)}>{menu ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}</button>
        </div>
        {menu && (
          <div className="border-t border-slate-100 bg-white px-4 py-4 md:hidden">
            <nav className="flex flex-col gap-3 text-sm font-medium text-slate-700">
              <a href="#features" onClick={() => setMenu(false)}>Features</a>
              <a href="#roles" onClick={() => setMenu(false)}>Who it's for</a>
              <a href="#how" onClick={() => setMenu(false)}>How it works</a>
            </nav>
            <div className="mt-4 flex gap-2">
              <Link to="/login" className="flex-1"><Button variant="outline" className="w-full">Sign in</Button></Link>
              <Link to="/register" className="flex-1"><Button className="w-full">Get started</Button></Link>
            </div>
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.12),_transparent_60%)]" />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 pb-20 pt-16 sm:px-6 lg:grid-cols-2 lg:px-8 lg:pt-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700"><Sparkles className="h-3.5 w-3.5" /> Smart India Hackathon · SIH26044</span>
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl lg:text-6xl">
              Map skills. Close gaps. <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">Get placed.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg text-slate-600">
              AcademiaLink is a unified portal for academia–industry collaboration — turning student competencies into verified, industry-aligned skill profiles that drive internships and placements.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/register"><Button size="lg" icon={<ArrowRight className="h-4 w-4" />} className="w-full sm:w-auto">Create free account</Button></Link>
              <Link to="/login"><Button size="lg" variant="outline" className="w-full sm:w-auto">Explore demo dashboard</Button></Link>
            </div>
            <div className="mt-10 grid grid-cols-3 gap-6 border-t border-slate-100 pt-8">
              {[
                ["Deterministic", "Skill scoring, not guesswork"],
                ["Verified", "Faculty-reviewed evidence"],
                ["Explainable", "Transparent match scores"],
              ].map(([v, l]) => (
                <div key={l}><p className="text-lg font-bold text-slate-900 sm:text-xl">{v}</p><p className="text-xs text-slate-500 sm:text-sm">{l}</p></div>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-400">SIH 2026 prototype (SIH26044) — figures shown elsewhere in the app reflect real platform data, not projected user counts.</p>
          </div>

          {/* Hero mock dashboard */}
          <div className="relative">
            <div className="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-br from-indigo-200/60 via-violet-200/40 to-sky-200/60 blur-2xl" />
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-2xl shadow-indigo-200/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3"><img src="https://i.pravatar.cc/80?img=47" className="h-10 w-10 rounded-full" alt="" /><div><p className="text-sm font-semibold">Ananya Sharma</p><p className="text-xs text-slate-500">B.Tech CSE · NIT Karnataka</p></div></div>
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">Placement ready</span>
              </div>
              <div className="mt-5 grid grid-cols-3 gap-3">
                <div className="flex flex-col items-center rounded-2xl bg-slate-50 p-3"><ProgressRing value={74} size={72} stroke={6} sub="Skill" /></div>
                <div className="flex flex-col items-center rounded-2xl bg-slate-50 p-3"><ProgressRing value={68} size={72} stroke={6} color="#10b981" sub="Ready" /></div>
                <div className="flex flex-col items-center rounded-2xl bg-slate-50 p-3"><ProgressRing value={91} size={72} stroke={6} color="#f59e0b" sub="Match" /></div>
              </div>
              <div className="mt-4">
                <p className="text-xs font-semibold text-slate-500">TOP SKILLS</p>
                <div className="mt-2 flex flex-wrap gap-2"><SkillBadge name="React" score={86} verified /><SkillBadge name="JavaScript" score={88} verified /><SkillBadge name="Git" score={90} verified /><SkillBadge name="System Design" score={42} /></div>
              </div>
              <div className="mt-4 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-3">
                <div className="flex items-center justify-between text-xs"><span className="font-semibold text-indigo-900">Frontend Intern · Razorpay</span><span className="font-bold text-indigo-700">91% match</span></div>
                <div className="mt-2 h-1.5 rounded-full bg-white"><div className="h-full w-[91%] rounded-full bg-indigo-600" /></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Roles */}
      <section id="roles" className="border-y border-slate-100 bg-slate-50 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center"><h2 className="text-3xl font-bold tracking-tight">One platform, every stakeholder</h2><p className="mt-3 text-slate-600">Purpose-built experiences for everyone in the academia–industry ecosystem.</p></div>
          <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {roles.map((r) => (
              <div key={r.label} className="rounded-2xl border border-slate-200 bg-white p-5 text-center transition hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-100">
                <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><r.icon className="h-5 w-5" /></span>
                <p className="mt-3 text-sm font-semibold">{r.label}</p><p className="mt-1 text-xs text-slate-500">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center"><h2 className="text-3xl font-bold tracking-tight">Everything needed to go from classroom to career</h2><p className="mt-3 text-slate-600">Skill intelligence, verified evidence and opportunity matching — in one place.</p></div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="group rounded-2xl border border-slate-200 p-6 transition hover:border-indigo-200 hover:shadow-xl hover:shadow-indigo-100/60">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-200"><f.icon className="h-6 w-6" /></span>
                <h3 className="mt-5 text-lg font-semibold">{f.title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="bg-slate-950 py-20 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center"><h2 className="text-3xl font-bold tracking-tight">How AcademiaLink works</h2><p className="mt-3 text-slate-400">A guided journey from self-awareness to placement.</p></div>
          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {steps.map((s) => (
              <div key={s.n} className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur"><p className="text-sm font-bold text-indigo-400">{s.n}</p><h3 className="mt-3 text-lg font-semibold">{s.title}</h3><p className="mt-2 text-sm text-slate-400">{s.desc}</p></div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="mx-auto max-w-5xl overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 to-violet-700 px-6 py-14 text-center text-white shadow-2xl shadow-indigo-300 sm:px-12">
          <h2 className="text-3xl font-bold sm:text-4xl">Ready to map your future?</h2>
          <p className="mx-auto mt-4 max-w-xl text-indigo-100">Join thousands of students and hundreds of industry partners building India's most trusted skill ecosystem.</p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link to="/register"><Button size="lg" variant="secondary" className="w-full bg-white text-indigo-700 hover:bg-indigo-50 sm:w-auto">Get started free</Button></Link>
            <Link to="/login"><Button size="lg" variant="ghost" className="w-full text-white hover:bg-white/10 hover:text-white sm:w-auto">Sign in</Button></Link>
          </div>
          <div className="mt-8 flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-indigo-100">
            {["Free for students", "NEP 2020 aligned", "NSQF skill taxonomy", "Verified by institutions"].map((t) => <span key={t} className="inline-flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4" />{t}</span>)}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-100 py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-sm text-slate-500 sm:flex-row sm:px-6 lg:px-8">
          <Logo />
          <p>© 2025 AcademiaLink · Portal for Academia–Industry Collaboration · SIH26044</p>
        </div>
      </footer>
    </div>
  );
}
