import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Briefcase,
  CheckCircle2,
  Clock,
  ExternalLink,
  Flame,
  Info,
  Target,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { ProgressBar, ProgressRing } from "../../components/ui/Progress";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { studentService } from "../../services/studentService";
import { cn } from "../../utils/cn";

export default function LearningPathPage() {
  const [paths, setPaths] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPathId, setSelectedPathId] = useState<string | null>(null);
  const [updatingSkillId, setUpdatingSkillId] = useState<string | null>(null);

  const fetchPaths = async () => {
    try {
      setLoading(true);
      const data = await studentService.getLearningPaths();
      setPaths(data);
      if (data.length > 0 && !selectedPathId) {
        setSelectedPathId(data[0].path_id);
      }
    } catch (err) {
      console.error("Failed to load learning paths", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaths();
  }, []);

  const currentPath = useMemo(() => {
    if (!paths.length) return null;
    return paths.find((p) => p.path_id === selectedPathId) || paths[0];
  }, [paths, selectedPathId]);

  const handleStatusChange = async (
    skillId: string,
    newStatus: "not_started" | "in_progress" | "completed"
  ) => {
    if (!currentPath) return;
    setUpdatingSkillId(skillId);
    try {
      const updated = await studentService.updateLearningPathSkill(
        currentPath.path_id,
        skillId,
        newStatus
      );
      setPaths((prev) =>
        prev.map((p) => (p.path_id === updated.path_id ? updated : p))
      );
    } catch (err) {
      console.error("Failed to update skill status", err);
    } finally {
      setUpdatingSkillId(null);
    }
  };

  if (loading) return <PageSkeleton />;

  if (!paths.length || !currentPath) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Personalized Learning Paths"
          description="Targeted competency roadmaps derived from job requirement skill gaps."
        />
        <Card>
          <CardBody className="py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 ring-8 ring-blue-50/50">
              <BookOpen className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-base font-bold text-slate-900">
              No Active Learning Paths
            </h3>
            <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-slate-500">
              You haven't generated a personalized learning roadmap yet. Browse open
              opportunities, view your skill gap breakdown, and click "Create Learning
              Path" to formulate a targeted study roadmap.
            </p>
            <div className="mt-6">
              <Link to="/student/opportunities">
                <Button icon={<ArrowRight className="h-4 w-4" />}>
                  Explore Opportunities
                </Button>
              </Link>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  const skills = currentPath.skills || [];
  const completedCount = skills.filter((s: any) => s.status === "completed").length;
  const inProgressCount = skills.filter((s: any) => s.status === "in_progress").length;
  const highPriorityCount = skills.filter((s: any) => s.priority === "High").length;
  const completionPercent = skills.length
    ? Math.round((completedCount / skills.length) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Personalized Learning Paths"
        description="Targeted competency roadmaps derived from job requirement skill gaps."
        actions={
          <Link to="/student/opportunities">
            <Button variant="outline" size="sm" icon={<Briefcase className="h-4 w-4" />}>
              View Opportunities
            </Button>
          </Link>
        }
      />

      {/* Path Selector tabs if multiple paths */}
      {paths.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {paths.map((p) => (
            <button
              key={p.path_id}
              onClick={() => setSelectedPathId(p.path_id)}
              className={cn(
                "whitespace-nowrap rounded-xl px-4 py-2 text-xs font-semibold transition-all",
                p.path_id === currentPath.path_id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
              )}
            >
              {p.target_job_title} ({p.target_company})
            </button>
          ))}
        </div>
      )}

      {/* Target Job Roadmap Header */}
      <Card className="overflow-hidden">
        <div className="h-16 bg-gradient-to-r from-blue-700 via-blue-600 to-sky-700" />
        <CardBody className="relative pt-0">
          <div className="-mt-8 flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-lg font-bold text-white shadow-md ring-4 ring-white">
                {currentPath.target_company.slice(0, 2).toUpperCase()}
              </div>
              <div className="pt-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-slate-900">
                    {currentPath.target_job_title}
                  </h2>
                  <Badge tone={currentPath.status === "active" ? "blue" : "slate"}>
                    {currentPath.status}
                  </Badge>
                </div>
                <p className="text-xs font-medium text-blue-600">
                  {currentPath.target_company}
                </p>
                <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                  <span>Target Role ID: {currentPath.target_job_id}</span>
                  <span>•</span>
                  <Link
                    to={`/student/opportunities/${currentPath.target_job_id}`}
                    className="inline-flex items-center gap-1 font-medium text-blue-600 hover:underline"
                  >
                    Opportunity Details
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            </div>

            {/* Score comparison & Progress */}
            <div className="flex flex-wrap items-center gap-6 rounded-2xl border border-slate-100 bg-slate-50/75 p-4">
              <div className="flex items-center gap-3">
                <ProgressRing
                  value={Math.round(currentPath.overall_match_before || 0)}
                  size={76}
                  stroke={7}
                  sub="Initial"
                />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    Match Before
                  </p>
                  <p className="text-sm font-bold text-slate-800">
                    {Math.round(currentPath.overall_match_before || 0)}%
                  </p>
                </div>
              </div>

              <ArrowRight className="hidden h-5 w-5 text-slate-400 sm:block" />

              <div className="flex items-center gap-3">
                <ProgressRing
                  value={100}
                  size={76}
                  stroke={7}
                  color="#10b981"
                  sub="Target"
                />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    Projected Match
                  </p>
                  <p className="text-sm font-bold text-emerald-600">100%</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 border-t border-slate-100 pt-4">
            <div className="flex items-center justify-between text-xs text-slate-600">
              <span className="font-medium">
                Syllabus Progress: {completedCount} of {skills.length} skills mastered
              </span>
              <span className="font-bold text-blue-600">{completionPercent}%</span>
            </div>
            <ProgressBar value={completionPercent} className="mt-2" size="sm" />
          </div>
        </CardBody>
      </Card>

      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Skills to Develop"
          value={skills.length}
          icon={<Target className="h-5 w-5" />}
          accent="blue"
          hint="Identified from job gaps"
        />
        <StatCard
          label="High Priority"
          value={highPriorityCount}
          icon={<Flame className="h-5 w-5" />}
          accent="rose"
          hint="Score ≥ 4.0 (Focus first)"
        />
        <StatCard
          label="In Progress"
          value={inProgressCount}
          icon={<Clock className="h-5 w-5" />}
          accent="amber"
          hint="Currently studying"
        />
        <StatCard
          label="Completed"
          value={completedCount}
          icon={<CheckCircle2 className="h-5 w-5" />}
          accent="emerald"
          hint="Study items finished"
        />
      </div>

      {/* Integrity Notice Banner */}
      <div className="flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50/50 p-4 text-xs text-slate-600">
        <Info className="h-5 w-5 shrink-0 text-blue-600" />
        <div className="space-y-1">
          <p className="font-semibold text-slate-900">
            Study Progress vs. Verified Competencies
          </p>
          <p>
            Tracking syllabus completion here records your personal study progress towards
            this opportunity. Official verified proficiency levels in your skill profile
            remain strictly gated by verified assessments and mentor sign-offs.
          </p>
        </div>
      </div>

      {/* Prioritized Skill Roadmap */}
      <Card>
        <CardHeader
          title="Prioritized Learning Roadmap"
          subtitle="Ranked mathematically by gap size, job weighting, and missing skill status."
        />
        <CardBody className="divide-y divide-slate-100 pt-0">
          {skills.map((item: any) => {
            const isUpdating = updatingSkillId === item.skill_id;
            const priorityTone =
              item.priority === "High"
                ? "rose"
                : item.priority === "Medium"
                ? "amber"
                : "slate";

            return (
              <div
                key={item.skill_id}
                className="flex flex-col gap-4 py-5 first:pt-3 last:pb-3 lg:flex-row lg:items-center lg:justify-between"
              >
                <div className="space-y-2 lg:max-w-2xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">
                      {item.skill_name}
                    </span>
                    <Badge tone={priorityTone}>{item.priority} Priority</Badge>
                    <Badge tone="blue">
                      Score: {item.priority_score.toFixed(2)}
                    </Badge>
                    <span className="text-xs text-slate-400">
                      Weight: {item.job_weight.toFixed(1)}x
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600">
                    <span className="inline-flex items-center gap-1.5">
                      <span className="font-medium text-slate-400">Current Level:</span>
                      <span className="font-semibold text-slate-700">
                        {item.current_proficiency.toFixed(1)} / 5.0
                      </span>
                    </span>
                    <span className="text-slate-300">→</span>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="font-medium text-slate-400">Target Required:</span>
                      <span className="font-semibold text-blue-700">
                        {item.required_proficiency.toFixed(1)} / 5.0
                      </span>
                    </span>
                    <span className="inline-flex items-center gap-1 text-rose-600 font-semibold">
                      (-{item.gap.toFixed(1)} gap)
                    </span>
                  </div>

                  <p className="text-xs leading-relaxed text-slate-500">
                    {item.reason}
                  </p>
                </div>

                {/* Status Switcher */}
                <div className="flex items-center gap-1 self-start rounded-xl border border-slate-200 bg-slate-50 p-1 lg:self-center">
                  {(
                    [
                      { key: "not_started", label: "Not Started" },
                      { key: "in_progress", label: "In Progress" },
                      { key: "completed", label: "Completed" },
                    ] as const
                  ).map((s) => (
                    <button
                      key={s.key}
                      disabled={isUpdating}
                      onClick={() => handleStatusChange(item.skill_id, s.key)}
                      className={cn(
                        "rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                        item.status === s.key
                          ? s.key === "completed"
                            ? "bg-emerald-600 text-white shadow-sm"
                            : s.key === "in_progress"
                            ? "bg-amber-600 text-white shadow-sm"
                            : "bg-white text-slate-800 shadow-sm"
                          : "text-slate-500 hover:text-slate-800"
                      )}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </CardBody>
      </Card>

      {/* Verified Learning Resources Section */}
      <Card>
        <CardHeader
          title="Curriculum & Learning Resources"
          subtitle="Accredited university courseware and enterprise learning modules."
        />
        <CardBody className="pt-2">
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 ring-8 ring-amber-50/50">
              <AlertCircle className="h-6 w-6" />
            </div>
            <p className="mt-3 text-sm font-semibold text-slate-800">
              No verified learning resources available yet.
            </p>
            <p className="mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              AcademiaLINK rigorously vets institutional syllabi and corporate training
              curriculums. Unverified third-party course links are strictly prohibited to
              prevent fabricated credentials. Verified university courses will appear here
              as campus departments publish accredited modules.
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
