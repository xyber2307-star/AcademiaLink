import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthLayout } from "../layouts/AuthLayout";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { PageSkeleton } from "../components/ui/Skeleton";
import type { UserRole } from "../types";

const LandingPage = lazy(() => import("../pages/public/LandingPage"));
const LoginPage = lazy(() => import("../pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("../pages/auth/RegisterPage"));
const VerifyEmailPage = lazy(() => import("../pages/auth/VerifyEmailPage"));
const StudentDashboard = lazy(() => import("../pages/student/StudentDashboard"));
const StudentProfilePage = lazy(() => import("../pages/student/StudentProfilePage"));
const SkillGapPage = lazy(() => import("../pages/student/SkillGapPage"));
const SkillAssessmentPage = lazy(() => import("../pages/student/SkillAssessmentPage"));
const OpportunitiesPage = lazy(() => import("../pages/student/OpportunitiesPage"));
const OpportunityDetailsPage = lazy(() => import("../pages/student/OpportunityDetailsPage"));
const LearningPathPage = lazy(() => import("../pages/student/LearningPathPage"));
const PortfolioPage = lazy(() => import("../pages/student/PortfolioPage"));
const RecruiterDashboardPage = lazy(() => import("../pages/recruiter/RecruiterDashboardPage"));
const RecruiterCandidatesPage = lazy(() => import("../pages/recruiter/RecruiterCandidatesPage"));
const FacultyDashboardPage = lazy(() => import("../pages/faculty/FacultyDashboardPage"));
const FacultyStudentDetailPage = lazy(() => import("../pages/faculty/FacultyStudentDetailPage"));
const StudentMentorPage = lazy(() => import("../pages/student/StudentMentorPage"));
const InstitutionDashboardPage = lazy(() => import("../pages/institution/InstitutionDashboardPage"));
const StudentAIChatPage = lazy(() => import("../pages/student/StudentAIChatPage").then(m => ({ default: m.StudentAIChatPage })));
const MyApplicationsPage = lazy(() => import("../pages/student/MyApplicationsPage").then(m => ({ default: m.MyApplicationsPage })));
const NotificationsPage = lazy(() => import("../pages/NotificationsPage").then(m => ({ default: m.NotificationsPage })));
const RecruiterApplicationsPage = lazy(() => import("../pages/recruiter/RecruiterApplicationsPage").then(m => ({ default: m.RecruiterApplicationsPage })));
const AdminRolesPage = lazy(() => import("../pages/admin/AdminRolesPage").then(m => ({ default: m.AdminRolesPage })));
const AdminSkillsPage = lazy(() => import("../pages/admin/AdminSkillsPage").then(m => ({ default: m.AdminSkillsPage })));
const ProfilePage = lazy(() => import("../pages/common/ProfilePage"));
const JobMarketIntelligencePage = lazy(() => import("../pages/student/JobMarketIntelligencePage").then(m => ({ default: m.JobMarketIntelligencePage })));
const ComingSoonPage = lazy(() => import("../pages/ComingSoonPage"));
const NotFoundPage = lazy(() => import("../pages/NotFoundPage"));

const otherRoles: UserRole[] = ["admin"];

export function AppRoutes() {
  return (
    <Suspense fallback={<div className="p-8"><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<LandingPage />} />

        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Route>

        <Route path="/student" element={<DashboardLayout role="student" />}>
          <Route index element={<StudentDashboard />} />
          <Route path="profile" element={<StudentProfilePage />} />
          <Route path="skill-gap" element={<SkillGapPage />} />
          {/* Phase 2 — student modules */}
          <Route path="assessment" element={<SkillAssessmentPage />} />
          <Route path="skills" element={<ComingSoonPage title="Skill Profile" />} />
          <Route path="learning" element={<LearningPathPage />} />
          <Route path="opportunities" element={<OpportunitiesPage />} />
          <Route path="opportunities/:id" element={<OpportunityDetailsPage />} />
          <Route path="applications" element={<MyApplicationsPage />} />
          <Route path="market-intelligence" element={<JobMarketIntelligencePage />} />
          <Route path="ai-assistant" element={<StudentAIChatPage />} />
          <Route path="mentors" element={<StudentMentorPage />} />
          <Route path="portfolio" element={<PortfolioPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="settings" element={<ComingSoonPage title="Settings" />} />
        </Route>

        {/* Recruiter Experience */}
        <Route path="/recruiter" element={<DashboardLayout role="recruiter" />}>
          <Route index element={<RecruiterDashboardPage />} />
          <Route path="profile" element={<ProfilePage role="recruiter" />} />
          <Route path="opportunities" element={<RecruiterDashboardPage />} />
          <Route path="post" element={<RecruiterDashboardPage />} />
          <Route path="candidates" element={<RecruiterCandidatesPage />} />
          <Route path="jobs/:jobId/candidates" element={<RecruiterCandidatesPage />} />
          <Route path="applications" element={<RecruiterApplicationsPage />} />
          <Route path="jobs/:jobId/applications" element={<RecruiterApplicationsPage />} />
          <Route path="*" element={<ComingSoonPage title="Recruiter Module" />} />
        </Route>

        {/* Faculty / Mentor Experience */}
        <Route path="/faculty" element={<DashboardLayout role="faculty" />}>
          <Route index element={<FacultyDashboardPage />} />
          <Route path="profile" element={<ProfilePage role="faculty" />} />
          <Route path="students" element={<FacultyDashboardPage />} />
          <Route path="students/:studentId" element={<FacultyStudentDetailPage />} />
          <Route path="verification" element={<FacultyDashboardPage />} />
          <Route path="reviews" element={<FacultyDashboardPage />} />
          <Route path="feedback" element={<FacultyDashboardPage />} />
          <Route path="mentorship" element={<FacultyDashboardPage />} />
          <Route path="*" element={<ComingSoonPage title="Faculty Module" />} />
        </Route>

        {/* Institution Admin Analytics Experience */}
        <Route path="/institution" element={<DashboardLayout role="institution" />}>
          <Route index element={<InstitutionDashboardPage />} />
          <Route path="profile" element={<ProfilePage role="institution" />} />
          <Route path="students" element={<InstitutionDashboardPage activeTab="students" />} />
          <Route path="skills" element={<InstitutionDashboardPage activeTab="skills" />} />
          <Route path="placements" element={<InstitutionDashboardPage activeTab="recruitment" />} />
          <Route path="industry" element={<InstitutionDashboardPage activeTab="recruitment" />} />
          <Route path="*" element={<ComingSoonPage title="Institution Module" />} />
        </Route>

        {/* Administrator Role Management */}
        <Route path="/admin" element={<DashboardLayout role="admin" />}>
          <Route index element={<AdminRolesPage />} />
          <Route path="profile" element={<ProfilePage role="admin" />} />
          <Route path="roles" element={<AdminRolesPage />} />
          <Route path="skills" element={<AdminSkillsPage />} />
          <Route path="*" element={<AdminRolesPage />} />
        </Route>

        <Route path="/dashboard" element={<Navigate to="/student" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
