import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, Award, Briefcase, GitCompare, Star, Target, TrendingUp } from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { StatCard } from "../../components/ui/StatCard";
import { ProgressBar, ProgressRing } from "../../components/ui/Progress";
import { Badge } from "../../components/ui/Badge";
import { SkillBadge } from "../../components/ui/SkillBadge";
import { Avatar } from "../../components/ui/Avatar";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { ApplicationStatusChart, ReadinessRadialChart, ReadinessTrendChart, SkillDistributionChart, SkillGapChart, CHART_COLORS } from "../../components/charts";
import { useFetch } from "../../hooks/useFetch";
import { studentService } from "../../services/studentService";
import { priorityColor, scoreBar, statusColor } from "../../utils/format";

export default function StudentDashboard() {
  const { data, loading } = useFetch(async () => {
    const [profile, skills, gaps, learning, opportunities, applications, feedback, trend, breakdown] = await Promise.all([
      studentService.getProfile(), studentService.getSkills(), studentService.getSkillGaps(), studentService.getLearning(),
      studentService.getOpportunities(), studentService.getApplications(), studentService.getMentorFeedback(),
      studentService.getReadinessTrend(), studentService.getReadinessBreakdown(),
    ]);
    return { profile, skills, gaps, learning, opportunities, applications, feedback, trend, breakdown };
  });

  if (loading || !data) return <PageSkeleton />;
  const { profile, skills, gaps, learning, opportunities, applications, feedback, trend, breakdown } = data;
  const strong = [...skills].sort((a, b) => b.score - a.score).slice(0, 5);
  const weak = [...skills].sort((a, b) => a.score - b.score).slice(0, 5);
  const activeApps = applications.filter((a) => !["Rejected", "Offered"].includes(a.status)).length;

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-600 via-indigo-600 to-violet-600 p-6 text-white shadow-lg shadow-indigo-200 sm:p-8">
        <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/10" />
        <div className="absolute -bottom-16 right-32 h-48 w-48 rounded-full bg-white/10" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm text-indigo-100">Good morning 👋</p>
            <h1 className="mt-1 text-2xl font-bold sm:text-3xl">{profile.name}</h1>
            <p className="mt-1 text-sm text-indigo-100">{profile.degree} · {profile.branch} · {profile.year}</p>
            <p className="mt-4 max-w-lg text-sm text-indigo-50">You're <span className="font-semibold text-white">{profile.careerReadiness}% ready</span> for a <span className="font-semibold text-white">{profile.targetRole}</span> role. Close 2 high-priority gaps to reach the 80% placement benchmark.</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link to="/student/skill-gap" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-50">View skill gaps <ArrowRight className="h-4 w-4" /></Link>
              <Link to="/student/assessment" className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold text-white ring-1 ring-white/30 hover:bg-white/25">Take assessment</Link>
            </div>
          </div>
          <div className="flex items-center gap-6 rounded-2xl bg-white/10 p-4 ring-1 ring-white/20 backdrop-blur">
            <ProgressRing value={profile.profileCompletion} size={92} stroke={8} color="#fff" labelClassName="text-white" />
            <div>
              <p className="text-sm font-semibold">Profile completion</p>
              <p className="mt-1 text-xs text-indigo-100">Add 2 more projects and verify 1 certificate to reach 100%.</p>
              <Link to="/student/profile" className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-white underline-offset-2 hover:underline">Complete profile <ArrowUpRight className="h-3 w-3" /></Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Skill score" value={`${profile.skillScore}/100`} icon={<Award className="h-5 w-5" />} delta={4} hint="vs last month" accent="indigo" />
        <StatCard label="Career readiness" value={`${profile.careerReadiness}%`} icon={<TrendingUp className="h-5 w-5" />} delta={5} hint="target role benchmark 80%" accent="emerald" />
        <StatCard label="Skill gaps" value={gaps.filter((g) => g.priority !== "Low").length} icon={<GitCompare className="h-5 w-5" />} hint={`${gaps.filter((g) => g.priority === "High").length} high priority`} accent="rose" />
        <StatCard label="Active applications" value={activeApps} icon={<Target className="h-5 w-5" />} hint="1 interview this week" accent="amber" />
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Career readiness trend" subtitle="Readiness and skill score over the last 6 months" action={<Badge tone="emerald">+26% since Jan</Badge>} />
          <CardBody><ReadinessTrendChart data={trend} /></CardBody>
        </Card>
        <Card>
          <CardHeader title="Skill distribution" subtitle="You vs industry expectation by category" />
          <CardBody><SkillDistributionChart skills={skills} /></CardBody>
        </Card>
      </div>

      {/* Strong / weak / gaps */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Strong skills" subtitle="Your top competencies" action={<Link to="/student/skills" className="text-xs font-semibold text-indigo-600">View all</Link>} />
          <CardBody className="space-y-3">
            {strong.map((s) => (
              <div key={s.id}>
                <div className="mb-1 flex items-center justify-between text-sm"><span className="font-medium text-slate-800">{s.name}</span><span className="font-semibold text-emerald-600">{s.score}</span></div>
                <ProgressBar value={s.score} barClassName="bg-emerald-500" size="sm" />
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Weak skills" subtitle="Needs attention" action={<Link to="/student/learning" className="text-xs font-semibold text-indigo-600">Improve</Link>} />
          <CardBody className="space-y-3">
            {weak.map((s) => (
              <div key={s.id}>
                <div className="mb-1 flex items-center justify-between text-sm"><span className="font-medium text-slate-800">{s.name}</span><span className={`font-semibold ${s.score < 55 ? "text-rose-600" : "text-amber-600"}`}>{s.score}</span></div>
                <ProgressBar value={s.score} barClassName={scoreBar(s.score)} size="sm" />
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Skill gap snapshot" subtitle={`vs ${profile.targetRole} benchmark`} action={<Link to="/student/skill-gap" className="text-xs font-semibold text-indigo-600">Full analysis</Link>} />
          <CardBody><SkillGapChart gaps={gaps.slice(0, 5)} height={230} /></CardBody>
        </Card>
      </div>

      {/* Learning + opportunities */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Recommended learning" subtitle="Curated to close your top gaps" action={<Link to="/student/learning" className="text-xs font-semibold text-indigo-600">View path</Link>} />
          <CardBody className="space-y-3">
            {learning.slice(0, 4).map((l) => (
              <div key={l.id} className="flex items-center gap-4 rounded-xl border border-slate-100 p-3 transition hover:border-indigo-200 hover:bg-indigo-50/30">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-xs font-bold text-indigo-600">{l.type.slice(0, 3).toUpperCase()}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">{l.title}</p>
                  <p className="text-xs text-slate-500">{l.provider} · {l.duration} · <span className="text-indigo-600">{l.skill}</span></p>
                  {l.progress > 0 && <ProgressBar value={l.progress} size="sm" className="mt-2" />}
                </div>
                <span className="text-xs font-semibold text-slate-600">{l.progress > 0 ? `${l.progress}%` : <span className="inline-flex items-center gap-1 text-amber-600"><Star className="h-3 w-3 fill-amber-400 text-amber-400" />{l.rating}</span>}</span>
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Recommended opportunities" subtitle="Ranked by your skill-match score" action={<Link to="/student/opportunities" className="text-xs font-semibold text-indigo-600">Marketplace</Link>} />
          <CardBody className="space-y-3">
            {opportunities.slice(0, 4).map((o) => (
              <Link to={`/student/opportunities/${o.id}`} key={o.id} className="flex items-center gap-4 rounded-xl border border-slate-100 p-3 transition hover:border-indigo-200 hover:bg-indigo-50/30">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-xs font-bold text-white">{o.logo}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">{o.title}</p>
                  <p className="text-xs text-slate-500">{o.company} · {o.location} · {o.stipend}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1">{o.skills.slice(0, 3).map((s) => <span key={s} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">{s}</span>)}</div>
                </div>
                <div className="text-right"><p className={`text-lg font-bold ${o.matchScore >= 80 ? "text-emerald-600" : "text-amber-600"}`}>{o.matchScore}%</p><p className="text-[10px] uppercase tracking-wide text-slate-400">match</p></div>
              </Link>
            ))}
          </CardBody>
        </Card>
      </div>

      {/* Applications + readiness + feedback */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Application status" subtitle={`${applications.length} total applications`} action={<Link to="/student/applications" className="text-xs font-semibold text-indigo-600">Tracker</Link>} />
          <CardBody>
            <ApplicationStatusChart applications={applications} />
            <ul className="mt-2 space-y-2">
              {applications.slice(0, 3).map((a) => (
                <li key={a.id} className="flex items-center justify-between text-sm"><span className="truncate text-slate-700">{a.role} <span className="text-slate-400">· {a.company}</span></span><span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${statusColor[a.status]}`}>{a.status}</span></li>
              ))}
            </ul>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Career readiness breakdown" subtitle="Weighted components of your readiness index" />
          <CardBody>
            <ReadinessRadialChart data={breakdown} />
            <ul className="mt-1 grid grid-cols-1 gap-1.5">
              {breakdown.map((b, i) => (
                <li key={b.name} className="flex items-center justify-between text-xs"><span className="flex items-center gap-2 text-slate-600"><span className="h-2.5 w-2.5 rounded-full" style={{ background: CHART_COLORS[i] }} />{b.name}</span><span className="font-semibold text-slate-800">{b.value}%</span></li>
              ))}
            </ul>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Mentor feedback" subtitle="Latest guidance from your mentors" action={<Link to="/student/mentors" className="text-xs font-semibold text-indigo-600">All feedback</Link>} />
          <CardBody className="space-y-4">
            {feedback.map((f) => (
              <div key={f.id} className="rounded-xl bg-slate-50 p-3">
                <div className="flex items-center gap-3">
                  <Avatar src={f.avatar} name={f.mentor} size="sm" />
                  <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-800">{f.mentor}</p><p className="truncate text-[11px] text-slate-500">{f.mentorRole}</p></div>
                  <span className="flex items-center gap-0.5">{[1, 2, 3, 4, 5].map((i) => <Star key={i} className={`h-3 w-3 ${i <= f.rating ? "fill-amber-400 text-amber-400" : "text-slate-300"}`} />)}</span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{f.message}</p>
                <div className="mt-2 flex items-center justify-between"><SkillBadge name={f.skill} /><span className="text-[11px] text-slate-400">{f.date}</span></div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      {/* Priority gaps table */}
      <Card>
        <CardHeader title="Priority skill gaps" subtitle="Highest impact actions for your target role" action={<Link to="/student/skill-gap" className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600">Full report <ArrowRight className="h-3 w-3" /></Link>} />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3 font-medium">Skill</th><th className="px-5 py-3 font-medium">Current</th><th className="px-5 py-3 font-medium">Required</th><th className="px-5 py-3 font-medium">Gap</th><th className="px-5 py-3 font-medium">Priority</th><th className="px-5 py-3 font-medium">Recommended</th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {gaps.slice(0, 5).map((g) => (
                <tr key={g.skill} className="hover:bg-slate-50/60">
                  <td className="px-5 py-3 font-medium text-slate-800">{g.skill}</td>
                  <td className="px-5 py-3"><div className="flex items-center gap-2"><ProgressBar value={g.current} size="sm" className="w-20" barClassName={scoreBar(g.current)} /><span className="text-slate-600">{g.current}</span></div></td>
                  <td className="px-5 py-3 text-slate-600">{g.required}</td>
                  <td className="px-5 py-3 font-semibold text-rose-600">-{g.gap}</td>
                  <td className="px-5 py-3"><span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${priorityColor[g.priority]}`}>{g.priority}</span></td>
                  <td className="px-5 py-3"><span className="inline-flex items-center gap-1 text-indigo-600"><Briefcase className="h-3.5 w-3.5" />{g.recommendedCourse}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
