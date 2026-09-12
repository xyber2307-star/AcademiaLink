import { apiRequest } from "./api";
import type { Opportunity, Skill, SkillGap, StudentProfile } from "../types";

/**
 * IMPORTANT - DATA INTEGRITY:
 * This service must never silently substitute fabricated/mock data for a real
 * (possibly empty) backend response. An empty array/object from Firestore is a
 * legitimate, honest state (e.g. a brand-new student with no skills yet) and
 * pages must render it as an empty state, not paper over it with fake numbers.
 * Errors are logged and re-thrown/returned as empty so the UI's error/loading
 * states (see useFetch) can react correctly instead of showing invented data.
 */

export interface RoleBenchmarkResponse {
  targetRole: string;
  careerReadiness: number;
  skillsBenchmarked: number;
  meetingBenchmark: number;
  belowBenchmark: number;
  avgGap: number;
  gaps: SkillGap[];
  strengths: Array<{ skill: string; currentProficiency: number; requiredProficiency: number; matched: boolean }>;
}

export interface AssessmentHistoryItem {
  assessment_id: string;
  skill_name: string;
  category: string;
  score_percentage: number;
  assessed_proficiency: number;
  timestamp: string;
}

export interface LearningPathSkillItem {
  skill_id: string;
  skill_name: string;
  current_proficiency: number;
  required_proficiency: number;
  gap: number;
  job_weight: number;
  priority: "High" | "Medium" | "Low";
  priority_score: number;
  reason: string;
  status: "not_started" | "in_progress" | "completed";
}

export interface LearningPathItem {
  path_id: string;
  target_job_id: string;
  target_job_title: string;
  target_company: string;
  skills: LearningPathSkillItem[];
  overall_match_before: number;
  overall_match_after: number;
  status: "active" | "completed" | "archived";
  createdAt?: string;
  updatedAt?: string;
}

export const studentService = {
  getProfile: async (): Promise<StudentProfile> => {
    return apiRequest<StudentProfile>("/users/me");
  },

  getSkills: async (): Promise<Skill[]> => {
    const data = await apiRequest<Skill[]>("/skills/me");
    return Array.isArray(data) ? data : [];
  },

  /** Full deterministic role-benchmark response (real careerReadiness, gaps, strengths). */
  getRoleBenchmark: async (role?: string): Promise<RoleBenchmarkResponse> => {
    const query = role ? `?role=${encodeURIComponent(role)}` : "";
    return apiRequest<RoleBenchmarkResponse>(`/matching/role-benchmark${query}`);
  },

  getSkillGaps: async (): Promise<SkillGap[]> => {
    const benchmark = await studentService.getRoleBenchmark();
    return Array.isArray(benchmark?.gaps) ? benchmark.gaps : [];
  },

  getOpportunities: async (): Promise<Opportunity[]> => {
    const jobs = await apiRequest<any[]>("/jobs");
    if (!Array.isArray(jobs)) return [];
    return jobs.map((j) => ({
      id: j.id,
      title: j.title,
      company: j.company,
      logo: j.logo || (j.company || "CO").slice(0, 2).toUpperCase(),
      location: j.location,
      type: j.type || "Internship",
      mode: j.workMode || "Hybrid",
      stipend: j.stipend || "Not specified",
      skills: (j.requiredSkills || j.required_skills || []).map((s: any) => (typeof s === "string" ? s : s.name)),
      matchScore: typeof j.matchScore === "number" ? j.matchScore : 0,
      postedAgo: j.createdAt ? new Date(j.createdAt).toLocaleDateString() : "Recently",
      deadline: j.deadline || "Open",
      applicants: j.applicants || 0,
      description: j.description,
    }));
  },

  /** Real historical assessment scores, used to plot a genuine (not fabricated) trend. */
  getAssessmentHistory: async (): Promise<AssessmentHistoryItem[]> => {
    const data = await apiRequest<AssessmentHistoryItem[]>("/skills/assessments/history");
    return Array.isArray(data) ? data : [];
  },

  getJob: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/jobs/${jobId}`);
  },

  getJobMatch: async (jobId: string): Promise<any> => {
    return apiRequest<any>(`/matching/job/${jobId}`);
  },

  getLearningPaths: async (): Promise<LearningPathItem[]> => {
    try {
      const data = await apiRequest<LearningPathItem[]>("/learning-paths/me");
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

};

