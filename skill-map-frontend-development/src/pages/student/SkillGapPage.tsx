import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ArrowRight, BookOpen, CheckCircle2, Download, Flame, Search, Target, TrendingUp } from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Select } from "../../components/ui/Input";
import { ProgressBar, ProgressRing } from "../../components/ui/Progress";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { SkillDistributionChart, SkillGapChart } from "../../components/charts";
import { useFetch } from "../../hooks/useFetch";
import { studentService } from "../../services/studentService";
import { priorityColor, scoreBar } from "../../utils/format";
import { cn } from "../../utils/cn";

const targetRoles = [
  { value: "fullstack", label: "Full-Stack Developer" }, { value: "frontend", label: "Frontend Engineer" },
  { value: "backend", label: "Backend Engineer" }, { value: "devops", label: "DevOps Engineer" }, { value: "data", label: "Data Scientist" },
];

export default function SkillGapPage() {
  const [role, setRole] = useState("fullstack");
  const [priority, setPriority] = useState<"All" | "High" | "Medium" | "Low">("All");
  const [query, setQuery] = useState("");
  const { data, loading } = useFetch(async () => {
    const [gaps, skills, profile] = await Promise.all([studentService.getSkillGaps(), studentService.getSkills(), studentService.getProfile()]);
    return { gaps, skills, profile };
  });

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.gaps.filter((g) => (priority === "All" || g.priority === priority) && g.skill.toLowerCase().includes(query.toLowerCase()));
  }, [data, priority, query]);

  if (loading || !data) return <PageSkeleton />;
  const { gaps, skills, profile } = data;
  const high = gaps.filter((g) => g.priority === "High").length;
  const avgGap = Math.round(gaps.reduce((a, g) => a + g.gap, 0) / gaps.length);
  const meeting = skills.filter((s) => s.score >= s.required).length;
  const roleLabel = targetRoles.find((r) => r.value === role)?.label;

  return (
    <div className="space-y-6">
      <PageHeader title="Skill Gap Analysis" description="How your competencies compare against industry benchmarks for your target role." actions={<><Button variant="outline" icon={<Download className="h-4 w-4" />}>Export report</Button><Link to="/student/learning"><Button icon={<BookOpen className="h-4 w-4" />}>Start learning path</Button></Link></>} />

      {/* Role selector + overall */}
      <Card>
        <CardBody className="grid gap-6 pt-5 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="w-full sm:max-w-xs"><Select label="Target role" value={role} onChange={(e) => setRole(e.target.value)} options={targetRoles} /></div>
              <p className="pb-2 text-xs text-slate-500">Benchmarks are derived from 1,240 live job descriptions & recruiter competency frameworks.</p>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[["Skills benchmarked", skills.length], ["Meeting benchmark", meeting], ["Below benchmark", skills.length - meeting], ["Avg. gap", `${avgGap} pts`]].map(([l, v]) => (
                <div key={l} className="rounded-xl bg-slate-50 p-3"><p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{l}</p><p className="mt-1 text-lg font-bold text-slate-900">{v}</p></div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-5 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-5">
            <ProgressRing value={profile.careerReadiness} size={104} stroke={9} sub="Readiness" />
            <div><p className="text-sm font-semibold text-slate-900">{roleLabel}</p><p className="mt-1 max-w-[180px] text-xs text-slate-600">Reach <span className="font-semibold text-indigo-700">80%</span> to be placement-ready. Closing your 2 high-priority gaps adds ~+11%.</p></div>
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="High priority gaps" value={high} icon={<Flame className="h-5 w-5" />} accent="rose" hint="Address these first" />
        <StatCard label="Total gaps" value={gaps.length} icon={<AlertTriangle className="h-5 w-5" />} accent="amber" hint="Below role benchmark" />
        <StatCard label="Gaps closed" value={3} icon={<CheckCircle2 className="h-5 w-5" />} accent="emerald" delta={50} hint="last 90 days" />
        <StatCard label="Projected readiness" value="79%" icon={<TrendingUp className="h-5 w-5" />} accent="indigo" hint="if current plan completed" />
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="Current vs required proficiency" subtitle={`Ranked by gap size for ${roleLabel}`} />
          <CardBody><SkillGapChart gaps={gaps} height={340} /></CardBody>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Category comparison" subtitle="Average proficiency by skill category" />
          <CardBody><SkillDistributionChart skills={skills} /></CardBody>
        </Card>
      </div>

      {/* Detailed table */}
      <Card>
        <CardHeader title="Detailed gap report" subtitle={`${filtered.length} of ${gaps.length} skills`} action={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search skill" className="h-9 w-40 rounded-lg border border-slate-200 pl-9 pr-3 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 sm:w-52" /></div>
            <div className="flex rounded-lg bg-slate-100 p-0.5">{(["All", "High", "Medium", "Low"] as const).map((p) => <button key={p} onClick={() => setPriority(p)} className={cn("rounded-md px-2.5 py-1 text-xs font-medium", priority === p ? "bg-white text-slate-900 shadow-sm" : "text-slate-600")}>{p}</button>)}</div>
          </div>
        } />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr><th className="px-5 py-3 font-medium">Skill</th><th className="px-5 py-3 font-medium">Proficiency</th><th className="px-5 py-3 font-medium">Gap</th><th className="px-5 py-3 font-medium">Priority</th><th className="px-5 py-3 font-medium">Market demand</th><th className="px-5 py-3 font-medium">Recommended action</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((g) => (
                <tr key={g.skill} className="hover:bg-slate-50/60">
                  <td className="px-5 py-3.5 font-semibold text-slate-800">{g.skill}</td>
                  <td className="px-5 py-3.5">
                    <div className="w-44">
                      <div className="mb-1 flex justify-between text-xs"><span className="text-slate-600">{g.current}</span><span className="text-slate-400">req. {g.required}</span></div>
                      <div className="relative h-2 rounded-full bg-slate-100"><div className={cn("h-full rounded-full", scoreBar(g.current))} style={{ width: `${g.current}%` }} /><span className="absolute top-1/2 h-3.5 w-0.5 -translate-y-1/2 bg-slate-800" style={{ left: `${g.required}%` }} /></div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5"><span className="font-bold text-rose-600">-{g.gap}</span></td>
                  <td className="px-5 py-3.5"><span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset", priorityColor[g.priority])}>{g.priority}</span></td>
                  <td className="px-5 py-3.5"><div className="flex items-center gap-2"><ProgressBar value={g.demand} size="sm" className="w-16" barClassName="bg-sky-500" /><span className="text-xs text-slate-600">{g.demand}% roles</span></div></td>
                  <td className="px-5 py-3.5"><Link to="/student/learning" className="inline-flex items-center gap-1 text-indigo-600 hover:underline"><BookOpen className="h-3.5 w-3.5" />{g.recommendedCourse}</Link></td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={6} className="px-5 py-10 text-center text-sm text-slate-500">No skills match your filters.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Action plan */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Recommended 90-day action plan" subtitle="Sequenced by impact on career readiness" />
          <CardBody>
            <ol className="space-y-4">
              {gaps.filter((g) => g.priority !== "Low").slice(0, 4).map((g, i) => (
                <li key={g.skill} className="flex gap-4 rounded-xl border border-slate-100 p-4">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-semibold text-slate-800">Close the {g.skill} gap</p><Badge tone={g.priority === "High" ? "rose" : "amber"}>{g.priority} · Weeks {i * 3 + 1}–{i * 3 + 3}</Badge></div>
                    <p className="mt-1 text-xs text-slate-500">Complete <span className="font-medium text-slate-700">{g.recommendedCourse}</span>, then submit one project as evidence for faculty verification. Expected uplift: <span className="font-semibold text-emerald-600">+{Math.round(g.gap * 0.7)} pts</span>.</p>
                  </div>
                </li>
              ))}
            </ol>
          </CardBody>
        </Card>
        <Card className="bg-gradient-to-br from-slate-900 to-indigo-950 text-white">
          <CardBody className="pt-5">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10"><Target className="h-5 w-5" /></span>
            <h3 className="mt-4 text-lg font-bold">Skills you already exceed</h3>
            <p className="mt-1 text-sm text-indigo-200">Leverage these strengths in interviews and your portfolio.</p>
            <ul className="mt-4 space-y-2.5">
              {skills.filter((s) => s.score >= s.required).map((s) => (
                <li key={s.id} className="flex items-center justify-between text-sm"><span className="inline-flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" />{s.name}</span><span className="font-semibold text-emerald-300">+{s.score - s.required}</span></li>
              ))}
            </ul>
            <Link to="/student/opportunities" className="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-white hover:underline">Find matching opportunities <ArrowRight className="h-4 w-4" /></Link>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
