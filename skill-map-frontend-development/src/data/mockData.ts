/**
 * MOCK DATA — for UI development only.
 * All access to this data goes through `src/services/*`. Swap the service
 * implementations for real API calls when the backend is ready.
 */
import type {
  Application,
  LearningResource,
  MentorFeedback,
  Notification,
  Opportunity,
  Skill,
  SkillGap,
  StudentProfile,
} from "../types";

export const mockStudent: StudentProfile = {
  id: "stu_001",
  name: "Ananya Sharma",
  email: "ananya.sharma@nitk.edu.in",
  phone: "+91 98765 43210",
  avatar: "https://i.pravatar.cc/150?img=47",
  institution: "National Institute of Technology, Karnataka",
  degree: "B.Tech",
  branch: "Computer Science & Engineering",
  year: "3rd Year",
  cgpa: 8.72,
  rollNo: "211CS142",
  location: "Mangaluru, Karnataka",
  headline: "Aspiring Full-Stack Developer | ML Enthusiast",
  about:
    "Third-year CSE student passionate about building scalable web applications and exploring machine learning. Actively looking for a summer internship in product-based companies.",
  profileCompletion: 82,
  skillScore: 74,
  careerReadiness: 68,
  targetRole: "Full-Stack Developer",
  links: {
    github: "github.com/ananyasharma",
    linkedin: "linkedin.com/in/ananya-sharma",
    portfolio: "ananya.dev",
  },
  education: [
    { degree: "B.Tech, Computer Science", institution: "NIT Karnataka", year: "2021 – 2025", score: "CGPA 8.72" },
    { degree: "Class XII (CBSE)", institution: "DPS Bengaluru", year: "2021", score: "94.2%" },
  ],
  projects: [
    {
      title: "CampusConnect",
      description: "A MERN-stack campus event management platform with role-based access and real-time notifications.",
      tech: ["React", "Node.js", "MongoDB", "Socket.io"],
      link: "#",
    },
    {
      title: "SkillSense ML",
      description: "Resume-to-skill extraction pipeline using spaCy and a fine-tuned BERT classifier.",
      tech: ["Python", "spaCy", "PyTorch", "FastAPI"],
      link: "#",
    },
    {
      title: "FinTrack",
      description: "Personal finance dashboard with expense analytics built using Next.js and PostgreSQL.",
      tech: ["Next.js", "PostgreSQL", "Prisma", "Tailwind"],
      link: "#",
    },
  ],
  certifications: [
    { name: "AWS Cloud Practitioner", issuer: "Amazon Web Services", year: "2024", verified: true },
    { name: "Meta Front-End Developer", issuer: "Coursera", year: "2023", verified: true },
    { name: "Machine Learning Specialization", issuer: "DeepLearning.AI", year: "2024", verified: false },
  ],
  experience: [
    {
      role: "Web Development Intern",
      org: "Zerodha Tech",
      period: "May 2024 – Jul 2024",
      description: "Built internal dashboard components in React, improving load time by 30%.",
    },
    {
      role: "Technical Lead",
      org: "Google DSC – NITK",
      period: "Aug 2023 – Present",
      description: "Lead a 25-member team organising hackathons and workshops on web technologies.",
    },
  ],
};

export const mockSkills: Skill[] = [
  { id: "s1", name: "React", category: "Technical", score: 86, required: 80, level: "Advanced", verified: true, trend: 6 },
  { id: "s2", name: "JavaScript", category: "Technical", score: 88, required: 85, level: "Advanced", verified: true, trend: 3 },
  { id: "s3", name: "TypeScript", category: "Technical", score: 62, required: 80, level: "Intermediate", verified: false, trend: 9 },
  { id: "s4", name: "Node.js", category: "Technical", score: 70, required: 80, level: "Intermediate", verified: true, trend: 4 },
  { id: "s5", name: "System Design", category: "Domain", score: 42, required: 75, level: "Beginner", verified: false, trend: 5 },
  { id: "s6", name: "SQL & Databases", category: "Technical", score: 74, required: 78, level: "Intermediate", verified: true, trend: 2 },
  { id: "s7", name: "Data Structures", category: "Domain", score: 80, required: 85, level: "Advanced", verified: true, trend: 1 },
  { id: "s8", name: "Cloud (AWS)", category: "Tools", score: 48, required: 70, level: "Beginner", verified: true, trend: 8 },
  { id: "s9", name: "Docker & CI/CD", category: "Tools", score: 38, required: 70, level: "Beginner", verified: false, trend: 3 },
  { id: "s10", name: "Git", category: "Tools", score: 90, required: 75, level: "Expert", verified: true, trend: 0 },
  { id: "s11", name: "Communication", category: "Soft", score: 78, required: 80, level: "Advanced", verified: false, trend: 2 },
  { id: "s12", name: "Problem Solving", category: "Soft", score: 82, required: 85, level: "Advanced", verified: true, trend: 3 },
  { id: "s13", name: "Teamwork", category: "Soft", score: 85, required: 75, level: "Advanced", verified: false, trend: 1 },
  { id: "s14", name: "Testing (Jest)", category: "Technical", score: 45, required: 70, level: "Beginner", verified: false, trend: 6 },
];

