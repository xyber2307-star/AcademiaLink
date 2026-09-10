import React, { useState, useEffect } from "react";
import {
  Briefcase,
  Calendar,
  Building2,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowUpRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { applicationService, JobApplication, ApplicationStatus } from "../../services/applicationService";
import { Link } from "react-router-dom";

export const MyApplicationsPage: React.FC = () => {
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchApplications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await applicationService.getMyApplications();
      setApplications(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleWithdraw = async (applicationId: string) => {
    if (!window.confirm("Are you sure you want to withdraw this application?")) return;
    setActionLoading(applicationId);
    try {
      await applicationService.withdrawApplication(applicationId);
      await fetchApplications();
    } catch (err: any) {
      alert(`Could not withdraw application: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: ApplicationStatus) => {
    switch (status) {
      case "applied":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">Applied</span>;
      case "under_review":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700">Under Review</span>;
      case "shortlisted":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 font-bold">Shortlisted</span>;
      case "selected":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 font-bold">Selected</span>;
      case "rejected":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-700">Not Selected</span>;
      case "withdrawn":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">Withdrawn</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">{status}</span>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Applications</h1>
          <p className="text-sm text-gray-500 mt-1">
            Track real-time statuses, recruiter reviews, and match scores for your job applications.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchApplications}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-700 hover:bg-gray-50 rounded-xl text-sm font-medium transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            to="/student/jobs"
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition shadow-sm"
          >
            <Briefcase className="w-4 h-4" />
            Browse Opportunities
          </Link>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="py-20 text-center space-y-3 bg-white rounded-2xl border border-gray-100">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-gray-500">Loading your applications...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && applications.length === 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center space-y-4">
          <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto">
            <Briefcase className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-bold text-gray-900">No applications submitted yet</h3>
            <p className="text-sm text-gray-500 mt-1">
              Explore open internships and full-time postings matched against your skills to submit your first application.
            </p>
          </div>
          <Link
            to="/student/jobs"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition shadow-sm"
          >
            Explore Jobs
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Applications List */}
      {!loading && !error && applications.length > 0 && (
        <div className="space-y-4">
          {applications.map((app) => (
            <div
              key={app.application_id}
              className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-bold text-gray-900">{app.job_title}</h3>
                    {getStatusBadge(app.status)}
                  </div>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 mt-1.5">
                    <span className="flex items-center gap-1">
                      <Building2 className="w-3.5 h-3.5 text-gray-400" />
                      {app.company}
                    </span>
                    {app.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-gray-400" />
                        {app.location}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-gray-400" />
                      Applied: {new Date(app.applied_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {app.match_score !== undefined && (
                  <div className="text-right">
                    <span className="text-xs text-gray-400 block">Match Score</span>
                    <span className="text-xl font-extrabold text-indigo-600">
                      {Math.round(app.match_score)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Feedback or Notes */}
              {app.feedback && (
                <div className="p-3.5 bg-indigo-50/60 border border-indigo-100 rounded-xl text-xs text-indigo-900">
                  <span className="font-semibold block mb-0.5">Recruiter Feedback:</span>
                  {app.feedback}
                </div>
              )}

              {/* Provenance and Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-gray-100 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                  Source: Applications Registry (Verified)
                </span>

                {app.status !== "withdrawn" && app.status !== "rejected" && app.status !== "selected" && (
                  <button
                    disabled={actionLoading === app.application_id}
                    onClick={() => handleWithdraw(app.application_id)}
                    className="text-rose-600 hover:text-rose-700 font-medium transition disabled:opacity-50"
                  >
                    {actionLoading === app.application_id ? "Withdrawing..." : "Withdraw Application"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
