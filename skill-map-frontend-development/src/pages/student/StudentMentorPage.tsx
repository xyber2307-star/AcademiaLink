import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  UserCheck,
  ShieldCheck,
  MessageSquare,
  ArrowRight,
  CheckCircle2,
  Clock,
  XCircle,
  FolderCheck,
  Building2,
  Mail,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import {
  facultyService,
  type MentorInfo,
  type MentorFeedbackItem,
} from "../../services/facultyService";
import { studentService } from "../../services/studentService";

export default function StudentMentorPage() {
  const [mentor, setMentor] = useState<MentorInfo | null>(null);
  const [assigned, setAssigned] = useState(false);
  const [feedback, setFeedback] = useState<MentorFeedbackItem[]>([]);
  const [evidenceList, setEvidenceList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMentorData = async () => {
      try {
        setLoading(true);
        const [mentorData, feedbackData, evData] = await Promise.all([
          facultyService.getMyMentor(),
          facultyService.getMyMentorFeedback(),
          studentService.getEvidence(),
        ]);

        setAssigned(mentorData.assigned);
        setMentor(mentorData.mentor);
        setFeedback(feedbackData);
        setEvidenceList(evData);
      } catch (err) {
        console.error("Failed to load student mentor data", err);
      } finally {
        setLoading(false);
      }
    };

    loadMentorData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageSkeleton />
      </div>
    );
  }

  const approvedCount = evidenceList.filter((e) => e.verification_status === "approved").length;
  const pendingCount = evidenceList.filter((e) => e.verification_status === "pending").length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Faculty Mentorship & Guidance"
        description="Connect with your assigned faculty mentor, review constructive feedback, and track portfolio evidence evaluation."
      />

      {/* Assigned Mentor Card or Zero-Fake-Data Empty State */}
      {assigned && mentor ? (
        <Card className="p-6">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-5">
              <img
                src={mentor.avatar || "https://i.pravatar.cc/150?img=60"}
                alt={mentor.name}
                className="h-20 w-20 rounded-full border-2 border-indigo-200 object-cover"
              />
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-xl font-bold text-slate-900">{mentor.name}</h3>
                  <Badge tone="indigo">Assigned Faculty Mentor</Badge>
                </div>
                <div className="mt-2 space-y-1 text-xs text-slate-600">
                  <p className="flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-slate-400" />
                    <span>{mentor.email}</span>
                  </p>
                  {(mentor.department || mentor.institution) && (
                    <p className="flex items-center gap-1.5">
                      <Building2 className="h-3.5 w-3.5 text-slate-400" />
                      <span>{[mentor.department, mentor.institution].filter(Boolean).join(" • ")}</span>
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-indigo-50 p-4 text-center sm:text-right">
              <p className="text-xs font-semibold text-indigo-700">Cohort Mentorship</p>
              <p className="text-sm text-slate-600 mt-1">Available for evidence review & career advice</p>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="p-8 text-center border-dashed border-2 border-slate-200">
          <UserCheck className="mx-auto h-12 w-12 text-slate-300" />
          <h3 className="mt-4 text-base font-bold text-slate-900">No mentor assigned yet.</h3>
          <p className="mt-1 max-w-md mx-auto text-sm text-slate-500">
            You will be paired with a dedicated faculty mentor based on your department and academic cohort.
          </p>
        </Card>
      )}

      {/* Mentoring Guidance & Evidence Summary Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Mentoring Feedback Timeline */}
        <div className="space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-indigo-600" />
              <span>Mentor Guidance & Feedback</span>
            </h3>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
              {feedback.length} notes
            </span>
          </div>

          {feedback.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">
              No guidance messages recorded yet. When your mentor reviews your progress, their recommendations will appear here.
            </Card>
          ) : (
            <div className="space-y-3">
              {feedback.map((item) => (
                <Card key={item.feedback_id || item.id} className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-semibold text-slate-900">{item.mentor_name || "Faculty Mentor"}</span>
                      {item.related_skill_id && (
                        <span className="ml-2 rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                          {item.related_skill_id}
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
              ))}
            </div>
          )}
        </div>

        {/* Right 1 Col: Evidence Verification Overview */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-indigo-600" />
            <span>Evidence Reviews</span>
          </h3>

          <Card className="p-5 space-y-4">
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="rounded-xl bg-emerald-50 p-3">
                <div className="flex items-center justify-center gap-1 text-xs font-semibold text-emerald-700">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Approved
                </div>
                <p className="mt-1 text-2xl font-bold text-emerald-800">{approvedCount}</p>
              </div>
              <div className="rounded-xl bg-amber-50 p-3">
                <div className="flex items-center justify-center gap-1 text-xs font-semibold text-amber-700">
                  <Clock className="h-3.5 w-3.5" /> Pending
                </div>
                <p className="mt-1 text-2xl font-bold text-amber-800">{pendingCount}</p>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-3">
              <Link
                to="/student/portfolio"
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-100 px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition"
              >
                <span>Manage Evidence Portfolio</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </Card>

          {/* Recent Reviews with notes */}
          {evidenceList.filter((e) => e.verification_notes).length > 0 && (
            <Card className="p-5 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Recent Review Notes
              </h4>
              {evidenceList
                .filter((e) => e.verification_notes)
                .slice(0, 3)
                .map((ev) => (
                  <div key={ev.evidence_id || ev.id} className="rounded-lg bg-slate-50 p-3 text-xs">
                    <p className="font-semibold text-slate-800">{ev.title}</p>
                    <p className="mt-1 text-slate-600 italic">"{ev.verification_notes}"</p>
                  </div>
                ))}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
