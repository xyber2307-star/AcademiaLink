"""
AcademiaLINK Demo Data Seeder
Populates Cloud Firestore with realistic demo data for SIH evaluation:
- 3 Students (Ananya Sharma, Rahul Verma, Priya Patel) with full profiles and skills
- 2 Companies (Razorpay, Zoho Corporation)
- 4 Jobs/Internships with minimumProficiency ratings
- 10 Global Technical Skills
- 3 Curriculum Courses mapped to industry skills
"""

import os
import sys
from datetime import datetime, timezone

# Ensure app package is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.firebase import get_db, initialize_firebase

DEMO_STUDENTS = [
    {
        "uid": "demo_student_ananya",
        "name": "Ananya Sharma (DEMO)",
        "email": "ananya.sharma@nitk.edu.in",
        "role": "student",
        "phone": "+91 98765 43210",
        "avatar": "https://i.pravatar.cc/150?img=47",
        "institution": "National Institute of Technology, Karnataka",
        "degree": "B.Tech",
        "branch": "Computer Science & Engineering",
        "year": "3rd Year",
        "cgpa": 8.72,
        "rollNo": "211CS142",
        "location": "Mangaluru, Karnataka",
        "headline": "Aspiring Full-Stack Developer | Cloud & ML Enthusiast",
        "about": "Third-year CSE student passionate about building scalable web applications and exploring machine learning. Actively seeking summer 2025 internships.",
        "profileCompletion": 82,
        "skillScore": 74,
        "careerReadiness": 68,
        "targetRole": "Full-Stack Developer",
        "links": {
            "github": "github.com/ananyasharma",
            "linkedin": "linkedin.com/in/ananya-sharma",
            "portfolio": "ananya.dev",
        },
        "education": [
            {"degree": "B.Tech, Computer Science", "institution": "NIT Karnataka", "year": "2021 – 2025", "score": "CGPA 8.72"},
            {"degree": "Class XII (CBSE)", "institution": "DPS Bengaluru", "year": "2021", "score": "94.2%"},
        ],
        "projects": [
            {
                "title": "CampusConnect",
                "description": "A MERN-stack campus event management platform with role-based access and real-time notifications.",
                "tech": ["React", "Node.js", "MongoDB", "Socket.io"],
                "link": "https://github.com/example/campusconnect",
            },
            {
                "title": "SkillSense ML",
                "description": "Resume-to-skill extraction pipeline using spaCy and a fine-tuned BERT classifier.",
                "tech": ["Python", "spaCy", "PyTorch", "FastAPI"],
                "link": "https://github.com/example/skillsense",
            },
        ],
        "certifications": [
            {"name": "AWS Cloud Practitioner", "issuer": "Amazon Web Services", "year": "2024", "verified": True},
            {"name": "Meta Front-End Developer", "issuer": "Coursera", "year": "2023", "verified": True},
        ],
        "skills": [
            {"name": "React", "proficiency": 86, "category": "Technical", "level": "Advanced", "verified": True, "trend": 6},
            {"name": "JavaScript", "proficiency": 88, "category": "Technical", "level": "Advanced", "verified": True, "trend": 3},
            {"name": "TypeScript", "proficiency": 62, "category": "Technical", "level": "Intermediate", "verified": False, "trend": 9},
            {"name": "Node.js", "proficiency": 70, "category": "Technical", "level": "Intermediate", "verified": True, "trend": 4},
            {"name": "Python", "proficiency": 80, "category": "Technical", "level": "Advanced", "verified": True, "trend": 5},
            {"name": "SQL & Databases", "proficiency": 74, "category": "Technical", "level": "Intermediate", "verified": True, "trend": 2},
            {"name": "Data Structures", "proficiency": 80, "category": "Domain", "level": "Advanced", "verified": True, "trend": 1},
            {"name": "System Design", "proficiency": 42, "category": "Domain", "level": "Beginner", "verified": False, "trend": 5},
            {"name": "Docker & CI/CD", "proficiency": 38, "category": "Tools", "level": "Beginner", "verified": False, "trend": 3},
            {"name": "Cloud (AWS)", "proficiency": 48, "category": "Tools", "level": "Beginner", "verified": True, "trend": 8},
            {"name": "Git", "proficiency": 90, "category": "Tools", "level": "Expert", "verified": True, "trend": 0},
        ],
    },
    {
        "uid": "demo_student_rohit",
        "name": "Rohit Nair (DEMO)",
        "email": "rohit.nair@iitb.ac.in",
        "role": "student",
        "phone": "+91 91234 56789",
        "avatar": "https://i.pravatar.cc/150?img=11",
        "institution": "IIT Bombay",
        "degree": "B.Tech",
        "branch": "Electrical Engineering",
        "year": "Final Year",
        "cgpa": 9.10,
        "rollNo": "200040082",
        "location": "Mumbai, Maharashtra",
        "headline": "Backend & Cloud Systems Engineer",
        "about": "Passionate backend engineer with extensive experience in distributed systems, Go, Python, and AWS infrastructure.",
        "profileCompletion": 90,
        "skillScore": 84,
        "careerReadiness": 88,
        "targetRole": "Backend Engineer",
        "links": {"github": "github.com/rohitnair", "linkedin": "linkedin.com/in/rohitnair", "portfolio": ""},
        "education": [{"degree": "B.Tech, EE", "institution": "IIT Bombay", "year": "2021 – 2025", "score": "CGPA 9.10"}],
        "projects": [{"title": "High-Throughput Gateway", "description": "Distributed API Gateway in Go handling 50k req/sec.", "tech": ["Go", "Redis", "Docker"], "link": "#"}],
        "certifications": [{"name": "AWS Certified Solutions Architect", "issuer": "AWS", "year": "2024", "verified": True}],
        "skills": [
            {"name": "Python", "proficiency": 90, "category": "Technical", "level": "Expert", "verified": True, "trend": 4},
            {"name": "Node.js", "proficiency": 80, "category": "Technical", "level": "Advanced", "verified": True, "trend": 2},
            {"name": "SQL & Databases", "proficiency": 85, "category": "Technical", "level": "Advanced", "verified": True, "trend": 5},
            {"name": "Docker & CI/CD", "proficiency": 82, "category": "Tools", "level": "Advanced", "verified": True, "trend": 7},
            {"name": "System Design", "proficiency": 78, "category": "Domain", "level": "Advanced", "verified": True, "trend": 6},
            {"name": "Cloud (AWS)", "proficiency": 85, "category": "Tools", "level": "Advanced", "verified": True, "trend": 8},
        ],
    },
    {
        "uid": "demo_student_tanvi",
        "name": "Tanvi Gupta (DEMO)",
        "email": "tanvi.gupta@iiitd.ac.in",
        "role": "student",
        "phone": "+91 98450 12345",
        "avatar": "https://i.pravatar.cc/150?img=33",
        "institution": "IIIT Delhi",
        "degree": "B.Tech",
        "branch": "Computer Science & Artificial Intelligence",
        "year": "3rd Year",
        "cgpa": 8.95,
        "rollNo": "2022015",
        "location": "New Delhi",
        "headline": "Data Science & Machine Learning Enthusiast",
        "about": "Aspiring data scientist focused on LLMs, computer vision, and statistical analysis.",
        "profileCompletion": 78,
        "skillScore": 79,
        "careerReadiness": 75,
        "targetRole": "Data Scientist",
        "links": {"github": "github.com/tanvigupta", "linkedin": "linkedin.com/in/tanvigupta", "portfolio": ""},
        "education": [{"degree": "B.Tech, CSAI", "institution": "IIIT Delhi", "year": "2022 – 2026", "score": "CGPA 8.95"}],
        "projects": [{"title": "Multilingual Medical Chatbot", "description": "Fine-tuned LLaMA 3 for healthcare consultations.", "tech": ["PyTorch", "HuggingFace", "Python"], "link": "#"}],
        "certifications": [{"name": "TensorFlow Developer", "issuer": "Google", "year": "2024", "verified": True}],
        "skills": [
            {"name": "Python", "proficiency": 92, "category": "Technical", "level": "Expert", "verified": True, "trend": 5},
            {"name": "Machine Learning", "proficiency": 85, "category": "Technical", "level": "Advanced", "verified": True, "trend": 8},
            {"name": "SQL & Databases", "proficiency": 76, "category": "Technical", "level": "Intermediate", "verified": True, "trend": 3},
            {"name": "Data Structures", "proficiency": 82, "category": "Domain", "level": "Advanced", "verified": True, "trend": 2},
        ],
    },
]

