import { apiRequest } from "./api";

export type NotificationType =
  | "application_status_changed"
  | "evidence_reviewed"
  | "mentor_feedback"
  | "job_match"
  | "learning_path_created"
  | "assessment_completed"
  | "general";

export interface NotificationItem {
  notification_id: string;
  uid: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  related_id?: string;
  provenance?: {
    source: string;
    data_status: string;
  };
}

export interface NotificationListResponse {
  notifications: NotificationItem[];
  unread_count: number;
}

export const notificationService = {
  async getMyNotifications(limit = 50): Promise<NotificationListResponse> {
    return apiRequest<NotificationListResponse>(`/notifications/me?limit=${limit}`);
  },

  async markRead(notificationId: string): Promise<{ status: string; read: boolean }> {
    return apiRequest<{ status: string; read: boolean }>(`/notifications/${notificationId}/read`, {
      method: "PATCH",
    });
  },

  async markAllRead(): Promise<{ status: string; marked_read_count: number }> {
    return apiRequest<{ status: string; marked_read_count: number }>("/notifications/mark-all-read", {
      method: "POST",
    });
  },
};
