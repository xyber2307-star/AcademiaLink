import { apiRequest } from "./api";

export type UserRole = "student" | "faculty" | "recruiter" | "institution" | "admin" | "mentor";

export interface AdminUserSummary {
  uid: string;
  email: string;
  name: string;
  role: UserRole;
  institution?: string;
  institution_id?: string;
  department?: string;
  created_at?: string;
  provenance?: {
    source: string;
    data_status: string;
  };
}

export const adminService = {
  async listUsers(roleFilter?: string, limit = 50): Promise<AdminUserSummary[]> {
    const query = roleFilter ? `?role_filter=${roleFilter}&limit=${limit}` : `?limit=${limit}`;
    return apiRequest<AdminUserSummary[]>(`/admin/users${query}`);
  },

  async updateUserRole(
    uid: string,
    role: UserRole,
    department?: string,
    institutionId?: string
  ): Promise<AdminUserSummary> {
    return apiRequest<AdminUserSummary>(`/admin/users/${uid}/role`, {
      method: "PATCH",
      body: JSON.stringify({
        role,
        department: department || undefined,
        institution_id: institutionId || undefined,
      }),
    });
  },
};