DEMO_COMPANIES = [
    {"id": "comp_razorpay", "name": "Razorpay", "industry": "Fintech & Payments", "location": "Bengaluru, Karnataka"},
    {"id": "comp_zoho", "name": "Zoho Corporation", "industry": "SaaS & Enterprise", "location": "Chennai, Tamil Nadu"},
]

DEMO_JOBS = [
    {
        "id": "job_razorpay_fe",
        "title": "Frontend Engineering Intern (DEMO)",
        "company": "Razorpay",
        "logo": "RZ",
        "location": "Bengaluru",
        "workMode": "Hybrid",
        "type": "Internship",
        "stipend": "₹50,000/mo",
        "deadline": "30 Jun 2025",
        "description": "Work with the Payments UI team to build and ship high-impact merchant dashboard features with React, TypeScript, and modern component systems.",
        "requiredSkills": [
            {"name": "React", "minimumProficiency": 80},
            {"name": "JavaScript", "minimumProficiency": 85},
            {"name": "TypeScript", "minimumProficiency": 80},
        ],
        "preferredSkills": ["Testing (Jest)", "Git"],
        "createdBy": "recruiter_razorpay",
        "applicants": 214,
    },
    {
        "id": "job_zoho_fs",
        "title": "Full-Stack Developer Intern (DEMO)",
        "company": "Zoho",
        "logo": "ZO",
        "location": "Chennai",
        "workMode": "On-site",
        "type": "Internship",
        "stipend": "₹35,000/mo",
        "deadline": "15 Jul 2025",
        "description": "Contribute to Zoho CRM modules across the stack with mentorship from senior engineers. Work with Node.js, React, and high-performance SQL databases.",
        "requiredSkills": [
            {"name": "Node.js", "minimumProficiency": 75},
            {"name": "React", "minimumProficiency": 75},
            {"name": "SQL & Databases", "minimumProficiency": 75},
        ],
        "preferredSkills": ["System Design", "Docker & CI/CD"],
        "createdBy": "recruiter_zoho",
        "applicants": 388,
    },
    {
        "id": "job_amazon_cloud",
        "title": "Cloud Engineering Apprentice (DEMO)",
        "company": "Amazon",
        "logo": "AM",
        "location": "Hyderabad",
        "workMode": "Hybrid",
        "type": "Apprenticeship",
        "stipend": "₹45,000/mo",
        "deadline": "10 Jul 2025",
        "description": "12-month structured apprenticeship in AWS infrastructure, container orchestration with Docker & Kubernetes, and automated CI/CD pipelines.",
        "requiredSkills": [
            {"name": "Cloud (AWS)", "minimumProficiency": 70},
            {"name": "Docker & CI/CD", "minimumProficiency": 70},
            {"name": "Node.js", "minimumProficiency": 70},
        ],
        "preferredSkills": ["Git", "Linux"],
        "createdBy": "recruiter_amazon",
        "applicants": 540,
    },
    {
        "id": "job_tcs_ml",
        "title": "ML Research Intern (DEMO)",
        "company": "TCS Research",
        "logo": "TC",
        "location": "Remote",
        "workMode": "Remote",
        "type": "Internship",
        "stipend": "₹30,000/mo",
        "deadline": "05 Jul 2025",
        "description": "Research NLP pipelines for enterprise document understanding and graph-based knowledge representations using Python and PyTorch.",
        "requiredSkills": [
            {"name": "Python", "minimumProficiency": 80},
            {"name": "Machine Learning", "minimumProficiency": 75},
            {"name": "Data Structures", "minimumProficiency": 80},
        ],
        "preferredSkills": ["SQL & Databases", "Git"],
        "createdBy": "recruiter_tcs",
        "applicants": 176,
    },
]

