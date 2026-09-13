import { apiRequest } from "./api";

export interface SocialLinks {
  github?: string;
  linkedin?: string;
  portfolio?: string;
}

export type InstitutionVerificationStatus = "VERIFIED" | "NOT_VERIFIED" | "SOURCE_UNAVAILABLE";

/** Generic authenticated-user profile shape shared across all roles (student, faculty, recruiter, institution, admin). */
export interface MyProfile {
  uid: string;
  email: string;
  name: string;
  role: string;
  avatar?: string;
  phone?: string;
  institution?: string;
  institution_id?: string;
  institutionCode?: string;
  institutionState?: string;
  institutionDistrict?: string;
  institutionVerificationStatus?: InstitutionVerificationStatus | null;
  institutionVerificationSource?: string | null;
  institutionLastVerifiedAt?: string | null;
  department?: string;
  degree?: string;
  branch?: string;
  year?: string;
  cgpa?: number;
  rollNo?: string;
  location?: string;
  headline?: string;
  about?: string;
  targetRole?: string;
  links?: SocialLinks;
  verified?: boolean;
}

export interface UpdateProfilePayload {
  name?: string;
  phone?: string;
  avatar?: string;
  /** Free-text institution name. Setting this alone always yields NOT_VERIFIED. */
  institution?: string;
  /** Canonical registry id from institutionService.search() results. The backend derives
   *  institution name/state/district/verification status from this - never trust anything
   *  the client sends for those derived fields, because it won't be accepted (extra="forbid"). */
  institution_id?: string;
  department?: string;
  degree?: string;
  branch?: string;
  year?: string;
  cgpa?: number;
  rollNo?: string;
  location?: string;
  headline?: string;
  about?: string;
  targetRole?: string;
  links?: SocialLinks;
}

export const userService = {
  getMe: async (): Promise<MyProfile> => apiRequest<MyProfile>("/users/me"),

  updateMe: async (payload: UpdateProfilePayload): Promise<MyProfile> =>
    apiRequest<MyProfile>("/users/me", { method: "PUT", body: JSON.stringify(payload) }),
};
