import { apiRequest } from "./api";

export interface AIChatResponse {
  reply: string;
  grounded_data: {
    skills_count?: number;
    learning_paths_count?: number;
    evidence_count?: number;
    job_analyzed?: string;
    job_match_score?: number;
  };
  timestamp: string;
  provider: string;
  data_available: boolean;
  provenance?: {
    source: string;
    data_status: string;
    retrieved_at?: string;
  };
}

export const aiAssistantService = {
  async sendMessage(message: string, jobId?: string): Promise<AIChatResponse> {
    return apiRequest<AIChatResponse>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message, job_id: jobId || undefined }),
    });
  },
};
