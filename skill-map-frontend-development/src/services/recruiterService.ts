import { apiRequest } from "./api";

export interface RecruiterJobPayload {
  title: string;
  company: string;
  description: string;
  location: string;
  employment_type?: string;
  type?: string;
  workMode?: "Remote" | "Hybrid" | "On-site";
  stipend?: string;
  required_skills: {
    name: string;
    required_proficiency: number;
    weight: number;
  }[];
  preferred_skills?: string[];
  minimum_proficiency?: number;
  application_url?: string;
  deadline?: string;
  status?: "draft" | "published" | "closed" | "archived";
}

export const recruiterService = {
  getRecruiterJobs: async (statusFilter?: string): Promise<any[]> => {
    const query = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : "";
    try {
      const data = await apiRequest<any[]>(`/recruiter/jobs${query}`);
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Failed to fetch recruiter jobs", e);
      return [];
    }
  },

  getRecruiterJobById: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/recruiter/jobs/${jobId}`);
  },

  createRecruiterJob: async (payload: RecruiterJobPayload): Promise<any> => {
    return apiRequest<any>("/recruiter/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateRecruiterJob: async (jobId: string, payload: Partial<RecruiterJobPayload>): Promise<any> => {
    return apiRequest<any>(`/recruiter/jobs/${jobId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  archiveRecruiterJob: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/recruiter/jobs/${jobId}`, {
      method: "DELETE",
    });
  },

  getCandidatesForJob: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/recruiter/jobs/${jobId}/candidates`);
  },
};
