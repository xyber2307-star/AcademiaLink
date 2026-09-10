import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertCircle,
  Archive,
  Briefcase,
  CheckCircle2,
  Clock,
  Edit3,
  ExternalLink,
  Eye,
  FileText,
  Filter,
  Layers,
  MapPin,
  Plus,
  Search,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/ui/StatCard";
import { recruiterService, type RecruiterJobPayload } from "../../services/recruiterService";
import { cn } from "../../utils/cn";

export default function RecruiterDashboardPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [formTitle, setFormTitle] = useState("");
  const [formCompany, setFormCompany] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formLocation, setFormLocation] = useState("");
  const [formEmpType, setFormEmpType] = useState("Internship");
  const [formWorkMode, setFormWorkMode] = useState<"Remote" | "Hybrid" | "On-site">("Hybrid");
  const [formStipend, setFormStipend] = useState("₹40,000/mo");
  const [formAppUrl, setFormAppUrl] = useState("");
  const [formStatus, setFormStatus] = useState<"draft" | "published" | "closed" | "archived">("published");

  // Required skills list: [{ name, required_proficiency, weight }]
  const [skillsList, setSkillsList] = useState<
    { name: string; required_proficiency: number; weight: number }[]
  >([
    { name: "Python", required_proficiency: 4, weight: 2.0 },
    { name: "SQL", required_proficiency: 3, weight: 1.5 },
  ]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const data = await recruiterService.getRecruiterJobs();
      setJobs(data);
    } catch (err) {
      console.error("Failed to load recruiter jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const openCreateModal = () => {
    setEditingJobId(null);
    setFormTitle("");
    setFormCompany("Acme Corp");
    setFormDescription("");
    setFormLocation("Bengaluru, India (Hybrid)");
    setFormEmpType("Internship");
    setFormWorkMode("Hybrid");
    setFormStipend("₹40,000/mo");
    setFormAppUrl("");
    setFormStatus("published");
    setSkillsList([
      { name: "Python", required_proficiency: 4, weight: 2.0 },
      { name: "SQL", required_proficiency: 3, weight: 1.5 },
    ]);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (job: any) => {
    setEditingJobId(job.id || job.job_id);
    setFormTitle(job.title || "");
    setFormCompany(job.company || "");
    setFormDescription(job.description || "");
    setFormLocation(job.location || "");
    setFormEmpType(job.employment_type || job.type || "Internship");
    setFormWorkMode(job.workMode || "Hybrid");
    setFormStipend(job.stipend || "₹40,000/mo");
    setFormAppUrl(job.application_url || "");
    setFormStatus(job.status || "published");

    const req = job.required_skills || job.requiredSkills || [];
    setSkillsList(
      req.map((s: any) => ({
        name: s.name || String(s),
        required_proficiency: s.required_proficiency || 3,
        weight: s.weight || 1.0,
      }))
    );
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleAddSkillRow = () => {
    setSkillsList([...skillsList, { name: "", required_proficiency: 3, weight: 1.0 }]);
  };

  const handleRemoveSkillRow = (index: number) => {
    setSkillsList(skillsList.filter((_, i) => i !== index));
  };

  const handleSkillChange = (
    index: number,
    field: "name" | "required_proficiency" | "weight",
    value: any
  ) => {
    const updated = [...skillsList];
    updated[index] = { ...updated[index], [field]: value };
    setSkillsList(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim()) {
      setFormError("Job title is required");
      return;
    }
    if (!formCompany.trim()) {
      setFormError("Company name is required");
      return;
    }
    if (!skillsList.length || skillsList.some((s) => !s.name.trim())) {
      setFormError("Please provide at least one valid required skill with a name");
      return;
    }

    try {
      setSaving(true);
      setFormError(null);

      const payload: RecruiterJobPayload = {
        title: formTitle.trim(),
        company: formCompany.trim(),
        description: formDescription.trim(),
        location: formLocation.trim(),
        employment_type: formEmpType,
        type: formEmpType,
        workMode: formWorkMode,
        stipend: formStipend.trim(),
        application_url: formAppUrl.trim() || undefined,
        status: formStatus,
        required_skills: skillsList.map((s) => ({
          name: s.name.trim(),
          required_proficiency: Number(s.required_proficiency),
          weight: Number(s.weight),
        })),
      };

      if (editingJobId) {
        const updated = await recruiterService.updateRecruiterJob(editingJobId, payload);
        setJobs((prev) =>
          prev.map((j) => ((j.id || j.job_id) === (updated.id || updated.job_id) ? updated : j))
        );
      } else {
        const created = await recruiterService.createRecruiterJob(payload);
        setJobs((prev) => [created, ...prev]);
      }

      setIsModalOpen(false);
    } catch (err: any) {
      setFormError(err.message || "Failed to save job posting");
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (jobId: string) => {
    if (!window.confirm("Are you sure you want to archive this job posting?")) return;
    try {
      await recruiterService.archiveRecruiterJob(jobId);
      setJobs((prev) =>
        prev.map((j) =>
          (j.id || j.job_id) === jobId ? { ...j, status: "archived" } : j
        )
      );
    } catch (err: any) {
      alert("Failed to archive job: " + (err.message || "Error"));
    }
  };

  const filteredJobs = useMemo(() => {
    if (statusFilter === "all") return jobs;
    return jobs.filter((j) => (j.status || "published") === statusFilter);
  }, [jobs, statusFilter]);

  const publishedCount = jobs.filter((j) => (j.status || "published") === "published").length;
  const draftCount = jobs.filter((j) => j.status === "draft").length;
  const archivedCount = jobs.filter(
    (j) => j.status === "archived" || j.status === "closed"
  ).length;

  if (loading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recruiter Opportunity Management"
        description="Publish role requirements, manage company job listings, and discover verified matching candidates."
        actions={
          <Button icon={<Plus className="h-4 w-4" />} onClick={openCreateModal}>
            Post New Opportunity
          </Button>
        }
      />

      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Postings"
          value={jobs.length}
          icon={<Briefcase className="h-5 w-5" />}
          accent="indigo"
          hint="All job listings created"
        />
        <StatCard
          label="Published"
          value={publishedCount}
          icon={<CheckCircle2 className="h-5 w-5" />}
          accent="emerald"
          hint="Live in student discovery"
        />
        <StatCard
          label="Drafts"
          value={draftCount}
          icon={<Clock className="h-5 w-5" />}
          accent="amber"
          hint="Unpublished private drafts"
        />
        <StatCard
          label="Archived / Closed"
          value={archivedCount}
          icon={<Archive className="h-5 w-5" />}
          accent="slate"
          hint="Inactive opportunities"
        />
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-slate-200 pb-2">
        {(
          [
            { id: "all", label: "All Postings" },
            { id: "published", label: "Published" },
            { id: "draft", label: "Drafts" },
            { id: "archived", label: "Archived" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={cn(
              "rounded-xl px-4 py-2 text-xs font-semibold transition-all",
              statusFilter === tab.id
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Jobs List */}
      {filteredJobs.length === 0 ? (
        <Card>
          <CardBody className="py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 ring-8 ring-indigo-50/50">
              <Briefcase className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-base font-bold text-slate-900">
              No Job Postings Found
            </h3>
            <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-slate-500">
              {statusFilter === "all"
                ? "You haven't posted any job opportunities yet. Click 'Post New Opportunity' to publish role requirements and discover matching candidates."
                : `No jobs found with status '${statusFilter}'.`}
            </p>
            <div className="mt-6">
              <Button icon={<Plus className="h-4 w-4" />} onClick={openCreateModal}>
                Post Opportunity
              </Button>
            </div>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredJobs.map((job) => {
            const jobId = job.id || job.job_id;
            const status = job.status || "published";
            const reqSkills = job.required_skills || job.requiredSkills || [];

            const statusTone =
              status === "published"
                ? "emerald"
                : status === "draft"
                ? "amber"
                : "slate";

            return (
              <Card key={jobId} className="hover:border-slate-300 transition">
                <CardBody className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900">{job.title}</h3>
                      <Badge tone={statusTone} className="capitalize">
                        {status}
                      </Badge>
                      <span className="text-xs font-semibold text-indigo-600">
                        {job.company}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5" />
                        {job.location || "Remote"}
                      </span>
                      <span>•</span>
                      <span>{job.employment_type || job.type || "Internship"}</span>
                      <span>•</span>
                      <span className="font-semibold text-slate-700">
                        {job.stipend || "Competitive"}
                      </span>
                    </div>

                    {/* Required Skills Badges */}
                    {reqSkills.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mr-1">
                          Skills:
                        </span>
                        {reqSkills.map((s: any, idx: number) => {
                          const sName = s.name || String(s);
                          const sProf = s.required_proficiency || 3;
                          const sWeight = s.weight || 1.0;
                          return (
                            <span
                              key={idx}
                              className="rounded-lg bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                            >
                              {sName} (lvl {sProf}, {sWeight}x)
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3 lg:border-t-0 lg:pt-0">
                    <Link to={`/recruiter/jobs/${jobId}/candidates`}>
                      <Button
                        size="sm"
                        variant="primary"
                        icon={<Users className="h-4 w-4" />}
                      >
                        Match Candidates
                      </Button>
                    </Link>

                    <Button
                      size="sm"
                      variant="outline"
                      icon={<Edit3 className="h-4 w-4" />}
                      onClick={() => openEditModal(job)}
                    >
                      Edit
                    </Button>

                    {status !== "archived" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        icon={<Archive className="h-4 w-4 text-slate-400" />}
                        onClick={() => handleArchive(jobId)}
                        title="Archive Job"
                      >
                        Archive
                      </Button>
                    )}
                  </div>
                </CardBody>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create / Edit Job Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="my-8 w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl border border-slate-100">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingJobId ? "Edit Job Posting" : "Post New Job Opportunity"}
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
              {/* Title & Company */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Job Title <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Backend Platform Engineer Intern"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Company Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CloudScale Technologies"
                    value={formCompany}
                    onChange={(e) => setFormCompany(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
              </div>

              {/* Location & WorkMode */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700">
                    Location
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Bengaluru, India (Hybrid)"
                    value={formLocation}
                    onChange={(e) => setFormLocation(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Work Mode
                  </label>
                  <select
                    value={formWorkMode}
                    onChange={(e) => setFormWorkMode(e.target.value as any)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value="Hybrid">Hybrid</option>
                    <option value="Remote">Remote</option>
                    <option value="On-site">On-site</option>
                  </select>
                </div>
              </div>

              {/* Employment Type & Stipend & Status */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Employment Type
                  </label>
                  <select
                    value={formEmpType}
                    onChange={(e) => setFormEmpType(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value="Internship">Internship</option>
                    <option value="Full-time">Full-time</option>
                    <option value="Contract">Contract</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Stipend / Salary
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. ₹45,000/mo"
                    value={formStipend}
                    onChange={(e) => setFormStipend(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700">
                    Status
                  </label>
                  <select
                    value={formStatus}
                    onChange={(e) => setFormStatus(e.target.value as any)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value="published">Published (Active)</option>
                    <option value="draft">Draft (Private)</option>
                    <option value="closed">Closed</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-semibold text-slate-700">
                  Role Description & Scope
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe key responsibilities, team environment, and expectations..."
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
              </div>

              {/* Required Skills Builder */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-800">
                      Required Skills & Weights
                    </label>
                    <p className="text-[11px] text-slate-500">
                      Used by deterministic matching algorithm (Proficiency 1–5, Weight 0.1–5.0)
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    icon={<Plus className="h-3.5 w-3.5" />}
                    onClick={handleAddSkillRow}
                  >
                    Add Skill
                  </Button>
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {skillsList.map((skill, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        placeholder="Skill Name (e.g. Python)"
                        value={skill.name}
                        onChange={(e) => handleSkillChange(idx, "name", e.target.value)}
                        className="flex-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs focus:border-indigo-500 focus:outline-none"
                      />
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-slate-400">Req:</span>
                        <input
                          type="number"
                          min={1}
                          max={5}
                          step={1}
                          value={skill.required_proficiency}
                          onChange={(e) =>
                            handleSkillChange(
                              idx,
                              "required_proficiency",
                              Number(e.target.value)
                            )
                          }
                          className="w-14 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-center focus:border-indigo-500 focus:outline-none"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-slate-400">Wt:</span>
                        <input
                          type="number"
                          min={0.1}
                          max={5}
                          step={0.5}
                          value={skill.weight}
                          onChange={(e) =>
                            handleSkillChange(idx, "weight", Number(e.target.value))
                          }
                          className="w-14 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-center focus:border-indigo-500 focus:outline-none"
                        />
                      </div>
                      {skillsList.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveSkillRow(idx)}
                          className="p-1 text-slate-400 hover:text-rose-500"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsModalOpen(false)}
                  disabled={saving}
                >
                  Cancel
                </Button>
                <Button type="submit" loading={saving}>
                  {editingJobId ? "Save Changes" : "Post Opportunity"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
