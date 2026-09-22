import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  ExternalLink,
  FolderCheck,
  GitCompare,
  MessageSquare,
  Send,
  ShieldAlert,
  ShieldCheck,
  User,
  XCircle,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import {
  facultyService,
  type StudentMentoringDetail,
  type MentorFeedbackItem,
} from "../../services/facultyService";

export default function FacultyStudentDetailPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const [detail, setDetail] = useState<StudentMentoringDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"skills" | "gaps" | "learning" | "evidence" | "feedback">("skills");

  // Feedback form state
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [selectedSkill, setSelectedSkill] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  // Review modal state for evidence
  const [selectedEvidence, setSelectedEvidence] = useState<any | null>(null);
  const [reviewStatus, setReviewStatus] = useState<"approved" | "rejected">("approved");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const loadStudentDetail = async () => {
    if (!studentId) return;
    try {
      setLoading(true);
      const data = await facultyService.getAssignedStudentDetail(studentId);
      setDetail(data);
    } catch (e) {
      console.error("Error loading student mentoring detail", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudentDetail();
  }, [studentId]);

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId || !feedbackMessage.trim()) return;

    try {
      setSubmittingFeedback(true);
      await facultyService.createStudentFeedback(studentId, {
        message: feedbackMessage.trim(),
        related_skill_id: selectedSkill || undefined,
      });

      setFeedbackSuccess(true);
      setFeedbackMessage("");
      setSelectedSkill("");
      setTimeout(() => setFeedbackSuccess(false), 3000);

      // Reload detail to show new feedback in timeline
      loadStudentDetail();
    } catch (err) {
      console.error("Failed to submit feedback", err);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvidence || !studentId) return;

    try {
      setReviewing(true);
      await facultyService.reviewEvidence(selectedEvidence.evidence_id || selectedEvidence.id, {
        verification_status: reviewStatus,
        verification_notes: reviewNotes,
        student_uid: studentId,
      });

      setSelectedEvidence(null);
      setReviewNotes("");
      loadStudentDetail();
    } catch (err) {
      console.error("Failed to review evidence", err);
    } finally {
      setReviewing(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageSkeleton />
      </div>
    );
  }

  if (!detail) {
    return (
      <Card className="p-12 text-center">
        <ShieldAlert className="mx-auto h-12 w-12 text-rose-500" />
        <h3 className="mt-4 text-lg font-bold text-slate-900">Student Not Found or Access Denied</h3>
        <p className="mt-1 text-sm text-slate-500">
          This student profile does not exist or is not assigned to your mentoring queue.
        </p>
        <Link
          to="/faculty"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          <ArrowLeft className="h-4 w-4" /> Return to Faculty Hub
        </Link>
      </Card>
    );
  }

  const { profile, skills, learning_paths, evidence, feedback, skill_gaps } = detail;

  return (
    <div className="space-y-8">
      {/* Navigation & Header */}
      <div>
        <Link
          to="/faculty"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Assigned Students</span>
        </Link>

        {/* Student Profile Card */}
        <Card className="p-6">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-5">
              <img
                src={profile.avatar || "https://i.pravatar.cc/150?img=12"}
                alt={profile.name}
                className="h-20 w-20 rounded-full border-2 border-blue-100 object-cover"
              />
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-bold text-slate-900">{profile.name}</h2>
                  <Badge tone="blue">Student Mentee</Badge>
                </div>
                <p className="text-sm text-slate-500">{profile.email}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
                  {profile.targetRole && (
                    <span className="rounded bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
                      Target: {profile.targetRole}
                    </span>
                  )}
                  {profile.department && (
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
                      Dept: {profile.department}
                    </span>
                  )}
                  {profile.institution && (
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
                      {profile.institution}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Metrics */}
            <div className="flex gap-4 border-t border-slate-100 pt-4 sm:border-t-0 sm:pt-0">
              <div className="text-center rounded-xl bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Skills</p>
                <p className="text-xl font-bold text-slate-900">{skills.length}</p>
              </div>
              <div className="text-center rounded-xl bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Evidence</p>
                <p className="text-xl font-bold text-slate-900">{evidence.length}</p>
              </div>
              <div className="text-center rounded-xl bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Feedback</p>
                <p className="text-xl font-bold text-blue-600">{feedback.length}</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6 overflow-x-auto">
          {[
            { id: "skills", label: "Skills & Proficiencies", icon: Award, count: skills.length },
            { id: "gaps", label: "Skill Gaps", icon: GitCompare, count: skill_gaps?.length || 0 },
            { id: "learning", label: "Learning Paths", icon: BookOpen, count: learning_paths.length },
            { id: "evidence", label: "Submitted Evidence", icon: FolderCheck, count: evidence.length },
            { id: "feedback", label: "Mentoring Feedback", icon: MessageSquare, count: feedback.length },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 border-b-2 py-3 px-1 text-sm font-semibold transition whitespace-nowrap ${
                  activeTab === tab.id
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* TAB 1: Skills */}
      {activeTab === "skills" && (
        <div className="space-y-4">
          {skills.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">No skills added yet by this student.</Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {skills.map((skill) => (
                <Card key={skill.skillId || skill.id} className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-slate-900">{skill.name}</h4>
                      <span className="text-xs text-slate-400">{skill.category || "Technical"}</span>
                    </div>
                    <Badge tone={skill.verified ? "emerald" : "slate"}>
                      {skill.verified ? "Verified" : "Self-Reported"}
                    </Badge>
                  </div>
                  <div className="mt-4">
                    <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                      <span>Proficiency Level {skill.proficiency}/5</span>
                      <span>{skill.score}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full bg-blue-600 rounded-full"
                        style={{ width: `${(skill.proficiency / 5) * 100}%` }}
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Skill Gaps */}
      {activeTab === "gaps" && (
        <div className="space-y-4">
          {!skill_gaps || skill_gaps.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">
              No active skill gaps identified for the student's current learning target.
            </Card>
          ) : (
            <div className="space-y-3">
              {skill_gaps.map((gap, idx) => (
                <Card key={idx} className="p-5 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-slate-900">{gap.skill}</h4>
                      <Badge tone={gap.priority === "High" ? "rose" : gap.priority === "Medium" ? "amber" : "slate"}>
                        {gap.priority} Priority Gap
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      Target Role: <span className="font-semibold text-slate-700">{gap.target_job}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Required: Level {gap.required_proficiency}</p>
                    <p className="text-xs font-semibold text-rose-600">Current: Level {gap.student_proficiency}</p>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Learning Paths */}
      {activeTab === "learning" && (
        <div className="space-y-4">
          {learning_paths.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">No active learning paths created.</Card>
          ) : (
            learning_paths.map((path) => (
              <Card key={path.path_id} className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-lg font-bold text-slate-900">{path.target_job_title}</h4>
                    <p className="text-xs text-slate-500">{path.target_company}</p>
                  </div>
                  <Badge tone={path.status === "active" ? "emerald" : "slate"}>
                    {path.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {path.skills.map((s: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-xs">
                      <span className="font-medium text-slate-800">{s.skill_name}</span>
                      <span className="text-slate-500">Level {s.current_proficiency} → {s.required_proficiency}</span>
                    </div>
                  ))}
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* TAB 4: Evidence */}
      {activeTab === "evidence" && (
        <div className="space-y-4">
          {evidence.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">No portfolio evidence submitted by this student.</Card>
          ) : (
            evidence.map((ev) => (
              <Card key={ev.evidence_id || ev.id} className="p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge
                        tone={
                          ev.verification_status === "approved"
                            ? "emerald"
                            : ev.verification_status === "rejected"
                            ? "rose"
                            : "amber"
                        }
                      >
                        {ev.verification_status === "approved"
                          ? "Approved"
                          : ev.verification_status === "rejected"
                          ? "Rejected"
                          : "Pending Review"}
                      </Badge>
                      <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                        {ev.type}
                      </span>
                    </div>
                    <h4 className="mt-1 text-base font-bold text-slate-900">{ev.title}</h4>
                    {ev.issuer && <p className="text-xs text-slate-500">Issuer: {ev.issuer}</p>}
                  </div>

                  <button
                    onClick={() => {
                      setSelectedEvidence(ev);
                      setReviewStatus(ev.verification_status === "approved" ? "approved" : "rejected");
                      setReviewNotes(ev.verification_notes || "");
                    }}
                    className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                  >
                    {ev.verification_status === "pending" ? "Review Evidence" : "Update Evaluation"}
                  </button>
                </div>

                {ev.description && <p className="mt-3 text-sm text-slate-600">{ev.description}</p>}

                {ev.verification_notes && (
                  <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600 border border-slate-200">
                    <span className="font-semibold text-slate-800">Faculty Review Note: </span>
                    {ev.verification_notes}
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      )}

      {/* TAB 5: Mentoring Feedback */}
      {activeTab === "feedback" && (
        <div className="space-y-6">
          {/* Post Feedback Box */}
          <Card className="p-6">
            <h3 className="text-base font-bold text-slate-900 mb-1">Provide Guidance & Feedback</h3>
            <p className="text-xs text-slate-500 mb-4">
              Send constructive guidance or recommendations directly to {profile.name}'s dashboard.
            </p>

            {feedbackSuccess && (
              <div className="mb-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
                Mentoring feedback submitted successfully!
              </div>
            )}

            <form onSubmit={handleFeedbackSubmit} className="space-y-4">
              <div>
                <textarea
                  rows={3}
                  required
                  value={feedbackMessage}
                  onChange={(e) => setFeedbackMessage(e.target.value)}
                  placeholder={`Write your recommendations or review for ${profile.name}...`}
                  className="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="sm:w-1/2">
                  <select
                    value={selectedSkill}
                    onChange={(e) => setSelectedSkill(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs text-slate-700 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">-- Link to a Skill (Optional) --</option>
                    {skills.map((s) => (
                      <option key={s.skillId || s.id} value={s.name}>
                        {s.name} (Level {s.proficiency})
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={submittingFeedback || !feedbackMessage.trim()}
                  className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                  <span>{submittingFeedback ? "Dispatching..." : "Send Guidance"}</span>
                </button>
              </div>
            </form>
          </Card>

          {/* Feedback Timeline */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500">
              Guidance History ({feedback.length})
            </h4>

            {feedback.length === 0 ? (
              <Card className="p-8 text-center text-slate-500">
                No previous feedback recorded for this student.
              </Card>
            ) : (
              feedback.map((item) => (
                <Card key={item.feedback_id || item.id} className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-semibold text-slate-900">{item.mentor_name || "Faculty Mentor"}</span>
                      {item.related_skill_id && (
                        <span className="ml-2 rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                          Skill: {item.related_skill_id}
                        </span>
                      )}
                    </div>
                    {item.createdAt && (
                      <span className="text-xs text-slate-400">
                        {new Date(item.createdAt).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">{item.message}</p>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Review Modal */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Evaluate Evidence Submission</h3>
                <p className="text-xs text-slate-500">{selectedEvidence.title}</p>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReviewSubmit} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Determination
                </label>
                <div className="mt-2 grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setReviewStatus("approved")}
                    className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-sm font-semibold transition ${
                      reviewStatus === "approved"
                        ? "border-emerald-500 bg-emerald-50 text-emerald-700 ring-2 ring-emerald-400"
                        : "border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    Approve Evidence
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewStatus("rejected")}
                    className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-sm font-semibold transition ${
                      reviewStatus === "rejected"
                        ? "border-rose-500 bg-rose-50 text-rose-700 ring-2 ring-rose-400"
                        : "border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <XCircle className="h-4 w-4 text-rose-600" />
                    Reject Evidence
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Review Notes
                </label>
                <textarea
                  rows={4}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Notes for student..."
                  className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedEvidence(null)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewing}
                  className="rounded-xl bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {reviewing ? "Submitting..." : "Save Evaluation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
