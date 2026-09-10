import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Building2,
  MapPin,
  Briefcase,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Flame,
  Sparkles,
  ExternalLink,
  Target,
  BookOpen,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ProgressRing, ProgressBar } from "../../components/ui/Progress";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { PageHeader } from "../../components/ui/PageHeader";
import { studentService } from "../../services/studentService";
import { applicationService } from "../../services/applicationService";

interface SkillItem {
  skill: string;
  current_proficiency: number;
  required_proficiency: number;
  gap_amount: number;
  gap_category: "matched" | "partial" | "missing";
  weight: number;
  skill_score: number;
  weighted_score: number;
  priority: "High" | "Medium" | "Low";
}

interface MatchAnalysis {
  job_id: string;
  job_title: string;
  company: string;
  overall_score: number;
  match_score: number;
  total_weight: number;
  total_required: number;
  total_matched: number;
  matched_skills: SkillItem[];
  partial_skills: SkillItem[];
  missing_skills: SkillItem[];
  prioritized_gaps: SkillItem[];
  explanation: string;
}

export default function OpportunityDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<any | null>(null);
  const [match, setMatch] = useState<MatchAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingPath, setGeneratingPath] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApply = async () => {
    if (!id) return;
    try {
      setApplying(true);
      await applicationService.applyForJob(id);
      navigate("/student/applications");
    } catch (err: any) {
      alert(err.message || "Failed to submit job application.");
    } finally {
      setApplying(false);
    }
  };

  const handleCreateLearningPath = async () => {
    if (!id) return;
    try {
      setGeneratingPath(true);
      await studentService.createLearningPath(id);
      navigate("/student/learning");
    } catch (err) {
      console.error("Failed to create learning path", err);
    } finally {
      setGeneratingPath(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadData(id);
    }
  }, [id]);

  const loadData = async (jobId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [jobData, matchData] = await Promise.all([
        studentService.getJob(jobId).catch(() => null),
        studentService.getJobMatch(jobId).catch(() => null),
      ]);
      setJob(jobData);
      setMatch(matchData);
    } catch (err: any) {
      console.error("Failed to load opportunity details", err);
      setError(err?.message || "Failed to load opportunity data.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <PageSkeleton />;

  if (error || (!job && !match)) {
    return (
      <div className="space-y-6">
        <Link to="/student/opportunities">
          <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>
            Back to Opportunities
          </Button>
        </Link>
        <Card>
          <CardBody className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700">Opportunity Not Found</p>
            <p className="mt-1 text-xs text-slate-500">
              The opportunity you requested could not be retrieved.
            </p>
            <Link to="/student/opportunities" className="mt-4 inline-block">
              <Button size="sm">Browse Opportunities</Button>
            </Link>
          </CardBody>
        </Card>
      </div>
    );
  }

  const title = job?.title || match?.job_title || "Opportunity Details";
  const company = job?.company || match?.company || "Company";
  const location = job?.location || "Remote";
  const empType = job?.employment_type || job?.type || "Internship";
  const stipend = job?.stipend || "Competitive";
  const description = job?.description || "No description provided.";
  const overallScore = match ? Math.round(match.overall_score || match.match_score || 0) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/student/opportunities">
          <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>
            All Opportunities
          </Button>
        </Link>
      </div>

      {/* Header Banner */}
      <Card className="overflow-hidden">
        <div className="h-20 bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-600" />
        <CardBody className="relative pt-0">
          <div className="-mt-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex items-end gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 text-xl font-bold text-white shadow-lg ring-4 ring-white">
                {company.slice(0, 2).toUpperCase()}
              </div>
              <div className="pb-1">
                <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
                <p className="text-sm font-medium text-indigo-600">{company}</p>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {location}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="h-3.5 w-3.5" />
                    {empType}
                  </span>
                  <span className="font-semibold text-slate-700">{stipend}</span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pb-1">
              <Button
                variant="outline"
                icon={<BookOpen className="h-4 w-4" />}
                loading={generatingPath}
                onClick={handleCreateLearningPath}
              >
                Create Learning Path
              </Button>
              <Button
                variant="primary"
                loading={applying}
                onClick={handleApply}
              >
                Apply Now
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Match Engine Analysis Section */}
      {match && (
        <Card className="border-indigo-100 bg-gradient-to-br from-indigo-50/40 via-white to-violet-50/30">
          <CardHeader
            title="Skill Matching & Gap Analysis"
            subtitle="Calculated in real time by comparing your verified student profile against job requirements."
            action={
              <Badge tone={overallScore >= 75 ? "emerald" : overallScore >= 50 ? "amber" : "rose"}>
                {overallScore}% Match
              </Badge>
            }
          />
          <CardBody className="space-y-6">
            <div className="grid gap-6 md:grid-cols-[auto_1fr] md:items-center">
              <div className="flex flex-col items-center justify-center rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200/80">
                <ProgressRing
                  value={overallScore}
                  size={110}
                  stroke={10}
                  color={overallScore >= 75 ? "#10b981" : overallScore >= 50 ? "#f59e0b" : "#f43f5e"}
                  sub="Match"
                />
                <p className="mt-2 text-xs font-semibold text-slate-700">Weighted Match Score</p>
              </div>

              <div className="space-y-3">
                <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200/80">
                  <p className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                    Why am I or am I not a good match?
                  </p>
                  <p className="mt-1 text-sm text-slate-700 leading-relaxed font-medium">
                    {match.explanation}
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-xl bg-emerald-50/70 p-3 text-center ring-1 ring-emerald-200/60">
                    <p className="text-[11px] font-medium text-emerald-800">Matched</p>
                    <p className="text-lg font-bold text-emerald-700">
                      {match.matched_skills.length}
                    </p>
                  </div>
                  <div className="rounded-xl bg-amber-50/70 p-3 text-center ring-1 ring-amber-200/60">
                    <p className="text-[11px] font-medium text-amber-800">Partial</p>
                    <p className="text-lg font-bold text-amber-700">
                      {match.partial_skills.length}
                    </p>
                  </div>
                  <div className="rounded-xl bg-rose-50/70 p-3 text-center ring-1 ring-rose-200/60">
                    <p className="text-[11px] font-medium text-rose-800">Missing</p>
                    <p className="text-lg font-bold text-rose-700">
                      {match.missing_skills.length}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Categorized Skills Breakdown */}
            <div className="grid gap-4 md:grid-cols-3">
              {/* Matched */}
              <div className="rounded-xl border border-emerald-100 bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-emerald-700">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Matched Skills ({match.matched_skills.length})</span>
                </div>
                <div className="mt-3 space-y-2">
                  {match.matched_skills.map((s) => (
                    <div
                      key={s.skill}
                      className="flex items-center justify-between rounded-lg bg-emerald-50/50 p-2 text-xs"
                    >
                      <span className="font-semibold text-slate-800">{s.skill}</span>
                      <span className="text-emerald-700 font-medium">
                        Level {s.current_proficiency} / Req {s.required_proficiency}
                      </span>
                    </div>
                  ))}
                  {match.matched_skills.length === 0 && (
                    <p className="text-xs text-slate-400 italic">No fully matched skills yet</p>
                  )}
                </div>
              </div>

              {/* Partial */}
              <div className="rounded-xl border border-amber-100 bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-amber-700">
                  <AlertCircle className="h-4 w-4" />
                  <span>Partial Matches ({match.partial_skills.length})</span>
                </div>
                <div className="mt-3 space-y-2">
                  {match.partial_skills.map((s) => (
                    <div
                      key={s.skill}
                      className="flex items-center justify-between rounded-lg bg-amber-50/50 p-2 text-xs"
                    >
                      <span className="font-semibold text-slate-800">{s.skill}</span>
                      <span className="text-amber-700 font-medium">
                        Level {s.current_proficiency} / Req {s.required_proficiency} (-{s.gap_amount})
                      </span>
                    </div>
                  ))}
                  {match.partial_skills.length === 0 && (
                    <p className="text-xs text-slate-400 italic">No partial matches</p>
                  )}
                </div>
              </div>

              {/* Missing */}
              <div className="rounded-xl border border-rose-100 bg-white p-4">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-rose-700">
                  <XCircle className="h-4 w-4" />
                  <span>Missing Skills ({match.missing_skills.length})</span>
                </div>
                <div className="mt-3 space-y-2">
                  {match.missing_skills.map((s) => (
                    <div
                      key={s.skill}
                      className="flex items-center justify-between rounded-lg bg-rose-50/50 p-2 text-xs"
                    >
                      <span className="font-semibold text-slate-800">{s.skill}</span>
                      <span className="text-rose-700 font-medium">
                        Missing (Req Level {s.required_proficiency})
                      </span>
                    </div>
                  ))}
                  {match.missing_skills.length === 0 && (
                    <p className="text-xs text-slate-400 italic">No missing skills</p>
                  )}
                </div>
              </div>
            </div>

            {/* Prioritized Learning Gaps Table */}
            {match.prioritized_gaps.length > 0 && (
              <div className="border-t border-slate-100 pt-4">
                <div className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-rose-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Prioritized Skill Gaps (Ordered by Gap Size & Weight)
                  </h3>
                </div>
                <p className="mt-0.5 text-xs text-slate-500">
                  Focus on these competencies first to maximize your candidacy score.
                </p>

                <div className="mt-3 overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500">
                      <tr>
                        <th className="px-4 py-2.5 font-semibold">Skill</th>
                        <th className="px-4 py-2.5 font-semibold">Status</th>
                        <th className="px-4 py-2.5 font-semibold">Current</th>
                        <th className="px-4 py-2.5 font-semibold">Required</th>
                        <th className="px-4 py-2.5 font-semibold">Gap</th>
                        <th className="px-4 py-2.5 font-semibold">Job Weight</th>
                        <th className="px-4 py-2.5 font-semibold">Priority</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {match.prioritized_gaps.map((g) => (
                        <tr key={g.skill} className="hover:bg-slate-50/50">
                          <td className="px-4 py-2.5 font-semibold text-slate-800">{g.skill}</td>
                          <td className="px-4 py-2.5">
                            <Badge tone={g.gap_category === "partial" ? "amber" : "rose"}>
                              {g.gap_category}
                            </Badge>
                          </td>
                          <td className="px-4 py-2.5 text-slate-600">
                            {g.current_proficiency > 0 ? `Level ${g.current_proficiency}` : "0"}
                          </td>
                          <td className="px-4 py-2.5 text-slate-600">Level {g.required_proficiency}</td>
                          <td className="px-4 py-2.5 font-bold text-rose-600">-{g.gap_amount}</td>
                          <td className="px-4 py-2.5 text-slate-600">{g.weight.toFixed(1)}x</td>
                          <td className="px-4 py-2.5">
                            <span
                              className={`rounded-full px-2 py-0.5 font-medium ${
                                g.priority === "High"
                                  ? "bg-rose-100 text-rose-700"
                                  : g.priority === "Medium"
                                  ? "bg-amber-100 text-amber-700"
                                  : "bg-slate-100 text-slate-700"
                              }`}
                            >
                              {g.priority}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Job Description & Required Skills */}
      <Card>
        <CardHeader title="Role Overview & Requirements" />
        <CardBody className="space-y-5">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">About the Role</h3>
            <p className="mt-2 text-sm text-slate-700 leading-relaxed whitespace-pre-line">
              {description}
            </p>
          </div>

          {job?.preferred_skills && job.preferred_skills.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Preferred Skills
              </h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {job.preferred_skills.map((p: string) => (
                  <span
                    key={p}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700 font-medium"
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
