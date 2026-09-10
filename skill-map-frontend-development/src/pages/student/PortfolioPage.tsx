import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Award,
  BadgeCheck,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Code2,
  Download,
  Edit3,
  ExternalLink,
  FileText,
  FolderGit2,
  Globe,
  Info,
  Link2,
  Plus,
  ShieldAlert,
  Trash2,
  Upload,
  X,
  XCircle,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { studentService } from "../../services/studentService";
import { useFetch } from "../../hooks/useFetch";
import { cn } from "../../utils/cn";

type EvidenceType = "all" | "project" | "certificate" | "course" | "assessment" | "other";

interface EvidenceItem {
  evidence_id: string;
  id: string;
  user_id: string;
  type: "project" | "certificate" | "course" | "assessment" | "other";
  title: string;
  description: string;
  skill_ids: string[];
  issuer?: string;
  issue_date?: string;
  credential_id?: string;
  project_url?: string;
  source_url?: string;
  file_path?: string;
  verification_status: "pending" | "approved" | "rejected";
  verification_notes?: string;
  reviewer_id?: string;
  submittedAt?: string;
  reviewedAt?: string;
}

export default function PortfolioPage() {
  const [selectedFilter, setSelectedFilter] = useState<EvidenceType>("all");
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<EvidenceItem | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form fields
  const [formData, setFormData] = useState({
    type: "project" as "project" | "certificate" | "course" | "assessment" | "other",
    title: "",
    description: "",
    skill_ids: [] as string[],
    issuer: "",
    issue_date: "",
    credential_id: "",
    project_url: "",
    source_url: "",
    file_path: "",
  });

  // Load student profile & existing skills for skill linking
  const { data: initialData } = useFetch(async () => {
    const [profile, skills] = await Promise.all([
      studentService.getProfile(),
      studentService.getSkills(),
    ]);
    return { profile, skills };
  });

  const fetchEvidence = async () => {
    try {
      setLoading(true);
      const data = await studentService.getEvidence();
      setEvidenceList(data);
    } catch (err) {
      console.error("Failed to load evidence", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
  }, []);

  const openCreateModal = () => {
    setEditingItem(null);
    setFormData({
      type: "project",
      title: "",
      description: "",
      skill_ids: [],
      issuer: "",
      issue_date: "",
      credential_id: "",
      project_url: "",
      source_url: "",
      file_path: "",
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (item: EvidenceItem) => {
    setEditingItem(item);
    setFormData({
      type: item.type,
      title: item.title,
      description: item.description || "",
      skill_ids: item.skill_ids || [],
      issuer: item.issuer || "",
      issue_date: item.issue_date || "",
      credential_id: item.credential_id || "",
      project_url: item.project_url || "",
      source_url: item.source_url || "",
      file_path: item.file_path || "",
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check size limit (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setFormError("File size exceeds maximum allowed 5 MB.");
      return;
    }

    try {
      setUploading(true);
      setFormError(null);
      const res = await studentService.uploadEvidenceFile(file);
      setFormData((prev) => ({ ...prev, file_path: res.file_path }));
    } catch (err: any) {
      setFormError(err.message || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      setFormError("Title is required");
      return;
    }

    try {
      setSaving(true);
      setFormError(null);

      if (editingItem) {
        const updated = await studentService.updateEvidence(editingItem.evidence_id, formData);
        setEvidenceList((prev) =>
          prev.map((item) => (item.evidence_id === updated.evidence_id ? updated : item))
        );
      } else {
        const created = await studentService.createEvidence(formData);
        setEvidenceList((prev) => [created, ...prev]);
      }

      setIsModalOpen(false);
    } catch (err: any) {
      setFormError(err.message || "Failed to save evidence");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (evidenceId: string) => {
    if (!window.confirm("Are you sure you want to delete this portfolio evidence item?")) {
      return;
    }
    try {
      await studentService.deleteEvidence(evidenceId);
      setEvidenceList((prev) => prev.filter((item) => item.evidence_id !== evidenceId));
    } catch (err: any) {
      alert("Failed to delete evidence: " + (err.message || "Server error"));
    }
  };

  const toggleSkill = (skillName: string) => {
    setFormData((prev) => {
      const exists = prev.skill_ids.includes(skillName);
      if (exists) {
        return { ...prev, skill_ids: prev.skill_ids.filter((s) => s !== skillName) };
      } else {
        return { ...prev, skill_ids: [...prev.skill_ids, skillName] };
      }
    });
  };

  const filteredEvidence = useMemo(() => {
    if (selectedFilter === "all") return evidenceList;
    return evidenceList.filter((e) => e.type === selectedFilter);
  }, [evidenceList, selectedFilter]);

  const projectsCount = evidenceList.filter((e) => e.type === "project").length;
  const certsCount = evidenceList.filter((e) => e.type === "certificate").length;
  const approvedCount = evidenceList.filter((e) => e.verification_status === "approved").length;
  const pendingCount = evidenceList.filter((e) => e.verification_status === "pending").length;

  if (loading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evidence & Project Portfolio"
        description="Showcase authenticated projects, certificates, and academic artifacts backed by peer & faculty review."
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreateModal}>
            Add Evidence
          </Button>
        }
      />

      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Evidence"
          value={evidenceList.length}
          icon={<FileText className="h-5 w-5" />}
          accent="indigo"
          hint="Projects, certificates & courses"
        />
        <StatCard
          label="Projects Submitted"
          value={projectsCount}
          icon={<FolderGit2 className="h-5 w-5" />}
          accent="sky"
          hint="Live & source implementations"
        />
        <StatCard
          label="Certifications"
          value={certsCount}
          icon={<Award className="h-5 w-5" />}
          accent="violet"
          hint="Credentialed achievements"
        />
        <StatCard
          label="Pending Review"
          value={pendingCount}
          icon={<Clock className="h-5 w-5" />}
          accent="amber"
          hint="Awaiting mentor verification"
        />
      </div>

      {/* Data Integrity & Verification Policy Alert */}
      <div className="flex items-start gap-3 rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-slate-600">
        <ShieldAlert className="h-5 w-5 shrink-0 text-indigo-600" />
        <div className="space-y-1">
          <p className="font-semibold text-slate-900">
            Institutional Verification & Skill Integrity
          </p>
          <p>
            All student-submitted portfolio items default to <strong>Pending Review</strong>{" "}
            status until vetted by authorized faculty or corporate mentors. Submitting
            evidence establishes proof in your portfolio, but does <em>not</em> automatically
            increase official verified skill proficiency in your profile until assessed or
            signed off.
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-slate-200 pb-2">
        {(
          [
            { id: "all", label: "All Items" },
            { id: "project", label: "Projects" },
            { id: "certificate", label: "Certificates" },
            { id: "course", label: "Courses" },
            { id: "assessment", label: "Assessments" },
            { id: "other", label: "Other" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedFilter(tab.id)}
            className={cn(
              "rounded-xl px-4 py-2 text-xs font-semibold transition-all",
              selectedFilter === tab.id
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Evidence Items Grid */}
      {filteredEvidence.length === 0 ? (
        <Card>
          <CardBody className="py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 ring-8 ring-indigo-50/50">
              <FolderGit2 className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-base font-bold text-slate-900">
              No Portfolio Evidence Found
            </h3>
            <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-slate-500">
              You haven't submitted any {selectedFilter === "all" ? "" : selectedFilter}{" "}
              evidence yet. Click "Add Evidence" to upload code repos, verified course
              certificates, or project deliverables.
            </p>
            <div className="mt-6">
              <Button icon={<Plus className="h-4 w-4" />} onClick={openCreateModal}>
                Add First Evidence Item
              </Button>
            </div>
          </CardBody>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredEvidence.map((item) => {
            const isApproved = item.verification_status === "approved";
            const isPending = item.verification_status === "pending";
            const isRejected = item.verification_status === "rejected";

            return (
              <Card key={item.evidence_id} className="flex flex-col justify-between">
                <CardBody className="space-y-4">
                  {/* Top Header: Type & Status */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                        {item.type === "project" && <FolderGit2 className="h-4 w-4" />}
                        {item.type === "certificate" && <Award className="h-4 w-4" />}
                        {item.type === "course" && <BookOpen className="h-4 w-4" />}
                        {item.type === "assessment" && <BadgeCheck className="h-4 w-4" />}
                        {item.type === "other" && <FileText className="h-4 w-4" />}
                      </div>
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          {item.type}
                        </span>
                        {item.issuer && (
                          <p className="text-xs font-semibold text-indigo-600">
                            {item.issuer}
                          </p>
                        )}
                      </div>
                    </div>

                    <Badge
                      tone={isApproved ? "emerald" : isPending ? "amber" : "rose"}
                      className="capitalize"
                    >
                      {isApproved && <CheckCircle2 className="mr-1 h-3 w-3" />}
                      {isPending && <Clock className="mr-1 h-3 w-3" />}
                      {isRejected && <XCircle className="mr-1 h-3 w-3" />}
                      {item.verification_status === "pending"
                        ? "Pending Review"
                        : item.verification_status}
                    </Badge>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 line-clamp-1">
                      {item.title}
                    </h4>
                    {item.issue_date && (
                      <div className="mt-1 flex items-center gap-1 text-[11px] text-slate-400">
                        <Calendar className="h-3 w-3" />
                        <span>Date: {item.issue_date}</span>
                      </div>
                    )}
                    {item.credential_id && (
                      <p className="mt-0.5 text-[11px] text-slate-500">
                        Credential ID: <span className="font-mono">{item.credential_id}</span>
                      </p>
                    )}
                    {item.description && (
                      <p className="mt-2 text-xs leading-relaxed text-slate-600 line-clamp-3">
                        {item.description}
                      </p>
                    )}
                  </div>

                  {/* Linked Skills */}
                  {item.skill_ids && item.skill_ids.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                        Linked Competencies
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {item.skill_ids.map((skill) => (
                          <span
                            key={skill}
                            className="rounded-lg bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Review Notes (if any) */}
                  {item.verification_notes && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-2.5 text-xs text-amber-900">
                      <p className="font-semibold">Reviewer Feedback:</p>
                      <p className="mt-0.5 text-slate-600">{item.verification_notes}</p>
                    </div>
                  )}
                </CardBody>

                {/* Card Footer: Links & Action Buttons */}
                <div className="border-t border-slate-100 bg-slate-50/50 p-4 pt-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {item.project_url && (
                        <a
                          href={item.project_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline"
                        >
                          <Globe className="h-3.5 w-3.5" />
                          Live Demo
                        </a>
                      )}
                      {item.source_url && (
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900"
                        >
                          <Link2 className="h-3.5 w-3.5" />
                          Code / Proof
                        </a>
                      )}
                      {item.file_path && (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500">
                          <FileText className="h-3.5 w-3.5 text-slate-400" />
                          Attachment Attached
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEditModal(item)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition"
                        title="Edit evidence"
                      >
                        <Edit3 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.evidence_id)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-100 hover:text-rose-600 transition"
                        title="Delete evidence"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add / Edit Evidence Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="my-8 w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-100">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingItem ? "Edit Evidence Item" : "Submit Portfolio Evidence"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {formError && (
              <div className="mt-4 flex items-center gap-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-700 border border-rose-200">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              {/* Type and Title */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Type</label>
                  <select
                    value={formData.type}
                    onChange={(e) =>
                      setFormData({ ...formData, type: e.target.value as any })
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value="project">Project</option>
                    <option value="certificate">Certificate</option>
                    <option value="course">Course</option>
                    <option value="assessment">Assessment</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700">
                    Title <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Distributed Task Queue in Go"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
              </div>

              {/* Issuer and Date */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Issuer / Organization
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. AWS, Coursera, IIT Madras"
                    value={formData.issuer}
                    onChange={(e) => setFormData({ ...formData, issuer: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Date (YYYY-MM-DD)
                  </label>
                  <input
                    type="date"
                    value={formData.issue_date}
                    onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
              </div>

              {/* Credential ID */}
              <div>
                <label className="block text-xs font-semibold text-slate-700">
                  Credential / Certificate ID (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. CERT-8392-ABC"
                  value={formData.credential_id}
                  onChange={(e) => setFormData({ ...formData, credential_id: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-semibold text-slate-700">
                  Description / Abstract
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe your implementation, architectural decisions, and responsibilities..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
              </div>

              {/* Link Existing Skills */}
              {initialData?.skills && initialData.skills.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Link Existing Skills
                  </label>
                  <p className="text-[11px] text-slate-500 mb-2">
                    Select competencies demonstrated by this evidence:
                  </p>
                  <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-1.5 rounded-xl border border-slate-100 bg-slate-50">
                    {initialData.skills.map((skill) => {
                      const isSelected = formData.skill_ids.includes(skill.name);
                      return (
                        <button
                          key={skill.id}
                          type="button"
                          onClick={() => toggleSkill(skill.name)}
                          className={cn(
                            "rounded-lg px-2.5 py-1 text-xs font-medium transition",
                            isSelected
                              ? "bg-indigo-600 text-white shadow-sm"
                              : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
                          )}
                        >
                          {skill.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* URLs */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Live Project / Demo URL
                  </label>
                  <input
                    type="url"
                    placeholder="https://..."
                    value={formData.project_url}
                    onChange={(e) => setFormData({ ...formData, project_url: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Source Repo / Credential Link
                  </label>
                  <input
                    type="url"
                    placeholder="https://github.com/..."
                    value={formData.source_url}
                    onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
              </div>

              {/* File Attachment */}
              <div>
                <label className="block text-xs font-semibold text-slate-700">
                  Attach Evidence File (PDF, PNG, JPG, max 5MB)
                </label>
                <div className="mt-1 flex items-center gap-3">
                  <label className="flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100">
                    <Upload className="h-4 w-4 text-slate-500" />
                    <span>{uploading ? "Uploading..." : "Choose File"}</span>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp"
                      onChange={handleFileUpload}
                      disabled={uploading}
                      className="hidden"
                    />
                  </label>
                  {formData.file_path && (
                    <span className="text-xs font-medium text-emerald-600">
                      File attached ✓
                    </span>
                  )}
                </div>
              </div>

              {/* Integrity Reminder */}
              <p className="text-[11px] leading-relaxed text-slate-500">
                * By submitting, this evidence will be queued as <strong>Pending Review</strong>.
                Faculty reviews will confirm and stamp this competency for recruiter visibility.
              </p>

              {/* Buttons */}
              <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsModalOpen(false)}
                  disabled={saving || uploading}
                >
                  Cancel
                </Button>
                <Button type="submit" loading={saving} disabled={uploading}>
                  {editingItem ? "Save Changes" : "Submit Evidence"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
