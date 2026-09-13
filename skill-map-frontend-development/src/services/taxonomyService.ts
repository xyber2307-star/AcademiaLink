import { apiRequest } from "./api";

export type SkillTaxonomyType = "technical" | "tool" | "soft" | "domain";

export interface SkillTaxonomyEntry {
  id: string;
  name: string;
  category: string;
  subcategory?: string | null;
  type: SkillTaxonomyType;
  description?: string;
  aliases: string[];
  relatedSkills: string[];
  parentSkill?: string | null;
  assessmentAvailable: boolean;
  active: boolean;
  source: string;
  version: number;
  popularity: number;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface SkillTaxonomyCategoriesResponse {
  categories: string[];
  subcategories_by_category: Record<string, string[]>;
}

export interface SkillRecommendationItem {
  skill: string;
  reason: string;
  market_frequency_percentage?: number | null;
  priority: "High" | "Medium" | "Low";
}

export interface SkillRecommendationsResponse {
  target_role?: string | null;
  current_skills: string[];
  recommendations: SkillRecommendationItem[];
  explanation: string;
  provenance: { source: string; data_status: string; retrieved_at?: string | null };
}

export interface SkillReviewQueueItem {
  id: string;
  term: string;
  occurrences: number;
  example_context?: string | null;
  status: "pending" | "approved" | "rejected";
  createdAt?: string | null;
  updatedAt?: string | null;
}

function toQuery(params?: Record<string, any>): string {
  if (!params) return "";
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.append(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const taxonomyService = {
  search: async (params?: { q?: string; category?: string; subcategory?: string; type?: string; limit?: number }): Promise<SkillTaxonomyEntry[]> =>
    apiRequest<SkillTaxonomyEntry[]>(`/skills/taxonomy/search${toQuery(params)}`),

  getCategories: async (): Promise<SkillTaxonomyCategoriesResponse> =>
    apiRequest<SkillTaxonomyCategoriesResponse>("/skills/taxonomy/categories"),

  getPopular: async (limit = 12): Promise<SkillTaxonomyEntry[]> =>
    apiRequest<SkillTaxonomyEntry[]>(`/skills/taxonomy/popular?limit=${limit}`),

  getSkill: async (skillId: string): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>(`/skills/taxonomy/${encodeURIComponent(skillId)}`),

  getRecommendations: async (): Promise<SkillRecommendationsResponse> =>
    apiRequest<SkillRecommendationsResponse>("/skills/taxonomy/recommendations/me"),

  // Admin-only
  adminList: async (params?: { include_inactive?: boolean; q?: string }): Promise<SkillTaxonomyEntry[]> =>
    apiRequest<SkillTaxonomyEntry[]>(`/admin/skills${toQuery(params)}`),

  adminCreate: async (payload: Partial<SkillTaxonomyEntry> & { name: string; category: string }): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>("/admin/skills", { method: "POST", body: JSON.stringify(payload) }),

  adminUpdate: async (skillId: string, payload: Partial<SkillTaxonomyEntry>): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>(`/admin/skills/${encodeURIComponent(skillId)}`, { method: "PUT", body: JSON.stringify(payload) }),

  adminDeactivate: async (skillId: string): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>(`/admin/skills/${encodeURIComponent(skillId)}`, { method: "DELETE" }),

  adminReactivate: async (skillId: string): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>(`/admin/skills/${encodeURIComponent(skillId)}/reactivate`, { method: "POST" }),

  adminMerge: async (sourceSkillId: string, targetSkillId: string): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>("/admin/skills/merge", {
      method: "POST",
      body: JSON.stringify({ source_skill_id: sourceSkillId, target_skill_id: targetSkillId }),
    }),

  adminReviewQueue: async (statusFilter: "pending" | "approved" | "rejected" = "pending"): Promise<SkillReviewQueueItem[]> =>
    apiRequest<SkillReviewQueueItem[]>(`/admin/skills/review-queue?status=${statusFilter}`),

  adminApproveReviewItem: async (itemId: string, category: string, subcategory: string, type: string): Promise<SkillTaxonomyEntry> =>
    apiRequest<SkillTaxonomyEntry>(
      `/admin/skills/review-queue/${encodeURIComponent(itemId)}/approve${toQuery({ category, subcategory, type })}`,
      { method: "POST" }
    ),

  adminRejectReviewItem: async (itemId: string): Promise<{ success: boolean }> =>
    apiRequest<{ success: boolean }>(`/admin/skills/review-queue/${encodeURIComponent(itemId)}/reject`, { method: "POST" }),
};
