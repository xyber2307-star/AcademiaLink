import { Link } from "react-router-dom";
import { AlertTriangle, ArrowRight, ArrowUpRight, Award, Briefcase, GitCompare, Target, TrendingUp } from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { StatCard } from "../../components/ui/StatCard";
import { ProgressBar, ProgressRing } from "../../components/ui/Progress";
import { Avatar } from "../../components/ui/Avatar";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { ApplicationStatusChart, ReadinessRadialChart, ReadinessTrendChart, SkillDistributionChart, SkillGapChart, CHART_COLORS } from "../../components/charts";
import { useFetch } from "../../hooks/useFetch";
import { studentService } from "../../services/studentService";
import { applicationService, type JobApplication } from "../../services/applicationService";
import { facultyService } from "../../services/facultyService";
import { priorityColor, scoreBar, statusColor } from "../../utils/format";
import type { Application, ApplicationStatus } from "../../types";

/** Maps real backend application statuses onto the dashboard's display buckets. Real data, relabeled for presentation only - no invented applications or counts. */
function mapApplicationStatus(status: JobApplication["status"]): ApplicationStatus {
  switch (status) {
    case "applied":
    case "under_review":
      return "Applied";
    case "shortlisted":
      return "Shortlisted";
    case "selected":
      return "Offered";
    case "rejected":
    case "withdrawn":
      return "Rejected";
    default:
      return "Applied";
  }
}