DEMO_COURSES = [
    {
        "id": "course_cs301",
        "courseCode": "CS301",
        "courseName": "Data Structures & Algorithms",
        "semester": "Semester 3",
        "department": "Computer Science",
        "description": "Fundamental algorithms, space-time complexity analysis, graphs, trees, dynamic programming.",
        "skills": [
            {"skill": "Data Structures", "contribution": 35},
            {"skill": "Problem Solving", "contribution": 30},
        ],
    },
    {
        "id": "course_cs304",
        "courseCode": "CS304",
        "courseName": "Full-Stack Web Technologies",
        "semester": "Semester 5",
        "department": "Computer Science",
        "description": "Modern frontend frameworks, RESTful APIs, relational databases, and microservices architecture.",
        "skills": [
            {"skill": "React", "contribution": 30},
            {"skill": "JavaScript", "contribution": 25},
            {"skill": "Node.js", "contribution": 25},
            {"skill": "SQL & Databases", "contribution": 20},
        ],
    },
    {
        "id": "course_cs308",
        "courseCode": "CS308",
        "courseName": "Cloud Computing & DevOps",
        "semester": "Semester 6",
        "department": "Computer Science",
        "description": "Virtualization, containerization with Docker, cloud architectures on AWS, CI/CD pipelines.",
        "skills": [
            {"skill": "Cloud (AWS)", "contribution": 35},
            {"skill": "Docker & CI/CD", "contribution": 35},
            {"skill": "Git", "contribution": 15},
        ],
    },
]


