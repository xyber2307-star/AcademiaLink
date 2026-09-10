import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Award,
  BadgeCheck,
  Briefcase,
  CheckCircle2,
  Clock,
  ExternalLink,
  FolderGit2,
  Globe,
  Info,
  Link2,
  ShieldCheck,
  User,
  Users,
  XCircle,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ProgressRing } from "../../components/ui/Progress";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { recruiterService } from "../../services/recruiterService";
import { cn } from "../../utils/cn";

export default function RecruiterCandidatesPage() {
  const { jobId: routeJobId } = useParams<{ jobId?: string }>();
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>(routeJobId || "");
  const [candidatesData, setCandidatesData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Load recruiter jobs for switcher
  useEffect(() => {
    async function loadJobs() {
      try {
        const list = await recruiterService.getRecruiterJobs();
        setJobs(list);
        if (!selectedJobId && list.length > 0) {
          const firstId = list[0].id || list[0].job_id;
          setSelectedJobId(firstId);
        }
      } catch (err) {
        console.error("Failed to load recruiter jobs", err);
      }
    }
    loadJobs();
  }, []);

  // Fetch candidates for selected job
  useEffect(() => {
    async function loadCandidates() {
      if (!selectedJobId) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const data = await recruiterService.getCandidatesForJob(selectedJobId);
        setCandidatesData(data);
      } catch (err) {
        console.error("Failed to fetch job candidates", err);
        setCandidatesData(null);
      } finally {
        setLoading(false);
      }
    }
    loadCandidates();
  }, [selectedJobId]);

  if (loading) return <PageSkeleton />;

  const candidates = candidatesData?.candidates || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/recruiter/opportunities">
          <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>
            Back to Opportunities
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Candidate Match Analysis"
        description="Deterministic skill mapping comparing student proficiencies against role weights."
        actions={
          jobs.length > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500">Opportunity:</span>
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium focus:border-indigo-500 focus:outline-none"
              >
                {jobs.map((j) => (
                  <option key={j.id || j.job_id} value={j.id || j.job_id}>
                    {j.title} ({j.company})
                  </option>
                ))}
              </select>
            </div>
          )
        }
      />

      {/* Target Job Header Card */}
      {candidatesData && (
        <Card className="overflow-hidden">
          <div className="h-14 bg-gradient-to-r from-indigo-700 via-indigo-600 to-violet-700" />
          <CardBody className="relative pt-0">
            <div className="-mt-7 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {candidatesData.job_title}
                </h2>
                <p className="text-xs font-semibold text-indigo-600">
                  {candidatesData.company} • Job ID: {candidatesData.job_id}
                </p>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-100 px-4 py-2 text-right">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Matched Candidates
                </span>
                <p className="text-lg font-bold text-slate-900">
                  {candidatesData.total_candidates} Analyzed
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Algorithmic Notice */}
      <div className="flex items-start gap-3 rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-slate-600">
        <ShieldCheck className="h-5 w-5 shrink-0 text-indigo-600" />
        <div className="space-y-1">
          <p className="font-semibold text-slate-900">
            Deterministic Skill-Weighted Ranking
          </p>
          <p>
            Candidate match percentages are computed using the platform's transparent
            mathematical formula:{" "}
            <code>score = (sum(min(proficiency / required, 1.0) × weight) / total_weight) × 100</code>.
            Rankings are reproducible and free of artificial score inflation.
          </p>
        </div>
      </div>

      {/* Candidates List */}
      {candidates.length === 0 ? (
        <Card>
          <CardBody className="py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 ring-8 ring-indigo-50/50">
              <Users className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-base font-bold text-slate-900">
              No matching candidates available.
            </h3>
            <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-slate-500">
              Currently no student profiles match the minimum competency framework for this
              opportunity. As students complete verified coursework and assessments, they will
              populate here ranked by match proficiency.
            </p>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-4">
          {candidates.map((candidate: any, rankIdx: number) => {
            const matchScore = candidate.match_score || Math.round(candidate.overall_score);
            const scoreColor =
              matchScore >= 80
                ? "#10b981"
                : matchScore >= 60
                ? "#4f46e5"
                : matchScore >= 40
                ? "#f59e0b"
                : "#ef4444";

            return (
              <Card key={candidate.candidate_id} className="hover:border-slate-300 transition">
                <CardBody className="space-y-5">
                  {/* Top Candidate Summary */}
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-4">
                      <ProgressRing
                        value={matchScore}
                        size={72}
                        stroke={7}
                        color={scoreColor}
                        sub="Match"
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-700">
                            #{rankIdx + 1}
                          </span>
                          <h3 className="text-base font-bold text-slate-900">
                            {candidate.name}
                          </h3>
                        </div>
                        <p className="text-xs text-slate-500">
                          {candidate.targetRole || "Student"} • Candidate ID:{" "}
                          <span className="font-mono">{candidate.candidate_id.slice(0, 10)}</span>
                        </p>
                        {candidate.email && (
                          <p className="text-xs text-slate-400">{candidate.email}</p>
                        )}
                      </div>
                    </div>

                    <div className="rounded-xl bg-slate-50 border border-slate-100 p-3 text-xs text-slate-600 sm:max-w-xs">
                      <p className="font-semibold text-slate-800">Match Rationale:</p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">
                        {candidate.explanation}
                      </p>
                    </div>
                  </div>

                  {/* Skills Grid */}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 border-t border-slate-100 pt-4">
                    {/* Matched Skills */}
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">
                        ✓ Fully Matched ({candidate.matched_skills?.length || 0})
                      </span>
                      <div className="mt-2 space-y-1.5">
                        {candidate.matched_skills?.length > 0 ? (
                          candidate.matched_skills.map((s: any, i: number) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg bg-emerald-50/60 px-2.5 py-1 text-xs text-emerald-800"
                            >
                              <span className="font-semibold">{s.skill}</span>
                              <span>
                                {s.current_proficiency.toFixed(1)} / {s.required_proficiency.toFixed(1)} ({s.weight}x)
                              </span>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-400 italic">None</p>
                        )}
                      </div>
                    </div>

                    {/* Partial Skills */}
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700">
                        ⚡ Partial Skills ({candidate.partial_skills?.length || 0})
                      </span>
                      <div className="mt-2 space-y-1.5">
                        {candidate.partial_skills?.length > 0 ? (
                          candidate.partial_skills.map((s: any, i: number) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg bg-amber-50/60 px-2.5 py-1 text-xs text-amber-800"
                            >
                              <span className="font-semibold">{s.skill}</span>
                              <span>
                                {s.current_proficiency.toFixed(1)} / {s.required_proficiency.toFixed(1)} (-{s.gap_amount.toFixed(1)})
                              </span>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-400 italic">None</p>
                        )}
                      </div>
                    </div>

                    {/* Missing Skills */}
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-rose-700">
                        ✕ Missing Skills ({candidate.missing_skills?.length || 0})
                      </span>
                      <div className="mt-2 space-y-1.5">
                        {candidate.missing_skills?.length > 0 ? (
                          candidate.missing_skills.map((s: any, i: number) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg bg-rose-50/60 px-2.5 py-1 text-xs text-rose-800"
                            >
                              <span className="font-semibold">{s.skill}</span>
                              <span>Need lvl {s.required_proficiency.toFixed(1)} ({s.weight}x)</span>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-400 italic">None</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Evidence & Portfolio Showcase */}
                  {candidate.evidence && candidate.evidence.length > 0 && (
                    <div className="border-t border-slate-100 pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <FolderGit2 className="h-4 w-4 text-indigo-600" />
                        <span className="text-xs font-bold text-slate-800">
                          Candidate Portfolio & Supporting Evidence
                        </span>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                        {candidate.evidence.map((ev: any) => {
                          const isApproved = ev.verification_status === "approved";
                          const isPending = ev.verification_status === "pending";
                          const isRejected = ev.verification_status === "rejected";

                          return (
                            <div
                              key={ev.evidence_id}
                              className="rounded-xl border border-slate-200 bg-slate-50/50 p-3 text-xs space-y-1.5"
                            >
                              <div className="flex items-start justify-between gap-1">
                                <span className="font-bold text-slate-800 line-clamp-1">
                                  {ev.title}
                                </span>
                                <Badge
                                  tone={isApproved ? "emerald" : isPending ? "amber" : "rose"}
                                  className="text-[10px] px-1.5 py-0 capitalize shrink-0"
                                >
                                  {isApproved && <CheckCircle2 className="mr-0.5 h-2.5 w-2.5" />}
                                  {isPending && <Clock className="mr-0.5 h-2.5 w-2.5" />}
                                  {isRejected && <XCircle className="mr-0.5 h-2.5 w-2.5" />}
                                  {ev.verification_status === "pending"
                                    ? "Pending"
                                    : ev.verification_status}
                                </Badge>
                              </div>
                              {ev.issuer && (
                                <p className="text-[11px] text-indigo-600 font-medium">
                                  {ev.issuer}
                                </p>
                              )}
                              {ev.skill_ids && ev.skill_ids.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {ev.skill_ids.map((sk: string) => (
                                    <span
                                      key={sk}
                                      className="rounded bg-white border border-slate-200 px-1.5 py-0.2 text-[10px] text-slate-600"
                                    >
                                      {sk}
                                    </span>
                                  ))}
                                </div>
                              )}
                              <div className="flex items-center gap-2 pt-1">
                                {ev.project_url && (
                                  <a
                                    href={ev.project_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-indigo-600 hover:underline"
                                  >
                                    <Globe className="h-3 w-3" />
                                    Demo
                                  </a>
                                )}
                                {ev.source_url && (
                                  <a
                                    href={ev.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-slate-600 hover:underline"
                                  >
                                    <Link2 className="h-3 w-3" />
                                    Source
                                  </a>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </CardBody>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