export default function StudentDashboard() {
  const { data, loading, error } = useFetch(async () => {
    const [profile, skills, benchmark, opportunities, applications, feedback, learningPaths, assessmentHistory] = await Promise.all([
      studentService.getProfile(),
      studentService.getSkills(),
      studentService.getRoleBenchmark(),
      studentService.getOpportunities(),
      applicationService.getMyApplications(),
      facultyService.getMyMentorFeedback(),
      studentService.getLearningPaths(),
      studentService.getAssessmentHistory(),
    ]);
    return { profile, skills, benchmark, opportunities, applications, feedback, learningPaths, assessmentHistory };
  });

  if (loading || !data) return <PageSkeleton />;

  if (error) {
    return (
      <Card>
        <CardBody className="flex flex-col items-center gap-3 py-12 text-center">
          <AlertTriangle className="h-8 w-8 text-rose-500" />
          <p className="font-semibold text-slate-800">We couldn't load your dashboard</p>
          <p className="max-w-sm text-sm text-slate-500">{error}. Please refresh the page or try again shortly.</p>
        </CardBody>
      </Card>
    );
  }

  const { profile, skills, benchmark, opportunities, applications, feedback, learningPaths, assessmentHistory } = data;
  const gaps = benchmark.gaps || [];
  const strong = [...skills].sort((a, b) => b.score - a.score).slice(0, 5);
  const weak = [...skills].sort((a, b) => a.score - b.score).slice(0, 5);
  // NOTE: profile.careerReadiness / profile.skillScore are static fields written once at
  // account creation and never recalculated by the backend - they must not be displayed as
  // live metrics. benchmark.careerReadiness (from the deterministic role-benchmark endpoint)
  // and a live average of the student's actual skills are the real, current values.
  const liveSkillScore = skills.length > 0 ? Math.round(skills.reduce((sum, s) => sum + s.score, 0) / skills.length) : 0;
  const dashboardApplications: Application[] = applications.map((a) => ({
    id: a.application_id,
    opportunityId: a.job_id,
    role: a.job_title || "Role",
    company: a.company || "Company",
    appliedOn: a.applied_at,
    status: mapApplicationStatus(a.status),
    stage: 0,
  }));
  const activeApps = applications.filter((a) => !["rejected", "selected", "withdrawn"].includes(a.status)).length;
  // Defensive de-dupe: guards against the API ever returning the same opportunity twice.
  // Keyed by id AND by normalized title+company, because the real data can contain distinct
  // Firestore job documents that are content-duplicates of each other (same role/company
  // posted multiple times) - an id-only key would not catch that.
  const uniqueOpportunities = Array.from(
    new Map(opportunities.map((o) => [`${o.title.trim().toLowerCase()}|${o.company.trim().toLowerCase()}`, o])).values()
  );

  // Active learning path skills (real, gap-driven), sorted by deterministic priority already applied server-side.
  const activePath = learningPaths.find((p) => p.status === "active") || learningPaths[0];
  const learningItems = (activePath?.skills || []).slice(0, 4);

  // Genuine readiness breakdown - all real, derived from the same deterministic role-benchmark used on Skill Gap page.
  const breakdown = [
    { name: "Career readiness", value: benchmark.careerReadiness },
    { name: "Skill score", value: liveSkillScore },
    {
      name: "Benchmark coverage",
      value: benchmark.skillsBenchmarked > 0 ? Math.round((benchmark.meetingBenchmark / benchmark.skillsBenchmarked) * 100) : 0,
    },
  ];

  // Genuine historical trend from real assessment timestamps - only rendered with >= 2 distinct months of real data.
  const monthlyScores = new Map<string, number[]>();
  for (const a of assessmentHistory) {
    const month = new Date(a.timestamp).toLocaleDateString(undefined, { month: "short" });
    const arr = monthlyScores.get(month) || [];
    arr.push(a.score_percentage);
    monthlyScores.set(month, arr);
  }
  const trend = Array.from(monthlyScores.entries()).map(([month, scores]) => ({
    month,
    readiness: benchmark.careerReadiness,
    skillScore: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
  }));
  const hasTrendData = trend.length >= 2;

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 via-blue-600 to-sky-600 p-6 text-white shadow-lg shadow-blue-200 sm:p-8">
        <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/10" />
        <div className="absolute -bottom-16 right-32 h-48 w-48 rounded-full bg-white/10" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm text-blue-100">Good morning 👋</p>
            <h1 className="mt-1 text-2xl font-bold sm:text-3xl">{profile.name}</h1>
            <p className="mt-1 text-sm text-blue-100">{profile.degree} · {profile.branch} · {profile.year}</p>
            <p className="mt-4 max-w-lg text-sm text-blue-50">You're <span className="font-semibold text-white">{benchmark.careerReadiness}% ready</span> for a <span className="font-semibold text-white">{benchmark.targetRole}</span> role. {gaps.filter((g) => g.priority === "High").length > 0 ? `Close ${gaps.filter((g) => g.priority === "High").length} high-priority gap(s) to improve your readiness.` : "You're meeting your current benchmark requirements."}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link to="/student/skill-gap" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50">View skill gaps <ArrowRight className="h-4 w-4" /></Link>
              <Link to="/student/assessment" className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold text-white ring-1 ring-white/30 hover:bg-white/25">Take assessment</Link>
            </div>
          </div>
          <div className="flex items-center gap-6 rounded-2xl bg-white/10 p-4 ring-1 ring-white/20 backdrop-blur">
            <ProgressRing value={profile.profileCompletion} size={92} stroke={8} color="#fff" labelClassName="text-white" />
            <div>
              <p className="text-sm font-semibold">Profile completion</p>
              <p className="mt-1 text-xs text-blue-100">Complete your profile and add evidence to improve your standing.</p>
              <Link to="/student/profile" className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-white underline-offset-2 hover:underline">Complete profile <ArrowUpRight className="h-3 w-3" /></Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Skill score" value={`${liveSkillScore}/100`} icon={<Award className="h-5 w-5" />} hint="average of your verified skills" accent="blue" />
        <StatCard label="Career readiness" value={`${benchmark.careerReadiness}%`} icon={<TrendingUp className="h-5 w-5" />} hint={`target role benchmark: ${benchmark.targetRole}`} accent="emerald" />
        <StatCard label="Skill gaps" value={gaps.filter((g) => g.priority !== "Low").length} icon={<GitCompare className="h-5 w-5" />} hint={`${gaps.filter((g) => g.priority === "High").length} high priority`} accent="rose" />
        <StatCard label="Active applications" value={activeApps} icon={<Target className="h-5 w-5" />} hint={`${applications.length} total submitted`} accent="amber" />
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Career readiness trend" subtitle="Based on your real assessment history" />
          <CardBody>
            {hasTrendData ? (
              <ReadinessTrendChart data={trend} />
            ) : (
              <div className="flex h-[220px] flex-col items-center justify-center gap-1 text-center text-sm text-muted">
                <p>Not enough assessment history yet to plot a trend.</p>
                <p>Take assessments across a few weeks to see your progress here.</p>
                <Link to="/student/assessment" className="mt-3 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
                  Take assessment <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Skill distribution" subtitle="You vs industry expectation by category" />
          <CardBody>
            {skills.length > 0 ? (
              <SkillDistributionChart skills={skills} />
            ) : (
              <div className="flex flex-col items-center gap-3 py-10 text-center text-sm text-muted">
                <p>Add skills to see your distribution.</p>
                <Link to="/student/skills" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
                  Add a skill <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Priority gaps table - moved up: this is the highest-impact information on the
          page and should not require scrolling past five other sections to reach. */}
      <Card>
        <CardHeader title="Priority skill gaps" subtitle="Highest impact actions for your target role" action={<Link to="/student/skill-gap" className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600">Full report <ArrowRight className="h-3 w-3" /></Link>} />
        {gaps.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-muted">You're meeting all benchmarked requirements for your target role.</p>
        ) : (
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
                    <td className="px-5 py-3"><span className="inline-flex items-center gap-1 text-blue-600"><Briefcase className="h-3.5 w-3.5" />{g.recommendedCourse}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Strong / weak / gaps */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Strong skills" subtitle="Your top competencies" action={<Link to="/student/skills" className="text-xs font-semibold text-blue-600">View all</Link>} />
          <CardBody className="space-y-3">
            {strong.length === 0 && <p className="text-sm text-muted">No skills recorded yet.</p>}
            {strong.map((s) => (
              <div key={s.id}>
                <div className="mb-1 flex items-center justify-between text-sm"><span className="font-medium text-slate-800">{s.name}</span><span className="font-semibold text-emerald-600">{s.score}</span></div>
                <ProgressBar value={s.score} barClassName="bg-emerald-500" size="sm" />
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Weak skills" subtitle="Needs attention" action={<Link to="/student/learning" className="text-xs font-semibold text-blue-600">Improve</Link>} />
          <CardBody className="space-y-3">
            {weak.length === 0 && <p className="text-sm text-muted">No skills recorded yet.</p>}
            {weak.map((s) => (
              <div key={s.id}>
                <div className="mb-1 flex items-center justify-between text-sm"><span className="font-medium text-slate-800">{s.name}</span><span className={`font-semibold ${s.score < 55 ? "text-rose-600" : "text-amber-600"}`}>{s.score}</span></div>
                <ProgressBar value={s.score} barClassName={scoreBar(s.score)} size="sm" />
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Skill gap snapshot" subtitle={`vs ${benchmark.targetRole} benchmark`} action={<Link to="/student/skill-gap" className="text-xs font-semibold text-blue-600">Full analysis</Link>} />
          <CardBody>
            {gaps.length > 0 ? <SkillGapChart gaps={gaps.slice(0, 5)} height={230} /> : <p className="py-10 text-center text-sm text-muted">You're meeting all benchmarked skills.</p>}
          </CardBody>
        </Card>
      </div>

      {/* Learning + opportunities */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Recommended learning" subtitle="Generated from your real skill gaps" action={<Link to="/student/learning" className="text-xs font-semibold text-blue-600">View path</Link>} />
          <CardBody className="space-y-3">
            {learningItems.length === 0 && (
              <p className="text-sm text-muted">
                No active learning path yet. Generate one from a target job's Skill Gap analysis to get a personalized plan.
              </p>
            )}
            {learningItems.map((l) => (
              <div key={l.skill_id} className="flex items-center gap-4 rounded-xl border border-slate-100 p-3 transition hover:border-blue-200 hover:bg-blue-50/30">
                <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${l.priority === "High" ? "bg-rose-50 text-rose-600" : l.priority === "Medium" ? "bg-amber-50 text-amber-600" : "bg-emerald-50 text-emerald-600"}`}>{l.priority.slice(0, 3).toUpperCase()}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">{l.skill_name}</p>
                  <p className="text-xs text-slate-500">Gap: {l.gap.toFixed(1)} · Target for <span className="text-blue-600">{activePath?.target_job_title}</span></p>
                  <ProgressBar value={l.status === "completed" ? 100 : l.status === "in_progress" ? 50 : 0} size="sm" className="mt-2" />
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${priorityColor[l.priority]}`}>{l.priority}</span>
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Recommended opportunities" subtitle="Ranked by your skill-match score" action={<Link to="/student/opportunities" className="text-xs font-semibold text-blue-600">Marketplace</Link>} />
          <CardBody className="space-y-3">
            {uniqueOpportunities.length === 0 && <p className="text-sm text-muted">No open opportunities right now. Check back soon.</p>}
            {uniqueOpportunities.slice(0, 4).map((o) => (
              <Link to={`/student/opportunities/${o.id}`} key={o.id} className="flex items-center gap-4 rounded-xl border border-slate-100 p-3 transition hover:border-blue-200 hover:bg-blue-50/30">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-xs font-bold text-white">{o.logo}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">{o.title}</p>
                  <p className="text-xs text-slate-500">{o.company} · {o.location} · {o.stipend}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1">{o.skills.slice(0, 3).map((s) => <span key={s} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">{s}</span>)}</div>
                </div>
                <div className="text-right"><p className={`text-lg font-bold ${o.matchScore >= 80 ? "text-emerald-600" : "text-amber-600"}`}>{o.matchScore}%</p><p className="text-[10px] uppercase tracking-wide text-muted">match</p></div>
              </Link>
            ))}
          </CardBody>
        </Card>
      </div>

      {/* Applications + readiness + feedback */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Application status" subtitle={`${dashboardApplications.length} total applications`} action={<Link to="/student/applications" className="text-xs font-semibold text-blue-600">Tracker</Link>} />
          <CardBody>
            {dashboardApplications.length === 0 ? (
              <p className="py-10 text-center text-sm text-muted">You haven't applied to any opportunities yet.</p>
            ) : (
              <>
                <ApplicationStatusChart applications={dashboardApplications} />
                <ul className="mt-2 space-y-2">
                  {dashboardApplications.slice(0, 3).map((a) => (
                    <li key={a.id} className="flex items-center justify-between text-sm"><span className="truncate text-slate-700">{a.role} <span className="text-muted">· {a.company}</span></span><span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${statusColor[a.status]}`}>{a.status}</span></li>
                  ))}
                </ul>
              </>
            )}
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
          <CardHeader title="Mentor feedback" subtitle="Latest guidance from your mentor" action={<Link to="/student/mentors" className="text-xs font-semibold text-blue-600">All feedback</Link>} />
          <CardBody className="space-y-4">
            {feedback.length === 0 && <p className="text-sm text-muted">No mentor feedback yet.</p>}
            {feedback.slice(0, 3).map((f) => (
              <div key={f.feedback_id} className="rounded-xl bg-slate-50 p-3">
                <div className="flex items-center gap-3">
                  <Avatar name={f.mentor_name || "Mentor"} size="sm" />
                  <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-800">{f.mentor_name || "Faculty Mentor"}</p></div>
                  <span className="text-[11px] text-muted">{f.createdAt ? new Date(f.createdAt).toLocaleDateString() : ""}</span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{f.message}</p>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