export const mockSkillGaps: SkillGap[] = [
  { skill: "System Design", current: 42, required: 75, gap: 33, priority: "High", demand: 82, recommendedCourse: "Grokking System Design" },
  { skill: "Docker & CI/CD", current: 38, required: 70, gap: 32, priority: "High", demand: 71, recommendedCourse: "DevOps Bootcamp" },
  { skill: "Testing (Jest)", current: 45, required: 70, gap: 25, priority: "Medium", demand: 64, recommendedCourse: "Testing JavaScript" },
  { skill: "Cloud (AWS)", current: 48, required: 70, gap: 22, priority: "Medium", demand: 76, recommendedCourse: "AWS Solutions Architect" },
  { skill: "TypeScript", current: 62, required: 80, gap: 18, priority: "Medium", demand: 88, recommendedCourse: "Total TypeScript" },
  { skill: "Node.js", current: 70, required: 80, gap: 10, priority: "Low", demand: 79, recommendedCourse: "Node.js Advanced Concepts" },
  { skill: "Data Structures", current: 80, required: 85, gap: 5, priority: "Low", demand: 92, recommendedCourse: "DSA Masterclass" },
  { skill: "SQL & Databases", current: 74, required: 78, gap: 4, priority: "Low", demand: 74, recommendedCourse: "SQL for Developers" },
];

export const mockLearning: LearningResource[] = [
  { id: "l1", title: "Grokking the System Design Interview", provider: "Educative", duration: "24 hrs", level: "Intermediate", skill: "System Design", progress: 35, rating: 4.8, type: "Course" },
  { id: "l2", title: "Docker & Kubernetes: The Complete Guide", provider: "Udemy", duration: "22 hrs", level: "Beginner", skill: "Docker & CI/CD", progress: 0, rating: 4.7, type: "Course" },
  { id: "l3", title: "Total TypeScript", provider: "Matt Pocock", duration: "18 hrs", level: "Intermediate", skill: "TypeScript", progress: 60, rating: 4.9, type: "Course" },
  { id: "l4", title: "Build a CI/CD Pipeline Project", provider: "SKILL MAP Labs", duration: "8 hrs", level: "Intermediate", skill: "Docker & CI/CD", progress: 0, rating: 4.6, type: "Project" },
  { id: "l5", title: "AWS Certified Solutions Architect", provider: "AWS Training", duration: "40 hrs", level: "Intermediate", skill: "Cloud (AWS)", progress: 12, rating: 4.7, type: "Certification" },
  { id: "l6", title: "Testing JavaScript with Jest & RTL", provider: "Kent C. Dodds", duration: "10 hrs", level: "Beginner", skill: "Testing (Jest)", progress: 0, rating: 4.8, type: "Course" },
];

export const mockOpportunities: Opportunity[] = [
  {
    id: "o1", title: "Frontend Engineering Intern", company: "Razorpay", logo: "RZ", location: "Bengaluru", type: "Internship", mode: "Hybrid",
    stipend: "₹50,000/mo", skills: ["React", "TypeScript", "JavaScript"], matchScore: 91, postedAgo: "2 days ago", deadline: "30 Jun 2025", applicants: 214,
    description: "Work with the Payments UI team to build and ship high-impact merchant dashboard features.",
  },
  {
    id: "o2", title: "Full-Stack Developer Intern", company: "Zoho", logo: "ZO", location: "Chennai", type: "Internship", mode: "On-site",
    stipend: "₹35,000/mo", skills: ["Node.js", "React", "SQL & Databases"], matchScore: 84, postedAgo: "5 days ago", deadline: "15 Jul 2025", applicants: 388,
    description: "Contribute to Zoho CRM modules across the stack with mentorship from senior engineers.",
  },
  {
    id: "o3", title: "Software Engineer (New Grad)", company: "Infosys", logo: "IN", location: "Pune", type: "Full-time", mode: "On-site",
    stipend: "₹9.5 LPA", skills: ["Data Structures", "Java", "SQL & Databases"], matchScore: 78, postedAgo: "1 week ago", deadline: "20 Jul 2025", applicants: 1250,
    description: "Join the Digital Experience practice building enterprise-grade applications.",
  },
  {
    id: "o4", title: "Cloud Engineering Apprentice", company: "Amazon", logo: "AM", location: "Hyderabad", type: "Apprenticeship", mode: "Hybrid",
    stipend: "₹45,000/mo", skills: ["Cloud (AWS)", "Docker & CI/CD", "Node.js"], matchScore: 66, postedAgo: "3 days ago", deadline: "10 Jul 2025", applicants: 540,
    description: "12-month structured apprenticeship in AWS infrastructure and DevOps practices.",
  },
  {
    id: "o5", title: "ML Research Intern", company: "TCS Research", logo: "TC", location: "Remote", type: "Internship", mode: "Remote",
    stipend: "₹30,000/mo", skills: ["Python", "Machine Learning", "Data Structures"], matchScore: 72, postedAgo: "4 days ago", deadline: "05 Jul 2025", applicants: 176,
    description: "Research NLP pipelines for enterprise document understanding.",
  },
];

