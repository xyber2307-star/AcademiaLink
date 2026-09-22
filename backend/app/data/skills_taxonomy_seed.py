"""
Seed data for the canonical Skill Taxonomy (Firestore collection 'skills').

This is NOT meant to be "every skill on Earth" - it is a structured, disciplined starting
taxonomy organized by real-world category/subcategory, sourced from standard industry skill
groupings. New skills are added going forward via the admin skill-management API (see
app/routes/admin_skills.py), never by hard-coding more entries here or in the frontend.

Each entry: (name, category, subcategory, type, aliases)
  type is one of: "technical", "tool", "soft", "domain"
"""
from typing import Any, Dict, List, Optional, Tuple

Entry = Tuple[str, str, str, str, List[str]]


def _e(name: str, category: str, subcategory: str, type_: str = "technical", aliases: Optional[List[str]] = None) -> Entry:
    return (name, category, subcategory, type_, aliases or [])


def build_taxonomy_entries() -> List[Entry]:
    entries: List[Entry] = []

    # ---------------- Computer Science & Software ----------------
    cat = "Computer Science & Software"
    entries += [_e(n, cat, "Programming Languages", "technical", a) for n, a in [
        ("Python", ["Python Programming"]), ("Java", []), ("JavaScript", ["JS"]), ("TypeScript", ["TS"]),
        ("C", []), ("C++", ["CPP"]), ("C#", ["CSharp"]), ("Go", ["Golang"]), ("Rust", []),
        ("Kotlin", []), ("Swift", []), ("PHP", []), ("Ruby", []), ("Dart", []), ("R", []),
        ("Scala", []), ("Perl", []), ("Objective-C", []), ("MATLAB", []), ("Shell Scripting", ["Bash"]),
        ("SQL", []), ("HTML", []), ("CSS", []),
    ]]
    entries += [_e(n, cat, "Algorithms & Data Structures", "technical", []) for n in [
        "Algorithms", "Data Structures", "Competitive Programming", "Dynamic Programming",
        "Graph Algorithms", "Complexity Analysis",
    ]]
    entries += [_e(n, cat, "Web Development", "technical", a) for n, a in [
        ("Frontend Development", []), ("Backend Development", []), ("Full-Stack Development", []),
        ("REST API Design", ["REST", "RESTful API"]), ("GraphQL API Design", []), ("Web Accessibility", []),
        ("Responsive Web Design", []), ("Progressive Web Apps", ["PWA"]),
    ]]
    entries += [_e(n, cat, "Mobile Development", "technical", []) for n in [
        "Android Development", "iOS Development", "Cross-Platform Mobile Development",
    ]]
    entries += [_e(n, cat, "Software Engineering Practice", "technical", []) for n in [
        "Software Engineering", "Software Architecture", "Software Design Patterns", "Software Testing", "Test-Driven Development",
        "Code Review", "Software Documentation", "Agile Software Development", "Microservices Architecture",
        "Distributed Systems", "System Design", "API Design", "Object-Oriented Programming",
        "Functional Programming",
    ]]
    entries += [_e(n, cat, "Databases", "technical", []) for n in [
        "Database Design", "Database Administration", "Query Optimization", "NoSQL Databases",
        "Relational Databases", "Data Modeling",
    ]]
    entries += [_e(n, cat, "DevOps & Cloud", "technical", []) for n in [
        "DevOps", "Cloud Computing", "Continuous Integration", "Continuous Deployment",
        "Infrastructure as Code", "Site Reliability Engineering", "Container Orchestration",
        "Serverless Computing",
    ]]

    # Tools/Technologies (frameworks, platforms, languages ecosystem)
    entries += [_e(n, cat, "Frameworks & Libraries", "tool", a) for n, a in [
        ("React", []), ("Next.js", []), ("Angular", []), ("Vue.js", ["Vue"]), ("Svelte", []),
        ("Node.js", []), ("Django", []), ("FastAPI", []), ("Flask", []), ("Spring Boot", ["Spring"]),
        (".NET", ["dotnet", "ASP.NET"]), ("Express.js", ["Express"]), ("Ruby on Rails", ["Rails"]),
        ("Laravel", []), ("jQuery", []), ("Redux", []), ("Tailwind CSS", []), ("Bootstrap", []),
    ]]
    entries += [_e(n, cat, "Databases & Data Stores", "tool", []) for n in [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Firebase", "SQLite", "Oracle Database",
        "Microsoft SQL Server", "Cassandra", "DynamoDB", "Elasticsearch",
    ]]
    entries += [_e(n, cat, "Cloud Platforms", "tool", a) for n, a in [
        ("AWS", ["Amazon Web Services"]), ("Microsoft Azure", ["Azure"]), ("Google Cloud Platform", ["GCP", "Google Cloud"]),
        ("Heroku", []), ("Vercel", []), ("Netlify", []),
    ]]
    entries += [_e(n, cat, "DevOps Tools", "tool", []) for n in [
        "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "Jenkins", "Terraform", "Ansible",
        "CircleCI", "GitHub Actions", "Prometheus", "Grafana", "Nginx", "Apache Kafka", "RabbitMQ",
    ]]
    entries += [_e(n, cat, "Development Environments", "tool", []) for n in [
        "VS Code", "IntelliJ IDEA", "Postman", "Jupyter Notebook", "Linux", "Windows Server",
    ]]

    # ---------------- AI & Data ----------------
    cat = "AI & Data"
    entries += [_e(n, cat, "Machine Learning & AI", "technical", a) for n, a in [
        ("Machine Learning", ["ML"]), ("Deep Learning", []), ("Natural Language Processing", ["NLP"]),
        ("Computer Vision", []), ("Generative AI", []), ("Reinforcement Learning", []),
        ("Large Language Models", ["LLM", "LLMs"]), ("Prompt Engineering", []), ("Neural Networks", []),
        ("Model Deployment", []), ("MLOps", []),
    ]]
    entries += [_e(n, cat, "Data Science & Analytics", "technical", []) for n in [
        "Data Science", "Data Analytics", "Data Analysis", "Statistics", "Data Engineering",
        "Data Visualization", "Predictive Modeling", "A/B Testing", "Data Mining", "Feature Engineering",
        "Big Data", "ETL Pipeline Development", "Data Warehousing",
    ]]
    entries += [_e(n, cat, "AI/ML Tools & Frameworks", "tool", []) for n in [
        "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy", "Power BI", "Tableau",
        "Apache Spark", "Hugging Face Transformers", "OpenCV", "LangChain",
    ]]

    # ---------------- Cybersecurity ----------------
    cat = "Cybersecurity"
    entries += [_e(n, cat, "Security Disciplines", "technical", []) for n in [
        "Cybersecurity", "Networking", "Network Security", "Application Security", "Ethical Hacking", "Penetration Testing",
        "Digital Forensics", "Incident Response", "Cryptography", "Security Operations",
        "SOC Fundamentals", "Cloud Security", "Threat Intelligence", "Vulnerability Assessment",
        "Malware Analysis", "Identity and Access Management", "Security Auditing", "Risk Assessment",
    ]]
    entries += [_e(n, cat, "Security Tools", "tool", a) for n, a in [
        ("Wireshark", []), ("Metasploit", []), ("Nmap", []), ("Burp Suite", []), ("Splunk", []),
        ("SIEM Tools", ["SIEM"]), ("Kali Linux", []), ("Nessus", []),
    ]]

    # ---------------- Engineering ----------------
    cat = "Engineering"
    entries += [_e(n, cat, "Mechanical Engineering", "domain", []) for n in [
        "Mechanical Engineering", "Thermodynamics", "Fluid Mechanics", "Machine Design",
        "Manufacturing Processes", "HVAC Design", "Mechatronics",
    ]]
    entries += [_e(n, cat, "Civil Engineering", "domain", []) for n in [
        "Civil Engineering", "Structural Analysis", "Geotechnical Engineering", "Surveying",
        "Construction Management", "Transportation Engineering", "Structural Design",
    ]]
    entries += [_e(n, cat, "Electrical & Electronics Engineering", "domain", []) for n in [
        "Electrical Engineering", "Electronics Engineering", "Circuit Design", "Power Systems",
        "Signal Processing", "VLSI Design", "Analog Electronics", "Digital Electronics",
    ]]
    entries += [_e(n, cat, "Other Engineering Disciplines", "domain", []) for n in [
        "Chemical Engineering", "Aerospace Engineering", "Biomedical Engineering",
        "Industrial Engineering", "Environmental Engineering", "Robotics", "Control Systems",
    ]]
    entries += [_e(n, cat, "Engineering Tools & Methods", "tool", []) for n in [
        "CAD", "CAM", "AutoCAD", "SolidWorks", "CATIA", "Simulation", "Finite Element Analysis",
        "PLC Programming", "Embedded Systems", "Embedded C",
    ]]

    # ---------------- Business & Management ----------------
    cat = "Business & Management"
    entries += [_e(n, cat, "Management & Strategy", "domain", []) for n in [
        "Business Analysis", "Project Management", "Product Management", "Operations Management",
        "Supply Chain Management", "Strategic Planning", "Entrepreneurship", "Leadership",
        "Management", "Business Intelligence", "Change Management", "Stakeholder Management",
        "Vendor Management", "Process Improvement",
    ]]
    entries += [_e(n, cat, "Management Tools", "tool", []) for n in [
        "Jira", "Asana", "Trello", "Microsoft Excel", "Microsoft Project",
    ]]

    # ---------------- Finance & Economics ----------------
    cat = "Finance & Economics"
    entries += [_e(n, cat, "Finance", "domain", []) for n in [
        "Financial Analysis", "Accounting", "Corporate Finance", "Investment Analysis",
        "Risk Management", "Economics", "Financial Modeling", "Auditing", "Taxation",
        "Budgeting", "Financial Reporting", "Equity Research", "Portfolio Management",
    ]]
    entries += [_e(n, cat, "Finance Tools", "tool", []) for n in [
        "Bloomberg Terminal", "QuickBooks", "SAP FICO",
    ]]

    # ---------------- Marketing & Sales ----------------
    cat = "Marketing & Sales"
    entries += [_e(n, cat, "Marketing", "domain", []) for n in [
        "Digital Marketing", "SEO", "SEM", "Content Marketing", "Social Media Marketing",
        "Market Research", "Brand Management", "Advertising", "Email Marketing",
        "Marketing Analytics", "Growth Marketing", "Copywriting",
    ]]
    entries += [_e(n, cat, "Sales", "domain", []) for n in [
        "Sales", "CRM Management", "Lead Generation", "Sales Negotiation", "Account Management",
    ]]
    entries += [_e(n, cat, "Marketing Tools", "tool", []) for n in [
        "Google Analytics", "Google Ads", "HubSpot", "Salesforce", "Mailchimp", "Meta Ads Manager",
    ]]

    # ---------------- Design & Creative ----------------
    cat = "Design & Creative"
    entries += [_e(n, cat, "Design Disciplines", "domain", []) for n in [
        "UI Design", "UX Design", "Graphic Design", "Motion Design", "3D Modeling", "Animation",
        "Video Editing", "Photography", "Illustration", "Typography", "Interaction Design",
        "Design Systems", "User Research", "Wireframing",
    ]]
    entries += [_e(n, cat, "Design Tools", "tool", []) for n in [
        "Figma", "Adobe Photoshop", "Adobe Illustrator", "Adobe Premiere Pro", "Adobe After Effects",
        "Adobe XD", "Sketch", "Blender", "Canva", "InVision",
    ]]

    # ---------------- Communication & Languages ----------------
    cat = "Communication & Languages"
    entries += [_e(n, cat, "Professional Communication", "soft", []) for n in [
        "Public Speaking", "Presentation Skills", "Technical Writing", "Business Writing",
        "Communication", "Negotiation", "Interpersonal Communication", "Report Writing",
    ]]
    entries += [_e(n, cat, "Languages", "domain", []) for n in [
        "English", "Hindi", "Telugu", "Tamil", "Kannada", "Marathi", "Bengali", "French",
        "German", "Spanish", "Mandarin Chinese", "Japanese",
    ]]

    # ---------------- Healthcare & Life Sciences ----------------
    cat = "Healthcare & Life Sciences"
    entries += [_e(n, cat, "Clinical & Life Sciences", "domain", []) for n in [
        "Patient Care", "Clinical Research", "Medical Coding", "Pharmacology", "Biostatistics",
        "Nursing", "Radiology", "Healthcare Informatics", "Public Health", "Epidemiology",
        "Molecular Biology", "Biotechnology", "Genomics", "Medical Imaging", "Anatomy & Physiology",
    ]]

    # ---------------- Education & Research ----------------
    cat = "Education & Research"
    entries += [_e(n, cat, "Teaching & Research", "domain", []) for n in [
        "Teaching", "Curriculum Design", "Academic Research", "Scientific Writing",
        "Research Methodology", "Laboratory Skills", "Grant Writing", "Peer Review",
        "Instructional Design",
    ]]

    # ---------------- Legal & Compliance ----------------
    cat = "Legal & Compliance"
    entries += [_e(n, cat, "Legal", "domain", []) for n in [
        "Contract Management", "Regulatory Compliance", "Legal Research", "Corporate Law",
        "Data Privacy", "Risk & Governance", "Intellectual Property Law", "Litigation Support",
        "Compliance Auditing",
    ]]

    # ---------------- Hospitality & Tourism ----------------
    cat = "Hospitality & Tourism"
    entries += [_e(n, cat, "Hospitality Operations", "domain", []) for n in [
        "Hotel Management", "Front Office Operations", "Food & Beverage Management",
        "Event Management", "Travel Planning", "Guest Relations", "Housekeeping Management",
    ]]

    # ---------------- Agriculture ----------------
    cat = "Agriculture"
    entries += [_e(n, cat, "Agricultural Practice", "domain", []) for n in [
        "Crop Management", "Soil Science", "Agronomy", "Irrigation Management",
        "Farm Management", "Horticulture", "Precision Agriculture", "Agricultural Economics",
    ]]

    # ---------------- Media & Entertainment ----------------
    cat = "Media & Entertainment"
    entries += [_e(n, cat, "Media Production", "domain", []) for n in [
        "Journalism", "Broadcast Production", "Screenwriting", "Sound Design", "Film Direction",
        "Content Creation", "Podcast Production", "Game Design",
    ]]

    # ---------------- Skilled Trades ----------------
    cat = "Skilled Trades"
    entries += [_e(n, cat, "Trade Skills", "domain", []) for n in [
        "Electrical Wiring", "Plumbing", "Carpentry", "Welding", "HVAC Repair",
        "Automotive Repair", "Machining", "Sheet Metal Work",
    ]]

    # ---------------- Manufacturing ----------------
    cat = "Manufacturing"
    entries += [_e(n, cat, "Manufacturing & Quality", "domain", []) for n in [
        "Lean Manufacturing", "Six Sigma", "Quality Control", "Quality Assurance",
        "Production Planning", "Supply Chain Operations", "Inventory Management",
        "Total Quality Management",
    ]]

    # ---------------- Architecture ----------------
    cat = "Architecture"
    entries += [_e(n, cat, "Architectural Design", "domain", []) for n in [
        "Architectural Design", "Urban Planning", "Building Information Modeling", "Landscape Architecture",
        "Interior Design", "Sustainable Design",
    ]]
    entries += [_e(n, cat, "Architecture Tools", "tool", ["BIM"]) for n in ["Revit", "SketchUp"]]

    # ---------------- Construction ----------------
    cat = "Construction"
    entries += [_e(n, cat, "Construction Management", "domain", []) for n in [
        "Site Supervision", "Cost Estimation", "Construction Safety Management",
        "Building Codes Compliance", "Contract Administration",
    ]]

    # ---------------- Logistics ----------------
    cat = "Logistics"
    entries += [_e(n, cat, "Logistics & Supply Chain", "domain", []) for n in [
        "Warehouse Management", "Fleet Management", "Freight Management", "Procurement",
        "Demand Planning", "Logistics Coordination",
    ]]

    # ---------------- Human Resources ----------------
    cat = "Human Resources"
    entries += [_e(n, cat, "HR Practice", "domain", []) for n in [
        "Talent Acquisition", "Employee Relations", "Compensation & Benefits", "HR Analytics",
        "Performance Management", "Organizational Development", "Onboarding",
    ]]

    # ---------------- Customer Service ----------------
    cat = "Customer Service"
    entries += [_e(n, cat, "Customer Support", "domain", []) for n in [
        "Customer Support", "Technical Support", "Customer Relationship Management",
        "Complaint Resolution", "Help Desk Operations",
    ]]

    # ---------------- Soft Skills ----------------
    cat = "Soft Skills"
    entries += [_e(n, cat, "Core Soft Skills", "soft", []) for n in [
        "Leadership", "Teamwork", "Problem Solving", "Critical Thinking", "Time Management",
        "Adaptability", "Collaboration", "Creativity", "Decision Making", "Emotional Intelligence",
        "Conflict Resolution", "Attention to Detail", "Work Ethic", "Mentoring",
    ]]

    return entries
