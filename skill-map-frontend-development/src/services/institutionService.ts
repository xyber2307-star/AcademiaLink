import { apiRequest } from "./api";

export interface StudentOverviewMetrics {
  total_students: number;
  active_students: number;
  students_with_skills: number;
  students_with_learning_paths: number;
}

export interface SkillDistributionItem {
  name: string;
  count: number;
  average_proficiency: number;
  category: string;
}

export interface SkillAnalyticsMetrics {
  total_skills_recorded: number;
  most_common_skills: SkillDistributionItem[];
  proficiency_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
  common_skill_gaps: { skill: string; affected_students: number; average_gap: number }[];
}

export interface LearningAnalyticsMetrics {
  total_learning_paths: number;
  paths_by_status: Record<string, number>;
  skills_by_status: Record<string, number>;
  common_priority_skills: { skill: string; priority_count: number }[];
}

export interface EvidenceAnalyticsMetrics {
  total_evidence_submissions: number;
  evidence_by_status: Record<string, number>;
  evidence_by_type: Record<string, number>;
}

export interface MentorshipAnalyticsMetrics {
  total_mentor_assignments: number;
  active_mentor_assignments: number;
  assigned_students_count: number;
  feedback_activity_count: number;
  pending_evidence_reviews: number;
}

export interface RecruitmentAnalyticsMetrics {
  relevant_jobs_count: number;
  average_match_score: number;
  top_demand_skills: { skill: string; postings_count: number }[];
}

export interface InstitutionAnalyticsResponse {
  institution_id: string;
  institution_name: string;
  generated_at: string;
  student_overview: StudentOverviewMetrics;
  skill_analytics: SkillAnalyticsMetrics;
  learning_analytics: LearningAnalyticsMetrics;
  evidence_analytics: EvidenceAnalyticsMetrics;
  mentorship_analytics: MentorshipAnalyticsMetrics;
  recruitment_analytics: RecruitmentAnalyticsMetrics;
}

export const institutionService = {
  getAnalytics: async (institutionId?: string): Promise<InstitutionAnalyticsResponse | null> => {
    const query = institutionId ? `?institution_id=${encodeURIComponent(institutionId)}` : "";
    try {
      return await apiRequest<InstitutionAnalyticsResponse>(`/institution/analytics${query}`);
    } catch (e) {
      console.error("Failed to fetch institution analytics", e);
      return null;
    }
  },
};
