import { apiRequest } from "./api";

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  skill: string;
}

export interface QuizDetail {
  skill_name: string;
  total_questions: number;
  questions: QuizQuestion[];
  provenance?: {
    source: string;
    data_status: string;
  };
}

export interface QuizResult {
  assessment_id: string;
  skill_name: string;
  category: string;
  total_questions: number;
  correct_count: number;
  score_percentage: number;
  assessed_proficiency: number;
  previous_proficiency?: number | null;
  current_proficiency: number;
  preserved_verified: boolean;
  explanation: string;
  timestamp: string;
}

export interface AssessmentHistoryItem {
  assessment_id: string;
  skill_name: string;
  category: string;
  score_percentage: number;
  assessed_proficiency: number;
  correct_count: number;
  total_questions: number;
  timestamp: string;
}

export const quizService = {
  async getQuiz(skillName: string): Promise<QuizDetail> {
    return apiRequest<QuizDetail>(`/skills/quiz/${encodeURIComponent(skillName)}`);
  },

  async submitQuiz(
    skillName: string,
    category: string,
    answers: Record<string, number>
  ): Promise<QuizResult> {
    return apiRequest<QuizResult>("/skills/quiz/submit", {
      method: "POST",
      body: JSON.stringify({
        skill_name: skillName,
        category,
        answers,
      }),
    });
  },

  async getHistory(): Promise<AssessmentHistoryItem[]> {
    return apiRequest<AssessmentHistoryItem[]>("/skills/assessments/history");
  },
};
