import React, { useEffect, useState } from "react";
import {
  Search,
  Plus,
  Merge,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Power,
  Inbox,
} from "lucide-react";
import {
  taxonomyService,
  SkillTaxonomyEntry,
  SkillReviewQueueItem,
} from "../../services/taxonomyService";

type Tab = "taxonomy" | "review-queue";

export const AdminSkillsPage: React.FC = () => {
  const [tab, setTab] = useState<Tab>("taxonomy");

  // Taxonomy management state
  const [skills, setSkills] = useState<SkillTaxonomyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Add-skill form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSkill, setNewSkill] = useState({ name: "", category: "", subcategory: "", type: "technical" });
  const [submitting, setSubmitting] = useState(false);

  // Merge form
  const [mergeSource, setMergeSource] = useState("");
  const [mergeTarget, setMergeTarget] = useState("");

  // Review queue state
  const [queueItems, setQueueItems] = useState<SkillReviewQueueItem[]>([]);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [approveForm, setApproveForm] = useState({ category: "", subcategory: "", type: "tool" });

  const fetchSkills = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await taxonomyService.adminList({ q: searchQuery || undefined });
      setSkills(data);
    } catch (err: any) {
      setError(err.message || "Failed to load skill taxonomy.");
    } finally {
      setLoading(false);
    }
  };

  const fetchQueue = async () => {
    setLoadingQueue(true);
    try {
      const items = await taxonomyService.adminReviewQueue("pending");
      setQueueItems(items);
    } catch (err: any) {
      setError(err.message || "Failed to load review queue.");
    } finally {
      setLoadingQueue(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, [searchQuery]);

  useEffect(() => {
    if (tab === "review-queue") fetchQueue();
  }, [tab]);

  const flash = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(null), 4000);
  };

  const handleCreate = async () => {
    if (!newSkill.name.trim() || !newSkill.category.trim()) {
      setError("Name and category are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await taxonomyService.adminCreate({
        name: newSkill.name.trim(),
        category: newSkill.category.trim(),
        subcategory: newSkill.subcategory.trim() || undefined,
        type: newSkill.type as any,
      });
      flash(`Created skill "${newSkill.name}".`);
      setNewSkill({ name: "", category: "", subcategory: "", type: "technical" });
      setShowAddForm(false);
      fetchSkills();
    } catch (err: any) {
      setError(err.message || "Failed to create skill (it may already exist).");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (skill: SkillTaxonomyEntry) => {
    try {
      if (skill.active) await taxonomyService.adminDeactivate(skill.id);
      else await taxonomyService.adminReactivate(skill.id);
      flash(`${skill.active ? "Deactivated" : "Reactivated"} "${skill.name}".`);
      fetchSkills();
    } catch (err: any) {
      setError(err.message || "Failed to update skill status.");
    }
  };

  const handleMerge = async () => {
    if (!mergeSource || !mergeTarget || mergeSource === mergeTarget) {
      setError("Pick two different skills to merge.");
      return;
    }
    try {
      await taxonomyService.adminMerge(mergeSource, mergeTarget);
      flash(`Merged "${mergeSource}" into "${mergeTarget}".`);
      setMergeSource("");
      setMergeTarget("");
      fetchSkills();
    } catch (err: any) {
      setError(err.message || "Merge failed.");
    }
  };

  const handleApprove = async (item: SkillReviewQueueItem) => {
    if (!approveForm.category.trim()) {
      setError("Pick a category before approving.");
      return;
    }
    setApprovingId(item.id);
    try {
      await taxonomyService.adminApproveReviewItem(item.id, approveForm.category, approveForm.subcategory, approveForm.type);
      flash(`Approved "${item.term}" as a new canonical skill.`);
      fetchQueue();
      fetchSkills();
    } catch (err: any) {
      setError(err.message || "Approval failed.");
    } finally {
      setApprovingId(null);
    }
  };

  const handleReject = async (item: SkillReviewQueueItem) => {
    try {
      await taxonomyService.adminRejectReviewItem(item.id);
      flash(`Rejected "${item.term}".`);
      fetchQueue();
    } catch (err: any) {
      setError(err.message || "Rejection failed.");
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-slate-900">Skill Taxonomy Management</h1>
        <p className="text-sm text-slate-500">
          Add, edit, deactivate, and merge canonical skills. Review terms auto-discovered from live job descriptions.
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-200">
        <button
          onClick={() => setTab("taxonomy")}
          className={`px-4 py-2 text-sm font-medium border-b-2 ${tab === "taxonomy" ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500"}`}
        >
          Taxonomy
        </button>
        <button
          onClick={() => setTab("review-queue")}
          className={`px-4 py-2 text-sm font-medium border-b-2 flex items-center gap-1.5 ${tab === "review-queue" ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500"}`}
        >
          <Inbox className="h-3.5 w-3.5" /> Review Queue {queueItems.length > 0 && `(${queueItems.length})`}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}
      {successMessage && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4 shrink-0" /> {successMessage}
        </div>
      )}

      {tab === "taxonomy" && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search skills..."
                className="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
            <div className="flex gap-2">
              <button onClick={fetchSkills} className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </button>
              <button
                onClick={() => setShowAddForm((v) => !v)}
                className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-3.5 w-3.5" /> Add Skill
              </button>
            </div>
          </div>

          {showAddForm && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 grid gap-3 sm:grid-cols-5">
              <input placeholder="Name" value={newSkill.name} onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
              <input placeholder="Category" value={newSkill.category} onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
              <input placeholder="Subcategory (optional)" value={newSkill.subcategory} onChange={(e) => setNewSkill({ ...newSkill, subcategory: e.target.value })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
              <select value={newSkill.type} onChange={(e) => setNewSkill({ ...newSkill, type: e.target.value })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <option value="technical">Technical</option>
                <option value="tool">Tool</option>
                <option value="soft">Soft</option>
                <option value="domain">Domain</option>
              </select>
              <button disabled={submitting} onClick={handleCreate} className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
                {submitting ? "Creating..." : "Create"}
              </button>
            </div>
          )}

          <div className="rounded-xl border border-slate-200 p-4">
            <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-slate-700"><Merge className="h-4 w-4" /> Merge Duplicate Skill</h3>
            <div className="flex flex-col gap-2 sm:flex-row">
              <select value={mergeSource} onChange={(e) => setMergeSource(e.target.value)} className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <option value="">Source (will be deactivated)...</option>
                {skills.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              <select value={mergeTarget} onChange={(e) => setMergeTarget(e.target.value)} className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <option value="">Target (canonical skill)...</option>
                {skills.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              <button onClick={handleMerge} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900">
                Merge
              </button>
            </div>
          </div>

          {loading ? (
            <div className="py-12 text-center text-sm text-slate-500">Loading skills...</div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Category / Subcategory</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Assessment</th>
                    <th className="px-4 py-3">Popularity</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {skills.map((s) => (
                    <tr key={s.id} className={!s.active ? "opacity-50" : ""}>
                      <td className="px-4 py-3 font-medium text-slate-900">{s.name}</td>
                      <td className="px-4 py-3 text-slate-500">{s.category}{s.subcategory ? ` / ${s.subcategory}` : ""}</td>
                      <td className="px-4 py-3 text-slate-500">{s.type}</td>
                      <td className="px-4 py-3">
                        {s.assessmentAvailable ? <span className="text-emerald-600 font-medium">Available</span> : <span className="text-slate-400">None</span>}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{s.popularity}</td>
                      <td className="px-4 py-3">{s.active ? <span className="text-emerald-600">Active</span> : <span className="text-rose-500">Inactive</span>}</td>
                      <td className="px-4 py-3 text-right">
                        <button onClick={() => handleToggleActive(s)} title={s.active ? "Deactivate" : "Reactivate"} className="text-slate-400 hover:text-slate-700">
                          <Power className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "review-queue" && (
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            Terms detected repeatedly in real live job descriptions (via the connected Job Market Intelligence feed) that
            are not yet part of the canonical taxonomy. Approve to add as a new skill, or reject if it isn't a genuine skill.
          </p>
          {loadingQueue ? (
            <div className="py-12 text-center text-sm text-slate-500">Loading review queue...</div>
          ) : queueItems.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-500">No pending items. Nothing to review right now.</div>
          ) : (
            <div className="space-y-3">
              {queueItems.map((item) => (
                <div key={item.id} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-slate-900">{item.term}</h4>
                    <span className="text-xs text-slate-400">{item.occurrences} occurrence(s)</span>
                  </div>
                  {item.example_context && <p className="mt-1 text-xs text-slate-500 line-clamp-2">{item.example_context}</p>}
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                    <input
                      placeholder="Category"
                      value={approveForm.category}
                      onChange={(e) => setApproveForm({ ...approveForm, category: e.target.value })}
                      className="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs"
                    />
                    <input
                      placeholder="Subcategory (optional)"
                      value={approveForm.subcategory}
                      onChange={(e) => setApproveForm({ ...approveForm, subcategory: e.target.value })}
                      className="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs"
                    />
                    <select
                      value={approveForm.type}
                      onChange={(e) => setApproveForm({ ...approveForm, type: e.target.value })}
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs"
                    >
                      <option value="tool">Tool</option>
                      <option value="technical">Technical</option>
                      <option value="soft">Soft</option>
                      <option value="domain">Domain</option>
                    </select>
                    <button
                      disabled={approvingId === item.id}
                      onClick={() => handleApprove(item)}
                      className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" /> Approve
                    </button>
                    <button
                      onClick={() => handleReject(item)}
                      className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                    >
                      <XCircle className="h-3.5 w-3.5" /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminSkillsPage;