export const mockApplications: Application[] = [
  { id: "a1", opportunityId: "o1", role: "Frontend Engineering Intern", company: "Razorpay", appliedOn: "12 Jun 2025", status: "Interview", stage: 3 },
  { id: "a2", opportunityId: "o2", role: "Full-Stack Developer Intern", company: "Zoho", appliedOn: "08 Jun 2025", status: "Shortlisted", stage: 2 },
  { id: "a3", opportunityId: "o5", role: "ML Research Intern", company: "TCS Research", appliedOn: "02 Jun 2025", status: "Applied", stage: 1 },
  { id: "a4", opportunityId: "o3", role: "SDE Intern", company: "Flipkart", appliedOn: "20 May 2025", status: "Offered", stage: 4 },
  { id: "a5", opportunityId: "o4", role: "Backend Intern", company: "Swiggy", appliedOn: "15 May 2025", status: "Rejected", stage: 2 },
  { id: "a6", opportunityId: "o1", role: "Web Dev Intern", company: "Freshworks", appliedOn: "10 May 2025", status: "Applied", stage: 1 },
];

export const mockFeedback: MentorFeedback[] = [
  {
    id: "f1", mentor: "Rahul Verma", mentorRole: "Senior Engineer, Razorpay", avatar: "https://i.pravatar.cc/100?img=12", date: "2 days ago", rating: 4,
    message: "Strong React fundamentals. Focus next on component architecture at scale and TypeScript generics.", skill: "React",
  },
  {
    id: "f2", mentor: "Dr. Priya Nair", mentorRole: "Faculty Mentor, NITK", avatar: "https://i.pravatar.cc/100?img=32", date: "1 week ago", rating: 5,
    message: "Excellent project documentation for CampusConnect. Consider adding unit tests to strengthen your evidence portfolio.", skill: "Testing (Jest)",
  },
  {
    id: "f3", mentor: "Karthik Iyer", mentorRole: "DevOps Lead, Zoho", avatar: "https://i.pravatar.cc/100?img=59", date: "2 weeks ago", rating: 3,
    message: "Good start with Docker basics. Practice multi-stage builds and set up a GitHub Actions pipeline for a real project.", skill: "Docker & CI/CD",
  },
];

export const mockNotifications: Notification[] = [
  { id: "n1", title: "Interview scheduled", message: "Razorpay has scheduled your technical interview for 18 Jun, 11:00 AM.", time: "1h ago", read: false, type: "application" },
  { id: "n2", title: "New mentor feedback", message: "Rahul Verma left feedback on your React assessment.", time: "2d ago", read: false, type: "mentor" },
  { id: "n3", title: "Course reminder", message: "You are 60% through Total TypeScript. Keep the streak going!", time: "3d ago", read: true, type: "learning" },
  { id: "n4", title: "Profile verified", message: "Your AWS Cloud Practitioner certificate has been verified by faculty.", time: "5d ago", read: true, type: "system" },
];

export const mockReadinessTrend = [
  { month: "Jan", readiness: 42, skillScore: 51 },
  { month: "Feb", readiness: 47, skillScore: 55 },
  { month: "Mar", readiness: 53, skillScore: 60 },
  { month: "Apr", readiness: 58, skillScore: 65 },
  { month: "May", readiness: 63, skillScore: 70 },
  { month: "Jun", readiness: 68, skillScore: 74 },
];

export const mockReadinessBreakdown = [
  { name: "Technical Skills", value: 74 },
  { name: "Projects & Evidence", value: 70 },
  { name: "Soft Skills", value: 81 },
  { name: "Certifications", value: 60 },
  { name: "Industry Exposure", value: 55 },
];
