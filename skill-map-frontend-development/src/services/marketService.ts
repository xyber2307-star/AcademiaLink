import { apiRequest } from "./api";

export interface DataProvenance {
  source: string;
  source_url?: string;
  data_status: "available" | "unavailable" | "verified" | "unverified";
  retrieved_at?: string;
  is_test_data?: boolean;
}

export interface RequiredSkill {
  name: string;
  required_proficiency: number;
  weight: number;
}

export interface MarketJobRecord {
  job_id: string;
  company: string;
  job_title: string;
  country?: string;
  state?: string;
  city?: string;
  description?: string;
  skills: string[];
  required_skills: RequiredSkill[];
  preferred_skills: string[];
  experience?: string;
  employment_type?: string;
  posted_date?: string;
  closing_date?: string;
  source: string;
  source_url?: string;
  data_type: "observed_posting" | "verified_hiring";
  retrieved_at?: string;
  updated_at?: string;
  provenance: DataProvenance;
}

export interface MarketOverviewResponse {
  status: "available" | "empty" | "unconfigured";
  message?: string;
  total_observed_postings: number;
  total_verified_hirings: number;
  unique_companies_count: number;
  unique_roles_count: number;
  top_companies: Array<{ company: string; observed_postings: number; roles_count: number }>;
  most_requested_skills: Array<{ skill: string; observed_postings: number; percentage: number }>;
  employment_type_distribution: Record<string, number>;
  location_distribution: Record<string, number>;
  time_filter_applied: string;
  location_filter_applied: { country?: string; state?: string; city?: string };
  provenance: DataProvenance;
}

export interface CompanyMarketSummary {
  company: string;
  observed_postings: number;
  verified_hirings: number;
  unique_roles: number;
  locations: string[];
  top_skills: string[];
  is_target_company: boolean;
  is_dream_company: boolean;
}

export interface CompanyMarketDetailResponse {
  company: string;
  status: "available" | "not_found" | "unconfigured";
  message?: string;
  observed_postings_count: number;
  verified_hirings_count: number;
  roles_posted: string[];
  locations: string[];
  required_skills: Array<{ skill: string; demand_count: number; average_required_proficiency: number }>;
  preferred_skills: string[];
  experience_levels: string[];
  employment_types: string[];
  open_postings: MarketJobRecord[];
  posting_dates: string[];
  skill_frequency: Array<{ skill: string; observed_postings: number; percentage: number; average_required_proficiency: number }>;
  historical_activity: Array<{ month: string; observed_postings: number }>;
  is_target_company: boolean;
  is_dream_company: boolean;
  provenance: DataProvenance;
}

export interface SkillDemandItem {
  skill: string;
  observed_postings: number;
  percentage: number;
}

export interface SkillDemandResponse {
  status: "available" | "empty" | "unconfigured";
  message?: string;
  total_postings_analyzed: number;
  skills: SkillDemandItem[];
  filters_applied: Record<string, any>;
  provenance: DataProvenance;
}

export interface MarketTrendItem {
  month: string;
  observed_postings: number;
  unique_companies: number;
  top_skills: Array<{ skill: string; count: number }>;
  top_roles: Array<{ role: string; count: number }>;
}

export interface MarketTrendsResponse {
  status: "available" | "insufficient_data" | "unconfigured";
  message?: string;
  trends: MarketTrendItem[];
  provenance: DataProvenance;
}

export interface SkillGapAnalysisItem {
  skill: string;
  current_proficiency: number;
  required_proficiency: number;
  gap_amount: number;
  gap_category: "matched" | "partial" | "missing";
  weight: number;
  skill_score: number;
  weighted_score: number;
  priority: "High" | "Medium" | "Low";
}

export interface StudentMarketSkillGapResponse {
  target_company?: string;
  target_role?: string;
  target_location?: string;
  market_match_score: number;
  matched_skills: SkillGapAnalysisItem[];
  partial_skills: SkillGapAnalysisItem[];
  missing_skills: SkillGapAnalysisItem[];
  market_priority_skills: Array<{
    skill: string;
    current_proficiency: number;
    required_proficiency: number;
    gap_amount: number;
    market_frequency_percentage: number;
    priority: "High" | "Medium" | "Low";
  }>;
  explanation: string;
  provenance: DataProvenance;
}

export interface MarketLocationOptionsResponse {
  countries: string[];
  states: string[];
  cities: string[];
}

export interface MarketFilterParams {
  country?: string;
  state?: string;
  city?: string;
  company?: string;
  role?: string;
  category?: string;
  time_range?: "current" | "last_1_month" | "last_3_months" | "custom" | "all";
  start_date?: string;
  end_date?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

function toQuery(params?: Record<string, any>): string {
  if (!params) return "";
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  }
  const str = searchParams.toString();
  return str ? `?${str}` : "";
}

export const marketService = {
  getOverview: async (params?: MarketFilterParams): Promise<MarketOverviewResponse> => {
    return apiRequest<MarketOverviewResponse>(`/market/overview${toQuery(params)}`);
  },

  getLocations: async (): Promise<MarketLocationOptionsResponse> => {
    return apiRequest<MarketLocationOptionsResponse>("/market/locations");
  },

  getCompanies: async (params?: MarketFilterParams): Promise<CompanyMarketSummary[]> => {
    return apiRequest<CompanyMarketSummary[]>(`/market/companies${toQuery(params)}`);
  },

  getCompanyDetail: async (company: string, params?: MarketFilterParams): Promise<CompanyMarketDetailResponse> => {
    return apiRequest<CompanyMarketDetailResponse>(`/market/company/${encodeURIComponent(company)}${toQuery(params)}`);
  },

  getJobs: async (params?: MarketFilterParams): Promise<MarketJobRecord[]> => {
    return apiRequest<MarketJobRecord[]>(`/market/jobs${toQuery(params)}`);
  },

  getSkillDemand: async (params?: MarketFilterParams): Promise<SkillDemandResponse> => {
    return apiRequest<SkillDemandResponse>(`/market/skills${toQuery(params)}`);
  },

  getTrends: async (params?: { country?: string; state?: string; city?: string; company?: string }): Promise<MarketTrendsResponse> => {
    return apiRequest<MarketTrendsResponse>(`/market/trends${toQuery(params)}`);
  },

  getStudentMarketSkillGap: async (params?: { company?: string; role?: string; country?: string; state?: string; city?: string }): Promise<StudentMarketSkillGapResponse> => {
    return apiRequest<StudentMarketSkillGapResponse>(`/market/skill-gap${toQuery(params)}`);
  },

  setCompanyPreference: async (company: string, preference_type: "target" | "dream", action: "add" | "remove") => {
    return apiRequest<{ success: boolean; company: string; target_companies: string[]; dream_companies: string[] }>("/market/companies/preference", {
      method: "POST",
      body: JSON.stringify({
        company,
        preference_type,
        action,
      }),
    });
  },
};
