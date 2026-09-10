import { apiRequest, simulate } from "./api";
import {
  mockApplications,
  mockFeedback,
  mockLearning,
  mockNotifications,
  mockOpportunities,
  mockReadinessBreakdown,
  mockReadinessTrend,
  mockSkillGaps,
  mockSkills,
  mockStudent,
} from "../data/mockData";
import type { Opportunity, Skill, SkillGap, StudentProfile } from "../types";

export const studentService = {
  getProfile: async (): Promise<StudentProfile> => {
    try {
      const data = await apiRequest<any>("/users/me");
      return {
        ...mockStudent,
        ...data,
        id: data.uid || data.id || mockStudent.id,
      };
    } catch (e) {
      return simulate(mockStudent);
    }
  },

  getSkills: async (): Promise<Skill[]> => {
    try {
      const data = await apiRequest<Skill[]>("/skills/me");
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
      return simulate(mockSkills);
    } catch (e) {
      return simulate(mockSkills);
    }
  },

  getSkillGaps: async (): Promise<SkillGap[]> => {
    try {
      const benchmark = await apiRequest<{ gaps: SkillGap[] }>("/matching/role-benchmark");
      if (benchmark && Array.isArray(benchmark.gaps) && benchmark.gaps.length > 0) {
        return benchmark.gaps;
      }
      return simulate(mockSkillGaps);
    } catch (e) {
      return simulate(mockSkillGaps);
    }
  },

  getOpportunities: async (): Promise<Opportunity[]> => {
    try {
      const jobs = await apiRequest<any[]>("/jobs");
      if (Array.isArray(jobs) && jobs.length > 0) {
        return jobs.map((j) => ({
          id: j.id,
          title: j.title,
          company: j.company,
          logo: j.logo || "CO",
          location: j.location,
          type: j.type || "Internship",
          mode: j.workMode || "Hybrid",
          stipend: j.stipend || "₹40,000/mo",
          skills: (j.requiredSkills || []).map((s: any) => (typeof s === "string" ? s : s.name)),
          matchScore: j.matchScore || 80,
          postedAgo: "Recently",
          deadline: j.deadline || "Open",
          applicants: j.applicants || 0,
          description: j.description,
        }));
      }
      return simulate(mockOpportunities);
    } catch (e) {
      return simulate(mockOpportunities);
    }
  },

  getJob: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/jobs/${jobId}`);
  },

  getJobMatch: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/matching/job/${jobId}`);
  },

  getLearningPaths: async (): Promise<any[]> => {
    try {
      const data = await apiRequest<any[]>("/learning-paths/me");
      return Array.isArray(data) ? data : [];
    } catch (e) {
      return [];
    }
  },

  getLearningPathById: async (pathId: string): Promise<any> => {
    return apiRequest<any>(`/learning-paths/me/${pathId}`);
  },

  createLearningPath: async (jobId: string): Promise<any> => {
    return apiRequest<any>("/learning-paths", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId }),
    });
  },

  updateLearningPathSkill: async (
    pathId: string,
    skillId: string,
    status: "not_started" | "in_progress" | "completed"
  ): Promise<any> => {
    return apiRequest<any>(`/learning-paths/me/${pathId}/skills/${skillId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  updateLearningPathStatus: async (
    pathId: string,
    status: "active" | "completed" | "archived"
  ): Promise<any> => {
    return apiRequest<any>(`/learning-paths/me/${pathId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  getEvidence: async (): Promise<any[]> => {
    try {
      const data = await apiRequest<any[]>("/evidence/me");
      return Array.isArray(data) ? data : [];
    } catch (e) {
      return [];
    }
  },

  getEvidenceById: async (evidenceId: string): Promise<any> => {
    return apiRequest<any>(`/evidence/me/${evidenceId}`);
  },

  createEvidence: async (payload: {
    type: "project" | "certificate" | "course" | "assessment" | "other";
    title: string;
    description?: string;
    skill_ids?: string[];
    issuer?: string;
    issue_date?: string;
    credential_id?: string;
    project_url?: string;
    source_url?: string;
    file_path?: string;
  }): Promise<any> => {
    return apiRequest<any>("/evidence", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateEvidence: async (
    evidenceId: string,
    payload: {
      title?: string;
      description?: string;
      type?: "project" | "certificate" | "course" | "assessment" | "other";
      skill_ids?: string[];
      issuer?: string;
      issue_date?: string;
      credential_id?: string;
      project_url?: string;
      source_url?: string;
      file_path?: string;
    }
  ): Promise<any> => {
    return apiRequest<any>(`/evidence/me/${evidenceId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteEvidence: async (evidenceId: string): Promise<any> => {
    return apiRequest<any>(`/evidence/me/${evidenceId}`, {
      method: "DELETE",
    });
  },

  uploadEvidenceFile: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append("file", file);
    return apiRequest<any>("/evidence/upload", {
      method: "POST",
      body: formData,
    });
  },

  addSkill: async (payload: {
    name: string;
    category: "Technical" | "Soft" | "Domain" | "Tools";
    proficiency: number;
    source?: string;
    evidence?: any;
  }): Promise<Skill> => {
    return apiRequest<Skill>("/skills/me", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateSkill: async (
    skillId: string,
    payload: {
      name?: string;
      category?: "Technical" | "Soft" | "Domain" | "Tools";
      proficiency?: number;
      evidence?: any;
    }
  ): Promise<Skill> => {
    return apiRequest<Skill>(`/skills/me/${skillId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteSkill: async (skillId: string): Promise<void> => {
    await apiRequest<void>(`/skills/me/${skillId}`, {
      method: "DELETE",
    });
  },

  getAssessmentQuestions: async (skill = "python"): Promise<any[]> => {
    return apiRequest<any[]>(`/skills/assessment/questions?skill=${encodeURIComponent(skill)}`);
  },

  submitAssessment: async (submission: {
    skillName: string;
    category: "Technical" | "Soft" | "Domain" | "Tools";
    answers: { questionId: string; selectedOption: number }[];
  }): Promise<any> => {
    return apiRequest<any>("/skills/assessment", {
      method: "POST",
      body: JSON.stringify(submission),
    });
  },

  getLearning: () => simulate(mockLearning),
  getApplications: () => simulate(mockApplications),
  getMentorFeedback: () => simulate(mockFeedback),
  getNotifications: () => simulate(mockNotifications),
  getReadinessTrend: () => simulate(mockReadinessTrend),
  getReadinessBreakdown: () => simulate(mockReadinessBreakdown),
};

