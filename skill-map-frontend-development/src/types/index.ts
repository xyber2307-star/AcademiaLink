export type UserRole = "student" | "recruiter" | "faculty" | "institution" | "admin" | "mentor";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  verified: boolean;
}

export type SkillLevel = "Beginner" | "Intermediate" | "Advanced" | "Expert";
export type SkillCategory = "Technical" | "Soft" | "Domain" | "Tools";

export interface Skill {
  id: string;
  name: string;
  category: SkillCategory;
  score: number; // 0-100 current proficiency
  required: number; // 0-100 industry expected
  level: SkillLevel;
  verified: boolean;
  trend: number; // delta over last month
}

export interface SkillGap {
  skill: string;
  current: number;
  required: number;
  gap: number;
  priority: "High" | "Medium" | "Low";
  demand: number; // % of target roles requiring it
  recommendedCourse: string;
}

export interface LearningResource {
  id: string;
  title: string;
  provider: string;
  duration: string;
  level: SkillLevel;
  skill: string;
  progress: number;
  rating: number;
  type: "Course" | "Project" | "Workshop" | "Certification";
}

export type OpportunityType = "Internship" | "Full-time" | "Apprenticeship" | "Project";

export interface Opportunity {
  id: string;
  title: string;
  company: string;
  logo: string;
  location: string;
  type: OpportunityType;
  mode: "Remote" | "Hybrid" | "On-site";
  stipend: string;
  skills: string[];
  matchScore: number;
  postedAgo: string;
  deadline: string;
  applicants: number;
  description: string;
}

export type ApplicationStatus = "Applied" | "Shortlisted" | "Interview" | "Offered" | "Rejected";

export interface Application {
  id: string;
  opportunityId: string;
  role: string;
  company: string;
  appliedOn: string;
  status: ApplicationStatus;
  stage: number;
}

export interface MentorFeedback {
  id: string;
  mentor: string;
  mentorRole: string;
  avatar: string;
  date: string;
  rating: number;
  message: string;
  skill: string;
}

export interface StudentProfile {
  id: string;
  name: string;
  email: string;
  phone: string;
  avatar: string;
  institution: string;
  degree: string;
  branch: string;
  year: string;
  cgpa: number;
  rollNo: string;
  location: string;
  headline: string;
  about: string;
  profileCompletion: number;
  skillScore: number;
  careerReadiness: number;
  targetRole: string;
  links: { github: string; linkedin: string; portfolio: string };
  education: { degree: string; institution: string; year: string; score: string }[];
  projects: { title: string; description: string; tech: string[]; link: string }[];
  certifications: { name: string; issuer: string; year: string; verified: boolean }[];
  experience: { role: string; org: string; period: string; description: string }[];
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: "application" | "mentor" | "learning" | "system";
}
