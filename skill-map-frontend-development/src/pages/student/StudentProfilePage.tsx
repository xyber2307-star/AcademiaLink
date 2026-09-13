import { useState, useEffect } from "react";
import { Award, BadgeCheck, Briefcase, Camera, Download, Edit3, ExternalLink, FolderGit2, Globe, GraduationCap, Code2, Link2, Mail, MapPin, Phone, Plus, Share2, X } from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Avatar } from "../../components/ui/Avatar";
import { ProgressBar, ProgressRing } from "../../components/ui/Progress";
import { SkillBadge } from "../../components/ui/SkillBadge";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { PageHeader } from "../../components/ui/PageHeader";
import { useFetch } from "../../hooks/useFetch";
import { studentService } from "../../services/studentService";
import { EditProfileModal } from "../../components/profile/EditProfileModal";
import type { MyProfile } from "../../services/userService";
import type { Skill } from "../../types";
import { cn } from "../../utils/cn";

const tabs = ["Overview", "Education", "Projects", "Experience", "Certifications"] as const;
type Tab = (typeof tabs)[number];

const completionItems = [
  { label: "Basic details", done: true }, { label: "Education", done: true }, { label: "Skills assessed", done: true },
  { label: "Projects (min 3)", done: true }, { label: "Certifications verified", done: false }, { label: "Resume uploaded", done: false },
];

