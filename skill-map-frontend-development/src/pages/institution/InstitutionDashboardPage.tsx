import { useEffect, useState } from "react";
import {
  Users,
  Award,
  BookOpen,
  FolderCheck,
  UserCheck,
  Briefcase,
  TrendingUp,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
  Building2,
  BarChart3,
  GitCompare,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { StatCard } from "../../components/ui/StatCard";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import {
  institutionService,
  type InstitutionAnalyticsResponse,
} from "../../services/institutionService";

interface Props {
  activeTab?: "overview" | "students" | "skills" | "recruitment";
}

export default function InstitutionDashboardPage({ activeTab: initialTab = "overview" }: Props) {
  const [analytics, setAnalytics] = useState<InstitutionAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTab, setCurrentTab] = useState<"overview" | "students" | "skills" | "recruitment">(initialTab);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const data = await institutionService.getAnalytics();
        setAnalytics(data);
      } catch (err) {
        console.error("Failed to load institution analytics", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageSkeleton />
      </div>
    );
  }

  if (!analytics) {
    return (
      <Card className="p-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-rose-500" />
        <h3 className="mt-4 text-lg font-bold text-slate-900">Analytics Service Unavailable</h3>
        <p className="mt-1 text-sm text-slate-500">
          Unable to retrieve real-time institutional records. Please verify server connection and permissions.
        </p>
      </Card>
    );
  }

  const {
    institution_name,
    generated_at,
    student_overview,
    skill_analytics,
    learning_analytics,
    evidence_analytics,
    mentorship_analytics,
    recruitment_analytics,
  } = analytics;

  const totalProficiencies = Object.values(skill_analytics.proficiency_distribution).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <PageHeader
          title={`${institution_name} Analytics Dashboard`}
          description="Real-time institutional competency intelligence, curricular alignment, and mentor engagement."
        />
        <span className="text-xs text-slate-400 self-start sm:self-auto">
          Updated {new Date(generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>

      {/* KPI Stat Cards Grid */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard
          label="Total Students"
          value={student_overview.total_students}
          icon={<Users className="h-5 w-5" />}
          hint={`${student_overview.active_students} active`}
          accent="indigo"
        />
        <StatCard
          label="Skills Tracked"
          value={skill_analytics.total_skills_recorded}
          icon={<Award className="h-5 w-5" />}
          hint={`${student_overview.students_with_skills} with skills`}
          accent="violet"
        />
        <StatCard
          label="Learning Paths"
          value={learning_analytics.total_learning_paths}
          icon={<BookOpen className="h-5 w-5" />}
          hint={`${student_overview.students_with_learning_paths} students`}
          accent="sky"
        />
        <StatCard
          label="Evidence Items"
          value={evidence_analytics.total_evidence_submissions}
          icon={<FolderCheck className="h-5 w-5" />}
          hint={`${evidence_analytics.evidence_by_status.approved || 0} approved`}
          accent="emerald"
        />
        <StatCard
          label="Mentorships"
          value={mentorship_analytics.active_mentor_assignments}
          icon={<UserCheck className="h-5 w-5" />}
          hint={`${mentorship_analytics.assigned_students_count} assigned`}
          accent="amber"
        />
        <StatCard
          label="Market Openings"
          value={recruitment_analytics.relevant_jobs_count}
          icon={<Briefcase className="h-5 w-5" />}
          hint={recruitment_analytics.average_match_score > 0 ? `${recruitment_analytics.average_match_score}% avg match` : "Published roles"}
          accent="indigo"
        />
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 overflow-x-auto">
          {[
            { id: "overview", label: "Overview & Health", icon: BarChart3 },
            { id: "students", label: "Student & Mentorship", icon: Users },
            { id: "skills", label: "Skills & Curricular Gaps", icon: Award },
            { id: "recruitment", label: "Industry & Market Alignment", icon: Briefcase },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id as any)}
                className={`flex items-center gap-2 border-b-2 py-3 px-1 text-sm font-semibold transition whitespace-nowrap ${
                  currentTab === tab.id
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* TAB 1: Overview & Health */}
      {currentTab === "overview" && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Proficiency Distribution */}
            <Card className="p-6">
              <h3 className="text-base font-bold text-slate-900 mb-1">Competency Proficiency Breakdown</h3>
              <p className="text-xs text-slate-500 mb-6">
                Distribution across recorded student skills (Levels 1 to 5).
              </p>

              {totalProficiencies === 0 ? (
                <div className="py-8 text-center text-sm text-slate-400">No data available</div>
              ) : (
                <div className="space-y-3">
                  {[
                    { label: "Expert (Level 5)", count: skill_analytics.proficiency_distribution["Expert"] || 0, color: "bg-indigo-600" },
                    { label: "Advanced (Level 4)", count: skill_analytics.proficiency_distribution["Advanced"] || 0, color: "bg-indigo-500" },
                    { label: "Intermediate (Level 3)", count: skill_analytics.proficiency_distribution["Intermediate"] || 0, color: "bg-indigo-400" },
                    { label: "Basic (Level 2)", count: skill_analytics.proficiency_distribution["Basic"] || 0, color: "bg-slate-400" },
                    { label: "Beginner (Level 1)", count: skill_analytics.proficiency_distribution["Beginner"] || 0, color: "bg-slate-300" },
                  ].map((level) => {
                    const pct = totalProficiencies > 0 ? Math.round((level.count / totalProficiencies) * 100) : 0;
                    return (
                      <div key={level.label}>
                        <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                          <span>{level.label}</span>
                          <span>{level.count} ({pct}%)</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                          <div className={`h-full rounded-full ${level.color}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>

            {/* Evidence Verification Health */}
            <Card className="p-6">
              <h3 className="text-base font-bold text-slate-900 mb-1">Evidence & Portfolio Evaluation Health</h3>
              <p className="text-xs text-slate-500 mb-6">
                Institutional review status across projects, certifications, and coursework.
              </p>

              {evidence_analytics.total_evidence_submissions === 0 ? (
                <div className="py-8 text-center text-sm text-slate-400">No data available</div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="rounded-xl bg-emerald-50 p-3">
                      <div className="flex items-center justify-center gap-1 text-xs font-semibold text-emerald-700">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Approved
                      </div>
                      <p className="mt-1 text-2xl font-bold text-emerald-800">
                        {evidence_analytics.evidence_by_status["approved"] || 0}
                      </p>
                    </div>
                    <div className="rounded-xl bg-amber-50 p-3">
                      <div className="flex items-center justify-center gap-1 text-xs font-semibold text-amber-700">
                        <Clock className="h-3.5 w-3.5" /> Pending
                      </div>
                      <p className="mt-1 text-2xl font-bold text-amber-800">
                        {evidence_analytics.evidence_by_status["pending"] || 0}
                      </p>
                    </div>
                    <div className="rounded-xl bg-rose-50 p-3">
                      <div className="flex items-center justify-center gap-1 text-xs font-semibold text-rose-700">
                        <XCircle className="h-3.5 w-3.5" /> Rejected
                      </div>
                      <p className="mt-1 text-2xl font-bold text-rose-800">
                        {evidence_analytics.evidence_by_status["rejected"] || 0}
                      </p>
                    </div>
                  </div>

                  {/* Submission Types */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Submissions by Type
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(evidence_analytics.evidence_by_type).map(([type, count]) => (
                        <span key={type} className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                          {type}: {count}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: Students & Mentorship */}
      {currentTab === "students" && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Cohort Participation Card */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Student Participation Metrics</h3>
            <p className="text-xs text-slate-500 mb-6">
              Active engagement across competencies and personalized curricula.
            </p>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Enrolled Students</span>
                <span className="text-base font-bold text-slate-900">{student_overview.total_students}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Active Students</span>
                <span className="text-base font-bold text-indigo-600">{student_overview.active_students}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Students with Verified Skills</span>
                <span className="text-base font-bold text-slate-900">{student_overview.students_with_skills}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Students with Learning Paths</span>
                <span className="text-base font-bold text-slate-900">{student_overview.students_with_learning_paths}</span>
              </div>
            </div>
          </Card>

          {/* Mentorship Health Card */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Faculty Mentorship Operations</h3>
            <p className="text-xs text-slate-500 mb-6">
              Active pairings, guidance notes dispatched, and pending evaluations.
            </p>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Active Pairings</span>
                <span className="text-base font-bold text-emerald-600">{mentorship_analytics.active_mentor_assignments}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Mentees Under Faculty Guidance</span>
                <span className="text-base font-bold text-slate-900">{mentorship_analytics.assigned_students_count}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Mentoring Guidance Notes Dispatched</span>
                <span className="text-base font-bold text-indigo-600">{mentorship_analytics.feedback_activity_count}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                <span className="text-sm font-medium text-slate-700">Pending Portfolio Reviews</span>
                <span className={`text-base font-bold ${mentorship_analytics.pending_evidence_reviews > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                  {mentorship_analytics.pending_evidence_reviews}
                </span>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 3: Skills & Curricular Gaps */}
      {currentTab === "skills" && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Most Common Skills */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Top Student Competencies</h3>
            <p className="text-xs text-slate-500 mb-6">
              Most frequently recorded skills and cohort average proficiency.
            </p>

            {skill_analytics.most_common_skills.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-400">No data available</div>
            ) : (
              <div className="space-y-3">
                {skill_analytics.most_common_skills.map((skill) => (
                  <div key={skill.name} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{skill.name}</p>
                      <span className="text-xs text-slate-400">{skill.category}</span>
                    </div>
                    <div className="text-right">
                      <Badge tone="indigo">{skill.count} students</Badge>
                      <p className="mt-1 text-xs text-slate-500">Avg Level {skill.average_proficiency}/5</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Curricular Skill Gaps */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Curricular Skill Gaps</h3>
            <p className="text-xs text-slate-500 mb-6">
              Skills where students exhibit deficiencies relative to market requirements.
            </p>

            {skill_analytics.common_skill_gaps.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-400">No data available</div>
            ) : (
              <div className="space-y-3">
                {skill_analytics.common_skill_gaps.map((gap, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{gap.skill}</p>
                      <span className="text-xs text-rose-600 font-semibold">
                        Average Deficiency: -{gap.average_gap} levels
                      </span>
                    </div>
                    <Badge tone="rose">{gap.affected_students} affected</Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 4: Industry & Market Alignment */}
      {currentTab === "recruitment" && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Top In-Demand Industry Skills */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Market Skill Demand</h3>
            <p className="text-xs text-slate-500 mb-6">
              Skills most frequently sought by recruiters in published opportunities.
            </p>

            {recruitment_analytics.top_demand_skills.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-400">No data available</div>
            ) : (
              <div className="space-y-3">
                {recruitment_analytics.top_demand_skills.map((d, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
                    <span className="text-sm font-bold text-slate-900">{d.skill}</span>
                    <Badge tone="emerald">{d.postings_count} postings</Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Job Match Baseline */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Institutional Match Baseline</h3>
            <p className="text-xs text-slate-500 mb-6">
              Aggregated deterministic compatibility of student skills against market roles.
            </p>

            <div className="space-y-4">
              <div className="rounded-xl bg-indigo-50 p-6 text-center">
                <p className="text-xs font-semibold uppercase tracking-wider text-indigo-700">
                  Average Candidate Match
                </p>
                <p className="mt-2 text-4xl font-extrabold text-indigo-900">
                  {recruitment_analytics.average_match_score > 0 ? `${recruitment_analytics.average_match_score}%` : "No data available"}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  Computed via Step 29 deterministic weighted algorithm across published positions.
                </p>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 text-xs">
                <span className="font-semibold text-slate-700">Active Industry Positions</span>
                <span className="font-bold text-slate-900">{recruitment_analytics.relevant_jobs_count}</span>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
