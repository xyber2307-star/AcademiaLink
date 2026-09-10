import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users,
  ShieldCheck,
  MessageSquare,
  ArrowUpRight,
  Clock,
  CheckCircle2,
  XCircle,
  ExternalLink,
  BookOpen,
  Award,
  Sparkles,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { StatCard } from "../../components/ui/StatCard";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import {
  facultyService,
  type AssignedStudentSummary,
  type PendingEvidenceItem,
} from "../../services/facultyService";

export default function FacultyDashboardPage() {
  const [students, setStudents] = useState<AssignedStudentSummary[]>([]);
  const [pendingEvidence, setPendingEvidence] = useState<PendingEvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"students" | "evidence">("students");

  // Review modal state
  const [selectedEvidence, setSelectedEvidence] = useState<PendingEvidenceItem | null>(null);
  const [reviewStatus, setReviewStatus] = useState<"approved" | "rejected">("approved");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [reviewMessage, setReviewMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [stList, evList] = await Promise.all([
        facultyService.getAssignedStudents(),
        facultyService.getPendingEvidence(),
      ]);
      setStudents(stList);
      setPendingEvidence(evList);
    } catch (e) {
      console.error("Error loading faculty dashboard data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvidence) return;

    try {
      setReviewing(true);
      setReviewMessage(null);
      await facultyService.reviewEvidence(selectedEvidence.evidence_id, {
        verification_status: reviewStatus,
        verification_notes: reviewNotes,
        student_uid: selectedEvidence.user_id,
      });

      setReviewMessage({
        type: "success",
        text: `Evidence marked as ${reviewStatus} successfully!`,
      });

      setTimeout(() => {
        setSelectedEvidence(null);
        setReviewNotes("");
        setReviewMessage(null);
        loadData();
      }, 1200);
    } catch (err: any) {
      setReviewMessage({
        type: "error",
        text: err.message || "Failed to submit review.",
      });
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

  const totalAssigned = students.length;
  const totalPendingEvidence = pendingEvidence.length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <PageHeader
        title="Faculty & Mentor Hub"
        subtitle="Manage assigned students, evaluate submitted portfolio evidence, and deliver personalized mentoring."
      />

      {/* Stats Overview */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Assigned Students"
          value={totalAssigned}
          icon={<Users className="h-5 w-5" />}
          hint={totalAssigned === 0 ? "No active assignments" : "Active student mentees"}
          accent="indigo"
        />
        <StatCard
          label="Pending Evidence"
          value={totalPendingEvidence}
          icon={<ShieldCheck className="h-5 w-5" />}
          hint={totalPendingEvidence > 0 ? "Requires faculty evaluation" : "Queue is fully up to date"}
          accent={totalPendingEvidence > 0 ? "amber" : "emerald"}
        />
        <StatCard
          label="Active Cohort"
          value="Academic"
          icon={<Award className="h-5 w-5" />}
          hint="Institution verified role"
          accent="violet"
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("students")}
            className={`flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-semibold transition ${
              activeTab === "students"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
            }`}
          >
            <Users className="h-4 w-4" />
            Assigned Students
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {totalAssigned}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("evidence")}
            className={`flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-semibold transition ${
              activeTab === "evidence"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            Pending Reviews
            {totalPendingEvidence > 0 && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
                {totalPendingEvidence}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* TAB CONTENT: Assigned Students */}
      {activeTab === "students" && (
        <div className="space-y-6">
          {students.length === 0 ? (
            <Card className="p-12 text-center">
              <Users className="mx-auto h-12 w-12 text-slate-300" />
              <h3 className="mt-4 text-base font-semibold text-slate-900">No students assigned.</h3>
              <p className="mt-1 text-sm text-slate-500">
                You currently do not have any students assigned to your mentoring queue. Assignments are provisioned by your institution administrator.
              </p>
            </Card>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {students.map((student) => (
                <Card key={student.student_uid} className="flex flex-col justify-between p-6 transition hover:shadow-md">
                  <div>
                    <div className="flex items-start gap-4">
                      <img
                        src={student.avatar || "https://i.pravatar.cc/150?img=12"}
                        alt={student.name}
                        className="h-14 w-14 rounded-full border-2 border-slate-100 object-cover"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="truncate text-base font-bold text-slate-900">{student.name}</h4>
                        <p className="truncate text-xs text-slate-500">{student.email}</p>
                        {student.targetRole && (
                          <span className="mt-1.5 inline-block rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                            {student.targetRole}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-5 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-center">
                      <div className="rounded-lg bg-slate-50 p-2.5">
                        <p className="text-xs text-slate-500">Skills Tracked</p>
                        <p className="mt-1 text-lg font-bold text-slate-900">{student.skill_count}</p>
                      </div>
                      <div className="rounded-lg bg-slate-50 p-2.5">
                        <p className="text-xs text-slate-500">Pending Review</p>
                        <p className={`mt-1 text-lg font-bold ${student.pending_evidence_count > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                          {student.pending_evidence_count}
                        </p>
                      </div>
                    </div>

                    {(student.department || student.institution) && (
                      <p className="mt-3 truncate text-xs text-slate-400">
                        {[student.department, student.institution].filter(Boolean).join(" • ")}
                      </p>
                    )}
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-100">
                    <Link
                      to={`/faculty/students/${student.student_uid}`}
                      className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700"
                    >
                      <span>View Mentoring Dossier</span>
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: Pending Evidence Queue */}
      {activeTab === "evidence" && (
        <div className="space-y-6">
          {pendingEvidence.length === 0 ? (
            <Card className="p-12 text-center">
              <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-400" />
              <h3 className="mt-4 text-base font-semibold text-slate-900">No evidence awaiting review.</h3>
              <p className="mt-1 text-sm text-slate-500">
                All submissions from your assigned student mentees have been evaluated.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {pendingEvidence.map((item) => (
                <Card key={item.evidence_id} className="p-6">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge tone="amber">Pending Evaluation</Badge>
                        <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">
                          {item.type}
                        </span>
                      </div>
                      <h4 className="mt-1 text-lg font-bold text-slate-900">{item.title}</h4>
                      <p className="text-xs text-slate-500">
                        Submitted by <span className="font-semibold text-slate-700">{item.student_name}</span> ({item.student_email})
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setSelectedEvidence(item)}
                        className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700"
                      >
                        Evaluate Submission
                      </button>
                    </div>
                  </div>

                  {item.description && (
                    <p className="mt-3 text-sm text-slate-600">{item.description}</p>
                  )}

                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {item.skill_ids && item.skill_ids.map((skill, idx) => (
                      <span
                        key={idx}
                        className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700"
                      >
                        {skill}
                      </span>
                    ))}
                    {item.project_url && (
                      <a
                        href={item.project_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:underline"
                      >
                        <span>Demo</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:underline"
                      >
                        <span>Repository</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Review Modal */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Evaluate Student Evidence</h3>
                <p className="text-xs text-slate-500">
                  {selectedEvidence.title} • {selectedEvidence.student_name}
                </p>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            {reviewMessage && (
              <div
                className={`mt-4 rounded-xl p-3 text-sm ${
                  reviewMessage.type === "success"
                    ? "bg-emerald-50 text-emerald-800"
                    : "bg-rose-50 text-rose-800"
                }`}
              >
                {reviewMessage.text}
              </div>
            )}

            <form onSubmit={handleReviewSubmit} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Review Determination
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
                  Faculty Review Notes
                </label>
                <textarea
                  rows={4}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Provide constructive feedback, verification rationale, or next step recommendations..."
                  className="mt-1.5 w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {reviewing ? "Submitting..." : "Confirm Evaluation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
