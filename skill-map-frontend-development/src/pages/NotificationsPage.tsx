import React, { useState, useEffect } from "react";
import {
  Bell,
  CheckCircle2,
  Clock,
  Briefcase,
  Award,
  BookOpen,
  MessageSquare,
  CheckCheck,
  RefreshCw,
} from "lucide-react";
import { notificationService, NotificationItem } from "../services/notificationService";

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterUnread, setFilterUnread] = useState(false);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationService.getMyNotifications();
      setNotifications(res.notifications || []);
      setUnreadCount(res.unread_count || 0);
    } catch (err) {
      console.warn("Could not load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await notificationService.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.warn("Failed to mark read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.warn("Failed to mark all read:", err);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "application_status_changed":
        return <Briefcase className="w-5 h-5 text-blue-500" />;
      case "evidence_reviewed":
        return <Award className="w-5 h-5 text-emerald-500" />;
      case "mentor_feedback":
        return <MessageSquare className="w-5 h-5 text-purple-500" />;
      case "assessment_completed":
        return <CheckCircle2 className="w-5 h-5 text-amber-500" />;
      case "learning_path_created":
        return <BookOpen className="w-5 h-5 text-indigo-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  const displayed = filterUnread ? notifications.filter((n) => !n.read) : notifications;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Bell className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900">Notifications & Activity</h1>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-600 text-white">
                  {unreadCount} new
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">Real-time alerts for applications, mentorship, and evidence.</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
            >
              <CheckCheck className="w-4 h-4" />
              Mark all read
            </button>
          )}
          <button
            onClick={() => setFilterUnread(!filterUnread)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition ${
              filterUnread
                ? "bg-indigo-600 text-white border-indigo-600"
                : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
            }`}
          >
            {filterUnread ? "Show All" : "Unread Only"}
          </button>
          <button
            onClick={fetchNotifications}
            className="p-2 border border-gray-200 text-gray-500 hover:bg-gray-50 rounded-lg transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="py-16 text-center space-y-3 bg-white rounded-2xl border border-gray-100">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-gray-500">Loading notifications...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && displayed.length === 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-gray-50 text-gray-400 rounded-full flex items-center justify-center mx-auto">
            <Bell className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-gray-900">
            {filterUnread ? "No unread notifications" : "No notifications yet"}
          </h3>
          <p className="text-sm text-gray-500 max-w-sm mx-auto">
            Activity updates will appear here when mentors review your portfolio or application statuses change.
          </p>
        </div>
      )}

      {/* List */}
      {!loading && displayed.length > 0 && (
        <div className="space-y-3">
          {displayed.map((n) => (
            <div
              key={n.notification_id}
              onClick={() => !n.read && handleMarkRead(n.notification_id)}
              className={`p-4 rounded-2xl border transition flex items-start gap-4 cursor-pointer ${
                n.read
                  ? "bg-white border-gray-100 text-gray-700"
                  : "bg-indigo-50/40 border-indigo-100 text-gray-900 font-medium shadow-sm"
              }`}
            >
              <div className="p-2.5 rounded-xl bg-white border border-gray-100 shadow-sm flex-shrink-0 mt-0.5">
                {getIcon(n.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold truncate">{n.title}</h4>
                  <span className="text-[11px] text-gray-400 flex-shrink-0">
                    {new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1 leading-relaxed">{n.message}</p>
              </div>
              {!n.read && (
                <div className="w-2.5 h-2.5 rounded-full bg-indigo-600 flex-shrink-0 mt-2"></div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
