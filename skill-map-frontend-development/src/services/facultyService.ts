import { apiRequest } from "./api";

export interface AssignedStudentSummary {
  student_uid: string;
  name: string;
  email: string;
  avatar?: string;
  targetRole?: string;
  department?: string;
  institution?: string;
  skill_count: number;
  pending_evidence_count: number;
  assignment_id?: string;
  assignedAt?: string;
}

export interface MentorInfo {
  uid: string;
  name: string;
  email: string;
  avatar?: string;
  department?: string;
  institution?: string;
  role: string;
}

export interface AssignedMentorResponse {
  assigned: boolean;
  mentor: MentorInfo | null;
}

export interface MentorFeedbackPayload {
  message: string;
  related_skill_id?: string;
  related_learning_path_id?: string;
}

export interface MentorFeedbackItem {
  feedback_id: string;
  id: string;
  student_uid: string;
  mentor_uid: string;
  mentor_name?: string;
  message: string;
  related_skill_id?: string;
  related_learning_path_id?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface EvidenceReviewPayload {
  verification_status: "approved" | "rejected";
  verification_notes?: string;
  student_uid?: string;
}

export interface PendingEvidenceItem {
  evidence_id: string;
  id: string;
  user_id: string;
  student_name?: string;
  student_email?: string;
  type: string;
  title: string;
  description?: string;
  skill_ids?: string[];
  issuer?: string;
  issue_date?: string;
  credential_id?: string;
  project_url?: string;
  source_url?: string;
  file_path?: string;
  verification_status: string;
  verification_notes?: string;
  reviewer_id?: string;
  submittedAt?: string;
  createdAt?: string;
}

export interface StudentMentoringDetail {
  student_uid: string;
  profile: any;
  skills: any[];
  learning_paths: any[];
  evidence: any[];
  feedback: MentorFeedbackItem[];
  skill_gaps?: any[];
}

export const facultyService = {
  getAssignedStudents: async (): Promise<AssignedStudentSummary[]> => {
    try {
      const data = await apiRequest<AssignedStudentSummary[]>("/faculty/students");
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Failed to fetch assigned students", e);
      return [];
    }
  },

  getAssignedStudentDetail: async (studentUid: string): Promise<StudentMentoringDetail | null> => {
    try {
      return await apiRequest<StudentMentoringDetail>(`/faculty/students/${encodeURIComponent(studentUid)}`);
    } catch (e) {
      console.error(`Failed to fetch student details for ${studentUid}`, e);
      return null;
    }
  },

  getPendingEvidence: async (): Promise<PendingEvidenceItem[]> => {
    try {
      const data = await apiRequest<PendingEvidenceItem[]>("/faculty/evidence/pending");
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Failed to fetch pending evidence", e);
      return [];
    }
  },

  reviewEvidence: async (evidenceId: string, payload: EvidenceReviewPayload): Promise<any> => {
    return apiRequest<any>(`/faculty/evidence/${encodeURIComponent(evidenceId)}/review`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  createStudentFeedback: async (studentUid: string, payload: MentorFeedbackPayload): Promise<MentorFeedbackItem> => {
    return apiRequest<MentorFeedbackItem>(`/faculty/students/${encodeURIComponent(studentUid)}/feedback`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getStudentFeedbackHistory: async (studentUid: string): Promise<MentorFeedbackItem[]> => {
    try {
      const data = await apiRequest<MentorFeedbackItem[]>(`/faculty/students/${encodeURIComponent(studentUid)}/feedback`);
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Failed to fetch student feedback history", e);
      return [];
    }
  },

  getMyMentor: async (): Promise<AssignedMentorResponse> => {
    try {
      return await apiRequest<AssignedMentorResponse>("/mentor/me");
    } catch (e) {
      console.error("Failed to fetch assigned mentor", e);
      return { assigned: false, mentor: null };
    }
  },

  getMyMentorFeedback: async (): Promise<MentorFeedbackItem[]> => {
    try {
      const data = await apiRequest<MentorFeedbackItem[]>("/mentor/me/feedback");
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Failed to fetch my mentor feedback", e);
      return [];
    }
  },
};
