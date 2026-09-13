import {
  Award, BarChart3, Bell, BookOpen, Briefcase, Building2, ClipboardList, FolderCheck, GitCompare, Home, Layers,
  LayoutDashboard, MessageSquare, Search, Settings, ShieldCheck, Target, User, UserCheck, Users, type LucideIcon,
} from "lucide-react";
import type { UserRole } from "../../types";

export interface NavItem { label: string; to: string; icon: LucideIcon; badge?: number }
export interface NavSection { title?: string; items: NavItem[] }

export const navByRole: Record<UserRole, NavSection[]> = {
  student: [
    { items: [{ label: "Dashboard", to: "/student", icon: Home }, { label: "My Profile", to: "/student/profile", icon: User }] },
    {
      title: "Skills",
      items: [
        { label: "Skill Assessment", to: "/student/assessment", icon: ClipboardList },
        { label: "Skill Profile", to: "/student/skills", icon: Award },
        { label: "Skill Gap Analysis", to: "/student/skill-gap", icon: GitCompare },
        { label: "Learning Path", to: "/student/learning", icon: BookOpen },
      ],
    },
    {
      title: "Career",
      items: [
        { label: "Market Intelligence", to: "/student/market-intelligence", icon: BarChart3 },
        { label: "AI Career Advisor", to: "/student/ai-assistant", icon: MessageSquare },
        { label: "Opportunities", to: "/student/opportunities", icon: Briefcase },
        { label: "Applications", to: "/student/applications", icon: Target },
        { label: "Mentors", to: "/student/mentors", icon: UserCheck },
        { label: "Portfolio", to: "/student/portfolio", icon: FolderCheck },
      ],
    },
    { title: "Account", items: [{ label: "Notifications", to: "/student/notifications", icon: Bell }, { label: "Settings", to: "/student/settings", icon: Settings }] },
  ],
  recruiter: [
    { items: [{ label: "Dashboard", to: "/recruiter", icon: LayoutDashboard }, { label: "My Profile", to: "/recruiter/profile", icon: User }, { label: "Company Profile", to: "/recruiter/company", icon: Building2 }] },
    { title: "Hiring", items: [{ label: "Post Opportunity", to: "/recruiter/post", icon: Briefcase }, { label: "Manage Opportunities", to: "/recruiter/opportunities", icon: Layers }, { label: "Candidate Search", to: "/recruiter/candidates", icon: Search }, { label: "Applications", to: "/recruiter/applications", icon: ClipboardList }] },
  ],
  faculty: [
    { items: [{ label: "Dashboard", to: "/faculty", icon: LayoutDashboard }, { label: "My Profile", to: "/faculty/profile", icon: User }, { label: "Students", to: "/faculty/students", icon: Users }] },
    { title: "Mentoring", items: [{ label: "Skill Gaps", to: "/faculty/skill-gaps", icon: GitCompare }, { label: "Evidence Verification", to: "/faculty/verification", icon: ShieldCheck }, { label: "Feedback", to: "/faculty/feedback", icon: MessageSquare }, { label: "Mentorship", to: "/faculty/mentorship", icon: UserCheck }] },
  ],
  institution: [
    { items: [{ label: "Dashboard", to: "/institution", icon: LayoutDashboard }, { label: "My Profile", to: "/institution/profile", icon: User }] },
    { title: "Analytics", items: [{ label: "Student Analytics", to: "/institution/students", icon: Users }, { label: "Skill Analytics", to: "/institution/skills", icon: Award }, { label: "Placement Analytics", to: "/institution/placements", icon: BarChart3 }, { label: "Industry Collaboration", to: "/institution/industry", icon: Building2 }] },
  ],
  admin: [
    { items: [{ label: "My Profile", to: "/admin/profile", icon: User }, { label: "Role Management", to: "/admin/roles", icon: Users }] },
    {
      title: "Management",
      items: [
        { label: "User Roles", to: "/admin/roles", icon: Users },
        { label: "Skill Taxonomy", to: "/admin/skills", icon: Award },
      ],
    },
  ],
  mentor: [{ items: [{ label: "Dashboard", to: "/student/mentors", icon: LayoutDashboard }] }],
};
