import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "../ui/Button";
import { userService, MyProfile, UpdateProfilePayload } from "../../services/userService";
import type { InstitutionSearchResult } from "../../services/institutionSearchService";
import { InstitutionSearchInput } from "./InstitutionSearchInput";
import type { UserRole } from "../../types";

interface Props {
  profile: MyProfile;
  role: UserRole;
  onClose: () => void;
  onSaved: (updated: MyProfile) => void;
}

/**
 * Generic profile-edit form reused by every role (student, faculty, recruiter, institution,
 * admin) - the backend's PUT /api/users/me endpoint is already role-agnostic; only the
 * frontend previously lacked a working edit UI for anyone but a dead "Edit profile" button.
 */
export function EditProfileModal({ profile, role, onClose, onSaved }: Props) {
  const [form, setForm] = useState({
    name: profile.name || "",
    phone: profile.phone || "",
    location: profile.location || "",
    headline: profile.headline || "",
    about: profile.about || "",
    avatar: profile.avatar || "",
    institution: profile.institution || "",
    department: profile.department || "",
    degree: profile.degree || "",
    branch: profile.branch || "",
    year: profile.year || "",
    rollNo: profile.rollNo || "",
    targetRole: profile.targetRole || "",
    github: profile.links?.github || "",
    linkedin: profile.links?.linkedin || "",
    portfolio: profile.links?.portfolio || "",
  });
  const [institutionSelection, setInstitutionSelection] = useState({
    institution_id: profile.institution_id || "",
    institution: profile.institution || "",
    institutionState: profile.institutionState || "",
    institutionDistrict: profile.institutionDistrict || "",
    institutionCode: profile.institutionCode || "",
    institutionVerificationStatus: profile.institutionVerificationStatus ?? null,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("Name cannot be empty.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: UpdateProfilePayload = {
        name: form.name.trim(),
        phone: form.phone.trim() || undefined,
        location: form.location.trim() || undefined,
        headline: form.headline.trim() || undefined,
        about: form.about.trim() || undefined,
        avatar: form.avatar.trim() || undefined,
        links: {
          github: form.github.trim() || undefined,
          linkedin: form.linkedin.trim() || undefined,
          portfolio: form.portfolio.trim() || undefined,
        },
      };
      if (role === "student" || role === "faculty") {
        if (institutionSelection.institution_id) {
          // Canonical selection from the registry search - backend re-derives and
          // authoritatively verifies name/state/district/status from this id.
          payload.institution_id = institutionSelection.institution_id;
        } else {
          // Free text only (no registry match selected) - backend marks NOT_VERIFIED.
          payload.institution = form.institution.trim() || undefined;
          payload.institution_id = "";
        }
      }
      if (role === "student") {
        payload.degree = form.degree.trim() || undefined;
        payload.branch = form.branch.trim() || undefined;
        payload.year = form.year.trim() || undefined;
        payload.rollNo = form.rollNo.trim() || undefined;
        payload.targetRole = form.targetRole.trim() || undefined;
      }
      if (role === "faculty" || role === "institution") {
        payload.department = form.department.trim() || undefined;
      }
      if (role === "institution") {
        payload.institution = form.institution.trim() || undefined;
      }
      const updated = await userService.updateMe(payload);
      onSaved(updated);
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to save profile changes. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <h3 className="text-lg font-bold text-slate-900">Edit Profile</h3>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="mt-4 space-y-4">
          {error && <div className="rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{error}</div>}

          <div>
            <label className="block text-xs font-semibold text-slate-700">Full Name *</label>
            <input value={form.name} onChange={set("name")} required className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700">Phone</label>
              <input value={form.phone} onChange={set("phone")} placeholder="+91 98765 43210" className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700">Location</label>
              <input value={form.location} onChange={set("location")} placeholder="Bengaluru, India" className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700">Headline</label>
            <input value={form.headline} onChange={set("headline")} placeholder="e.g. Final-year CS student | Aspiring Backend Engineer" className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700">About</label>
            <textarea value={form.about} onChange={set("about")} rows={3} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700">Avatar URL</label>
            <input value={form.avatar} onChange={set("avatar")} placeholder="https://..." className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
          </div>

          {(role === "student" || role === "faculty" || role === "institution") && (
            <div className="grid grid-cols-2 gap-3 border-t border-slate-100 pt-3">
              {role === "institution" ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Institution</label>
                  <input value={form.institution} onChange={set("institution")} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
                </div>
              ) : (
                <div className="col-span-2">
                  <InstitutionSearchInput
                    freeTextValue={form.institution}
                    onFreeTextChange={(value) => {
                      setForm((f) => ({ ...f, institution: value }));
                      setInstitutionSelection((s) => ({ ...s, institution_id: "" }));
                    }}
                    selected={institutionSelection}
                    onSelect={(result: InstitutionSearchResult) => {
                      setForm((f) => ({ ...f, institution: result.name }));
                      setInstitutionSelection({
                        institution_id: result.institutionId,
                        institution: result.name,
                        institutionState: result.state || "",
                        institutionDistrict: result.district || "",
                        institutionCode: result.aicteId,
                        institutionVerificationStatus: result.verificationStatus,
                      });
                    }}
                    onClearSelection={() => {
                      setForm((f) => ({ ...f, institution: "" }));
                      setInstitutionSelection({
                        institution_id: "",
                        institution: "",
                        institutionState: "",
                        institutionDistrict: "",
                        institutionCode: "",
                        institutionVerificationStatus: null,
                      });
                    }}
                  />
                </div>
              )}
              {role !== "student" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Department</label>
                  <input value={form.department} onChange={set("department")} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
                </div>
              )}
              {role === "student" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700">Roll Number</label>
                  <input value={form.rollNo} onChange={set("rollNo")} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
                </div>
              )}
            </div>
          )}

          {role === "student" && (
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700">Degree</label>
                <input value={form.degree} onChange={set("degree")} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700">Branch</label>
                <input value={form.branch} onChange={set("branch")} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700">Year</label>
                <input value={form.year} onChange={set("year")} className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
              </div>
            </div>
          )}

          {role === "student" && (
            <div>
              <label className="block text-xs font-semibold text-slate-700">Target Role</label>
              <input value={form.targetRole} onChange={set("targetRole")} placeholder="e.g. Software Engineer" className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
            </div>
          )}

          <div className="grid grid-cols-3 gap-3 border-t border-slate-100 pt-3">
            <div>
              <label className="block text-[11px] text-slate-500">GitHub</label>
              <input value={form.github} onChange={set("github")} placeholder="username" className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
            </div>
            <div>
              <label className="block text-[11px] text-slate-500">LinkedIn</label>
              <input value={form.linkedin} onChange={set("linkedin")} placeholder="username" className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
            </div>
            <div>
              <label className="block text-[11px] text-slate-500">Portfolio</label>
              <input value={form.portfolio} onChange={set("portfolio")} placeholder="https://..." className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100" />
            </div>
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <Button type="button" variant="ghost" onClick={onClose} disabled={saving}>Cancel</Button>
            <Button type="submit" loading={saving}>Save Changes</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
