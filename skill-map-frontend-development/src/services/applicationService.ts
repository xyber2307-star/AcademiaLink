import { apiRequest } from "./api";

export type ApplicationStatus =
  | "applied"
  | "under_review"
  | "shortlisted"
  | "rejected"
  | "selected"
  | "withdrawn";

export interface JobApplication {
  application_id: string;
  student_uid: string;
  student_name?: string;
  student_email?: string;
  job_id: string;
  job_title?: string;
  company?: string;
  location?: string;
  status: ApplicationStatus;
  applied_at: string;
  updated_at: string;
  notes?: string;
  feedback?: string;
  match_score?: number;
  provenance?: {
    source: string;
    data_status: string;
  };
}

export const applicationService = {
  async applyForJob(jobId: string, notes?: string): Promise<JobApplication> {
    return apiRequest<JobApplication>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId, notes: notes || "" }),
    });
  },

  async getMyApplications(): Promise<JobApplication[]> {
    return apiRequest<JobApplication[]>("/applications/me");
  },

  async getApplicationsForJob(jobId: string): Promise<JobApplication[]> {
    return apiRequest<JobApplication[]>(`/applications/job/${jobId}`);
  },

  async updateApplicationStatus(
    applicationId: string,
    status: ApplicationStatus,
    feedback?: string
  ): Promise<JobApplication> {
    return apiRequest<JobApplication>(`/applications/${applicationId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, feedback: feedback || "" }),
    });
  },

  async withdrawApplication(applicationId: string): Promise<{ status: string; state: string }> {
    return apiRequest<{ status: string; state: string }>(`/applications/${applicationId}/withdraw`, {
      method: "PATCH",
    });
  },
};
