import { apiRequest } from "./api";
import type { InstitutionVerificationStatus } from "./userService";

export interface InstitutionSearchResult {
  institutionId: string;
  aicteId: string;
  name: string;
  state?: string | null;
  district?: string | null;
  city?: string | null;
  verificationStatus: InstitutionVerificationStatus;
  verificationSource: string;
}

export interface InstitutionSearchResponse {
  results: InstitutionSearchResult[];
  source: string;
  sourceAvailable: boolean;
  datasetDate?: string | null;
}

export interface InstitutionDetail extends InstitutionSearchResult {
  sourceReference?: string | null;
  datasetDate?: string | null;
  programLevelApprovalChecked: boolean;
}

export const institutionSearchService = {
  search: async (query: string): Promise<InstitutionSearchResponse> =>
    apiRequest<InstitutionSearchResponse>(`/institutions/search?q=${encodeURIComponent(query)}`),

  getById: async (institutionId: string): Promise<InstitutionDetail> =>
    apiRequest<InstitutionDetail>(`/institutions/${encodeURIComponent(institutionId)}`),
};