def seed_database():
    """Seed Cloud Firestore with demo records."""
    print("Connecting to Firestore...")
    try:
        db = get_db()
    except Exception as e:
        print(f"Error connecting to Firestore: {e}")
        print("Please check backend/.env configuration before running the seed script.")
        return False

    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Seed Students & their subcollection skills
    print("Seeding Students...")
    for student in DEMO_STUDENTS:
        skills = student.pop("skills", [])
        uid = student["uid"]
        student["createdAt"] = now_iso
        student["updatedAt"] = now_iso

        # Write student document
        db.collection("users").document(uid).set(student)
        print(f"  + User: {student['name']} ({uid})")

        # Write student skills subcollection
        for skill in skills:
            skill_id = "skill_" + skill["name"].lower().replace(" ", "_").replace("&", "and").replace("(", "").replace(")", "").replace("/", "_")
            skill["score"] = skill["proficiency"]
            skill["required"] = 75
            skill["updatedAt"] = now_iso
            db.collection("users").document(uid).collection("skills").document(skill_id).set(skill)
            print(f"    - Skill: {skill['name']} (score: {skill['proficiency']})")

    # 2. Seed Jobs
    print("Seeding Jobs...")
    for job in DEMO_JOBS:
        job_id = job["id"]
        job["createdAt"] = now_iso
        db.collection("jobs").document(job_id).set(job)
        print(f"  + Job: {job['title']} at {job['company']}")

    # 3. Seed Courses
    print("Seeding Courses...")
    for course in DEMO_COURSES:
        course_id = course["id"]
        course["createdAt"] = now_iso
        db.collection("courses").document(course_id).set(course)
        print(f"  + Course: {course['courseCode']} - {course['courseName']}")

    print("\nDatabase seeding completed successfully!")
    return True


if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)