export default function StudentProfilePage() {
  const [tab, setTab] = useState<Tab>("Overview");
  const [refreshKey, setRefreshKey] = useState(0);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const { data, loading } = useFetch(async () => {
    const [profile, skills] = await Promise.all([studentService.getProfile(), studentService.getSkills()]);
    return { profile, skills };
  }, [refreshKey]);

  const [skillsList, setSkillsList] = useState<Skill[]>([]);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addingSkill, setAddingSkill] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [skillForm, setSkillForm] = useState({
    name: "",
    category: "Technical" as "Technical" | "Soft" | "Domain" | "Tools",
    proficiency: 3,
    evidenceType: "project" as "project" | "certificate" | "course" | "assessment" | "other",
    evidenceTitle: "",
    evidenceUrl: "",
  });

  useEffect(() => {
    if (data?.skills) {
      setSkillsList(data.skills);
    }
  }, [data?.skills]);

  if (loading || !data) return <PageSkeleton />;
  const { profile } = data;
  const verifiedCount = skillsList.filter((s) => s.verified).length;

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillForm.name.trim()) return;
    try {
      setAddingSkill(true);
      setAddError(null);
      const newSkill = await studentService.addSkill({
        name: skillForm.name.trim(),
        category: skillForm.category,
        proficiency: Number(skillForm.proficiency),
        source: "manual",
        evidence: skillForm.evidenceTitle.trim()
          ? {
              type: skillForm.evidenceType,
              title: skillForm.evidenceTitle.trim(),
              url: skillForm.evidenceUrl.trim() || undefined,
              verified: false,
            }
          : undefined,
      });
      setSkillsList((prev) => [...prev, newSkill]);
      setIsAddModalOpen(false);
      setSkillForm({
        name: "",
        category: "Technical",
        proficiency: 3,
        evidenceType: "project",
        evidenceTitle: "",
        evidenceUrl: "",
      });
    } catch (err: any) {
      setAddError(err?.message || "Failed to add skill. Please try again.");
    } finally {
      setAddingSkill(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="My Profile" description="Your public skill profile visible to recruiters and faculty." actions={<><Button variant="outline" icon={<Share2 className="h-4 w-4" />}>Share</Button><Button variant="outline" icon={<Download className="h-4 w-4" />}>Export résumé</Button><Button icon={<Edit3 className="h-4 w-4" />} onClick={() => setIsEditModalOpen(true)}>Edit profile</Button></>} />

      {/* Header card */}
      <Card className="overflow-hidden">
        <div className="h-28 bg-gradient-to-r from-indigo-600 via-violet-600 to-sky-500 sm:h-36" />
        <CardBody className="relative pt-0">
          <div className="-mt-12 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="relative w-fit">
                <Avatar src={profile.avatar} name={profile.name} size="xl" className="ring-4 ring-white shadow-lg" />
                <button className="absolute bottom-0 right-0 rounded-full bg-indigo-600 p-1.5 text-white shadow ring-2 ring-white"><Camera className="h-3.5 w-3.5" /></button>
              </div>
              <div className="sm:pb-1">
                <div className="flex flex-wrap items-center gap-2"><h2 className="text-2xl font-bold text-slate-900">{profile.name}</h2><Badge tone="emerald"><BadgeCheck className="h-3.5 w-3.5" /> Verified student</Badge></div>
                <p className="mt-0.5 text-sm font-medium text-indigo-600">{profile.headline}</p>
                <p className="mt-1 flex flex-wrap items-center gap-1.5 text-sm text-slate-500">
                  <span>{profile.degree} · {profile.branch} · {profile.year} · {profile.institution}</span>
                  {profile.institutionVerificationStatus === "VERIFIED" && (
                    <Badge tone="emerald" title={`Institution registry verified · Source: ${profile.institutionVerificationSource || "AICTE"} · Program-level approval not checked.`}>
                      <BadgeCheck className="h-3.5 w-3.5" /> Institution Verified
                    </Badge>
                  )}
                  {profile.institutionVerificationStatus === "NOT_VERIFIED" && profile.institution && (
                    <span className="text-xs font-medium text-amber-600">Not Verified</span>
                  )}
                </p>
                {profile.institutionVerificationStatus === "VERIFIED" && (
                  <p className="text-xs text-slate-400">
                    {[profile.institutionDistrict, profile.institutionState].filter(Boolean).join(", ")}
                    {profile.institutionCode ? ` · AICTE ID: ${profile.institutionCode}` : ""}
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{profile.location}</span>
                  <span className="inline-flex items-center gap-1"><Mail className="h-3.5 w-3.5" />{profile.email}</span>
                  <span className="inline-flex items-center gap-1"><Phone className="h-3.5 w-3.5" />{profile.phone}</span>
                </div>
              </div>
            </div>
            <div className="flex gap-2 sm:pb-1">
              {[{ icon: Code2, l: profile.links.github }, { icon: Link2, l: profile.links.linkedin }, { icon: Globe, l: profile.links.portfolio }].map((x, i) => (
                <a key={i} href="#" title={x.l} className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600"><x.icon className="h-4 w-4" /></a>
              ))}
            </div>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3 border-t border-slate-100 pt-5 sm:grid-cols-4">
            {[["Skill score", `${profile.skillScore}/100`], ["Career readiness", `${profile.careerReadiness}%`], ["CGPA", profile.cgpa.toFixed(2)], ["Verified skills", `${verifiedCount}/${skillsList.length}`]].map(([l, v]) => (
              <div key={l} className="rounded-xl bg-slate-50 p-3"><p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{l}</p><p className="mt-1 text-lg font-bold text-slate-900">{v}</p></div>
            ))}
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Tabs */}
          <div className="flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1">
            {tabs.map((t) => <button key={t} onClick={() => setTab(t)} className={cn("flex-1 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition", tab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900")}>{t}</button>)}
          </div>

          {tab === "Overview" && (
            <>
              <Card><CardHeader title="About" /><CardBody><p className="text-sm leading-relaxed text-slate-600">{profile.about}</p>
                <div className="mt-4 flex flex-wrap gap-2"><Badge tone="indigo">Target: {profile.targetRole}</Badge><Badge tone="violet">Open to internships</Badge><Badge tone="sky">Available from May 2025</Badge></div></CardBody></Card>
              <Card>
                <CardHeader
                  title="Skills"
                  subtitle="Assessed and verified competencies"
                  action={
                    <Button
                      size="sm"
                      variant="outline"
                      icon={<Plus className="h-3.5 w-3.5" />}
                      onClick={() => setIsAddModalOpen(true)}
                    >
                      Add skill
                    </Button>
                  }
                />
                <CardBody className="space-y-5">
                  {(["Technical", "Domain", "Tools", "Soft"] as const).map((cat) => {
                    const catSkills = skillsList.filter((s) => s.category === cat);
                    return (
                      <div key={cat}>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{cat}</p>
                        <div className="flex flex-wrap gap-2">
                          {catSkills.map((s) => (
                            <SkillBadge key={s.id} name={s.name} score={s.score} verified={s.verified} />
                          ))}
                          {catSkills.length === 0 && (
                            <span className="text-xs text-slate-400 italic">No {cat.toLowerCase()} skills added</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </CardBody>
              </Card>
              <Card>
                <CardHeader title="Featured projects" action={<button onClick={() => setTab("Projects")} className="text-xs font-semibold text-indigo-600">View all</button>} />
                <CardBody className="grid gap-3 sm:grid-cols-2">
                  {profile.projects.slice(0, 2).map((p) => (
                    <div key={p.title} className="rounded-xl border border-slate-100 p-4"><div className="flex items-start justify-between"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600"><FolderGit2 className="h-4 w-4" /></span><a href={p.link} className="text-slate-400 hover:text-indigo-600"><ExternalLink className="h-4 w-4" /></a></div><p className="mt-3 text-sm font-semibold text-slate-800">{p.title}</p><p className="mt-1 line-clamp-2 text-xs text-slate-500">{p.description}</p><div className="mt-3 flex flex-wrap gap-1">{p.tech.map((t) => <span key={t} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">{t}</span>)}</div></div>
                  ))}
                </CardBody>
              </Card>
            </>
          )}

          {tab === "Education" && (
            <Card><CardHeader title="Education" action={<Button size="sm" variant="outline" icon={<Plus className="h-3.5 w-3.5" />}>Add</Button>} /><CardBody>
              <ol className="relative space-y-6 border-l-2 border-slate-100 pl-6">
                {profile.education.map((e) => (
                  <li key={e.degree} className="relative"><span className="absolute -left-[31px] flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-white ring-4 ring-white"><GraduationCap className="h-3 w-3" /></span>
                    <p className="text-sm font-semibold text-slate-800">{e.degree}</p><p className="text-sm text-slate-600">{e.institution}</p><p className="mt-1 text-xs text-slate-500">{e.year} · <span className="font-semibold text-slate-700">{e.score}</span></p></li>
                ))}
              </ol></CardBody></Card>
          )}

          {tab === "Projects" && (
            <Card><CardHeader title="Projects" subtitle={`${profile.projects.length} projects · counted as skill evidence`} action={<Button size="sm" icon={<Plus className="h-3.5 w-3.5" />}>Add project</Button>} /><CardBody className="space-y-3">
              {profile.projects.map((p) => (
                <div key={p.title} className="flex gap-4 rounded-xl border border-slate-100 p-4"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><FolderGit2 className="h-5 w-5" /></span>
                  <div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className="text-sm font-semibold text-slate-800">{p.title}</p><Badge tone="emerald"><BadgeCheck className="h-3 w-3" /> Verified</Badge></div><p className="mt-1 text-sm text-slate-600">{p.description}</p><div className="mt-2 flex flex-wrap gap-1">{p.tech.map((t) => <span key={t} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">{t}</span>)}</div></div></div>
              ))}
            </CardBody></Card>
          )}

          {tab === "Experience" && (
            <Card><CardHeader title="Experience" action={<Button size="sm" variant="outline" icon={<Plus className="h-3.5 w-3.5" />}>Add</Button>} /><CardBody>
              <ol className="relative space-y-6 border-l-2 border-slate-100 pl-6">
                {profile.experience.map((e) => (
                  <li key={e.role} className="relative"><span className="absolute -left-[31px] flex h-6 w-6 items-center justify-center rounded-full bg-violet-600 text-white ring-4 ring-white"><Briefcase className="h-3 w-3" /></span>
                    <p className="text-sm font-semibold text-slate-800">{e.role}</p><p className="text-sm text-slate-600">{e.org}</p><p className="mt-0.5 text-xs text-slate-500">{e.period}</p><p className="mt-2 text-sm text-slate-600">{e.description}</p></li>
                ))}
              </ol></CardBody></Card>
          )}

          {tab === "Certifications" && (
            <Card><CardHeader title="Certifications" action={<Button size="sm" variant="outline" icon={<Plus className="h-3.5 w-3.5" />}>Upload</Button>} /><CardBody className="grid gap-3 sm:grid-cols-2">
              {profile.certifications.map((c) => (
                <div key={c.name} className="rounded-xl border border-slate-100 p-4"><div className="flex items-start justify-between"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 text-amber-600"><Award className="h-4 w-4" /></span>{c.verified ? <Badge tone="emerald"><BadgeCheck className="h-3 w-3" /> Verified</Badge> : <Badge tone="amber">Pending</Badge>}</div><p className="mt-3 text-sm font-semibold text-slate-800">{c.name}</p><p className="text-xs text-slate-500">{c.issuer} · {c.year}</p></div>
              ))}
            </CardBody></Card>
          )}
        </div>

        {/* Side column */}
        <div className="space-y-6">
          <Card>
            <CardHeader title="Profile completion" />
            <CardBody>
              <div className="flex items-center gap-5"><ProgressRing value={profile.profileCompletion} size={88} stroke={8} /><div><p className="text-sm font-semibold text-slate-800">Almost there!</p><p className="mt-1 text-xs text-slate-500">Complete profiles get 3× more recruiter views.</p></div></div>
              <ul className="mt-5 space-y-2.5">
                {completionItems.map((c) => (
                  <li key={c.label} className="flex items-center gap-2.5 text-sm"><span className={cn("flex h-5 w-5 items-center justify-center rounded-full", c.done ? "bg-emerald-500 text-white" : "border-2 border-slate-300")}>{c.done && <BadgeCheck className="h-3.5 w-3.5" />}</span><span className={c.done ? "text-slate-500 line-through" : "font-medium text-slate-800"}>{c.label}</span></li>
                ))}
              </ul>
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Academic details" />
            <CardBody className="space-y-3 text-sm">
              {[["Roll number", profile.rollNo], ["Degree", profile.degree], ["Branch", profile.branch], ["Year", profile.year], ["CGPA", profile.cgpa.toFixed(2)]].map(([l, v]) => (
                <div key={l} className="flex items-center justify-between border-b border-slate-50 pb-2 last:border-0 last:pb-0"><span className="text-slate-500">{l}</span><span className="font-medium text-slate-800">{v}</span></div>
              ))}
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Profile strength by area" />
            <CardBody className="space-y-3">
              {[["Skills", 80], ["Evidence", 70], ["Certifications", 60], ["Experience", 75]].map(([l, v]) => (
                <div key={l}><div className="mb-1 flex justify-between text-xs"><span className="font-medium text-slate-700">{l}</span><span className="text-slate-500">{v}%</span></div><ProgressBar value={v as number} size="sm" /></div>
              ))}
            </CardBody>
          </Card>
        </div>
      </div>

      {/* Add Skill Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Add New Skill</h3>
                <p className="text-xs text-slate-500">Record a skill and provide optional verification evidence.</p>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddSkill} className="mt-4 space-y-4">
              {addError && (
                <div className="rounded-xl bg-rose-50 p-3 text-xs text-rose-700">
                  {addError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700">Skill Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Python, Docker, Kubernetes, React"
                  value={skillForm.name}
                  onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Category</label>
                  <select
                    value={skillForm.category}
                    onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value as any })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value="Technical">Technical</option>
                    <option value="Tools">Tools</option>
                    <option value="Domain">Domain</option>
                    <option value="Soft">Soft</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700">Proficiency Level</label>
                  <select
                    value={skillForm.proficiency}
                    onChange={(e) => setSkillForm({ ...skillForm, proficiency: Number(e.target.value) })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  >
                    <option value={1}>1 - Beginner (20%)</option>
                    <option value={2}>2 - Basic (40%)</option>
                    <option value={3}>3 - Intermediate (60%)</option>
                    <option value={4}>4 - Advanced (80%)</option>
                    <option value={5}>5 - Expert (100%)</option>
                  </select>
                </div>
              </div>

              <div className="border-t border-slate-100 pt-3">
                <p className="mb-2 text-xs font-semibold text-slate-700">Evidence & Proof (Optional)</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-500">Evidence Type</label>
                    <select
                      value={skillForm.evidenceType}
                      onChange={(e) => setSkillForm({ ...skillForm, evidenceType: e.target.value as any })}
                      className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                    >
                      <option value="project">Project</option>
                      <option value="certificate">Certificate</option>
                      <option value="course">Course</option>
                      <option value="assessment">Assessment</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-500">Evidence Title / Credential ID</label>
                    <input
                      type="text"
                      placeholder="e.g. Distributed Cache in Go"
                      value={skillForm.evidenceTitle}
                      onChange={(e) => setSkillForm({ ...skillForm, evidenceTitle: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                    />
                  </div>
                </div>

                <div className="mt-2">
                  <label className="block text-[11px] text-slate-500">Repository / Verification URL</label>
                  <input
                    type="url"
                    placeholder="https://github.com/user/project or credential link"
                    value={skillForm.evidenceUrl}
                    onChange={(e) => setSkillForm({ ...skillForm, evidenceUrl: e.target.value })}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsAddModalOpen(false)}
                  disabled={addingSkill}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  loading={addingSkill}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Save Skill
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isEditModalOpen && (
        <EditProfileModal
          profile={profile as unknown as MyProfile}
          role="student"
          onClose={() => setIsEditModalOpen(false)}
          onSaved={() => setRefreshKey((k) => k + 1)}
        />
      )}
    </div>
  );
}
