import { useState } from "react";
import { Building2, Code2, Edit3, Globe, Link2, Mail, MapPin, Phone } from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Avatar } from "../../components/ui/Avatar";
import { PageHeader } from "../../components/ui/PageHeader";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { EditProfileModal } from "../../components/profile/EditProfileModal";
import { useFetch } from "../../hooks/useFetch";
import { userService } from "../../services/userService";
import type { UserRole } from "../../types";

const roleLabel: Record<string, string> = {
  faculty: "Faculty",
  recruiter: "Recruiter",
  institution: "Institution Admin",
  admin: "Platform Admin",
  mentor: "Mentor",
  student: "Student",
};

/**
 * Generic "My Profile" page for any role that doesn't have a bespoke one (faculty, recruiter,
 * institution, admin). Reuses the same PUT /api/users/me endpoint and edit form as the
 * student profile - every role can view and edit their own account details here.
 */
export default function ProfilePage({ role }: { role: UserRole }) {
  const [refreshKey, setRefreshKey] = useState(0);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const { data: profile, loading } = useFetch(() => userService.getMe(), [refreshKey]);

  if (loading || !profile) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Profile"
        description="Your account details on AcademiaLink."
        actions={<Button icon={<Edit3 className="h-4 w-4" />} onClick={() => setIsEditModalOpen(true)}>Edit profile</Button>}
      />

      <Card className="overflow-hidden">
        <div className="h-24 bg-gradient-to-r from-indigo-600 via-violet-600 to-sky-500 sm:h-32" />
        <CardBody className="relative pt-0">
          <div className="-mt-12 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <Avatar src={profile.avatar} name={profile.name} size="xl" className="ring-4 ring-white shadow-lg" />
              <div className="sm:pb-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-2xl font-bold text-slate-900">{profile.name}</h2>
                  <Badge tone="indigo">{roleLabel[role] || role}</Badge>
                </div>
                {profile.headline && <p className="mt-0.5 text-sm font-medium text-indigo-600">{profile.headline}</p>}
                {(profile.institution || profile.department) && (
                  <p className="mt-1 text-sm text-slate-500">
                    {[profile.department, profile.institution].filter(Boolean).join(" · ")}
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1"><Mail className="h-3.5 w-3.5" />{profile.email}</span>
                  {profile.phone && <span className="inline-flex items-center gap-1"><Phone className="h-3.5 w-3.5" />{profile.phone}</span>}
                  {profile.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{profile.location}</span>}
                </div>
              </div>
            </div>
            <div className="flex gap-2 sm:pb-1">
              {profile.links?.github && <a href={profile.links.github} target="_blank" rel="noreferrer" className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600"><Code2 className="h-4 w-4" /></a>}
              {profile.links?.linkedin && <a href={profile.links.linkedin} target="_blank" rel="noreferrer" className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600"><Link2 className="h-4 w-4" /></a>}
              {profile.links?.portfolio && <a href={profile.links.portfolio} target="_blank" rel="noreferrer" className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600"><Globe className="h-4 w-4" /></a>}
            </div>
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader title="About" />
            <CardBody>
              {profile.about ? (
                <p className="text-sm leading-relaxed text-slate-600">{profile.about}</p>
              ) : (
                <p className="text-sm italic text-slate-400">No bio added yet. Click "Edit profile" to add one.</p>
              )}
            </CardBody>
          </Card>
        </div>
        <div>
          <Card>
            <CardHeader title="Account Details" />
            <CardBody className="space-y-3 text-sm">
              <div className="flex items-center justify-between border-b border-slate-50 pb-2"><span className="text-slate-500">Role</span><span className="font-medium text-slate-800">{roleLabel[role] || role}</span></div>
              {profile.institution && (
                <div className="flex items-center justify-between border-b border-slate-50 pb-2">
                  <span className="text-slate-500 inline-flex items-center gap-1"><Building2 className="h-3.5 w-3.5" /> Institution</span>
                  <span className="font-medium text-slate-800">{profile.institution}</span>
                </div>
              )}
              {profile.department && (
                <div className="flex items-center justify-between last:border-0">
                  <span className="text-slate-500">Department</span>
                  <span className="font-medium text-slate-800">{profile.department}</span>
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>

      {isEditModalOpen && (
        <EditProfileModal
          profile={profile}
          role={role}
          onClose={() => setIsEditModalOpen(false)}
          onSaved={() => setRefreshKey((k) => k + 1)}
        />
      )}
    </div>
  );
}
