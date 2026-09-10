import React, { useState, useEffect } from "react";
import {
  Users,
  Briefcase,
  Search,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Send,
  Building2,
  RefreshCw,
} from "lucide-react";
import { applicationService, JobApplication, ApplicationStatus } from "../../services/applicationService";
import { recruiterService, RecruiterJob } from "../../services/recruiterService";

export const RecruiterApplicationsPage: React.FC = () => {
  const [jobs, setJobs] = useState<RecruiterJob[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [appsLoading, setAppsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [feedbackInput, setFeedbackInput] = useState<Record<string, string>>({});

  useEffect(() => {
    // Load recruiter's jobs
    setLoading(true);
    recruiterService
      .getMyJobs()
      .then((data) => {
        setJobs(data || []);
        if (data && data.length > 0) {
          const firstJobId = data[0].job_id || data[0].id || "";
          setSelectedJobId(firstJobId);
        }
      })
      .catch((err) => setError(err.message || "Failed to load recruiter jobs."))
      .finally(() => setLoading(false));
  }, []);

  const fetchJobApplications = async (jobId: string) => {
    if (!jobId) return;
    setAppsLoading(true);
    setError(null);
    try {
      const data = await applicationService.getApplicationsForJob(jobId);
      setApplications(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load applications for selected job.");
    } finally {
      setAppsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedJobId) {
      fetchJobApplications(selectedJobId);
    }
  }, [selectedJobId]);

  const handleStatusUpdate = async (appId: string, newStatus: ApplicationStatus) => {
    setUpdatingId(appId);
    try {
      const fb = feedbackInput[appId] || "";
      const updated = await applicationService.updateApplicationStatus(appId, newStatus, fb);
      setApplications((prev) => prev.map((a) => (a.application_id === appId ? updated : a)));
    } catch (err: any) {
      alert(`Could not update candidate status: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Candidate Applications</h1>
            <p className="text-sm text-gray-500">
              Review candidate applications and update statuses for your posted opportunities.
            </p>
          </div>
        </div>

        {/* Job selector */}
        {jobs.length > 0 && (
          <div className="flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-gray-400" />
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="text-sm font-medium border border-gray-200 rounded-xl px-4 py-2 bg-gray-50 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {jobs.map((j) => {
                const jid = j.job_id || j.id || "";
                return (
                  <option key={jid} value={jid}>
                    {j.title} ({j.status})
                  </option>
                );
              })}
            </select>
            <button
              onClick={() => fetchJobApplications(selectedJobId)}
              className="p-2 border border-gray-200 rounded-xl text-gray-500 hover:bg-gray-50 transition"
            >
              <RefreshCw className={`w-4 h-4 ${appsLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="py-20 text-center space-y-3 bg-white rounded-2xl border border-gray-100">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-gray-500">Loading recruiter jobs...</p>
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center space-y-3">
          <Briefcase className="w-12 h-12 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-gray-900">No Jobs Posted</h3>
          <p className="text-sm text-gray-500">Post a job vacancy first to receive candidate applications.</p>
        </div>
      )}

      {!loading && selectedJobId && !appsLoading && applications.length === 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center space-y-3">
          <Users className="w-12 h-12 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-gray-900">No applications received yet</h3>
          <p className="text-sm text-gray-500">When students apply for this posting, their profiles and match scores will appear here.</p>
        </div>
      )}

      {!loading && applications.length > 0 && (
        <div className="space-y-4">
          {applications.map((app) => (
            <div
              key={app.application_id}
              className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-base font-bold text-gray-900">{app.student_name || "Applicant"}</h3>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 uppercase">
                      {app.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Email: {app.student_email || "Not disclosed"} • Applied: {new Date(app.applied_at).toLocaleDateString()}
                  </div>
                </div>

                {app.match_score !== undefined && (
                  <div className="text-right">
                    <span className="text-xs text-gray-400 block">Candidate Match</span>
                    <span className="text-xl font-black text-blue-600">{Math.round(app.match_score)}%</span>
                  </div>
                )}
              </div>

              {app.notes && (
                <div className="p-3 bg-gray-50 rounded-xl text-xs text-gray-600">
                  <span className="font-semibold block mb-0.5">Applicant Note:</span>
                  {app.notes}
                </div>
              )}

              {/* Status Action & Feedback Bar */}
              <div className="pt-3 border-t border-gray-100 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                <div className="flex-1 flex gap-2">
                  <input
                    type="text"
                    placeholder="Feedback or interview invitation notes..."
                    value={feedbackInput[app.application_id] || ""}
                    onChange={(e) =>
                      setFeedbackInput((prev) => ({ ...prev, [app.application_id]: e.target.value }))
                    }
                    className="flex-1 text-xs border border-gray-200 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-xs text-gray-500 font-medium">Update Status:</span>
                  <select
                    disabled={updatingId === app.application_id}
                    value={app.status}
                    onChange={(e) =>
                      handleStatusUpdate(app.application_id, e.target.value as ApplicationStatus)
                    }
                    className="text-xs font-semibold border border-gray-200 rounded-xl px-3 py-1.5 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 cursor-pointer"
                  >
                    <option value="applied">Applied</option>
                    <option value="under_review">Under Review</option>
                    <option value="shortlisted">Shortlist Candidate</option>
                    <option value="selected">Select / Offer</option>
                    <option value="rejected">Reject</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
