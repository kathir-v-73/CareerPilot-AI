import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

def get_sample_jobs() -> List[Dict[str, Any]]:
    """Generate sample job data for demonstration purposes"""
    
    # Define realistic data pools
    job_titles = [
        "Software Engineer", "Senior Software Engineer", "Full Stack Developer",
        "Backend Developer", "Frontend Developer", "Data Scientist", "Data Engineer",
        "Machine Learning Engineer", "DevOps Engineer", "Cloud Architect",
        "Product Manager", "Technical Lead", "Software Development Manager",
        "QA Engineer", "Test Automation Engineer", "Mobile Developer",
        "UI/UX Designer", "Business Analyst", "System Administrator",
        "Database Administrator", "Security Engineer", "Site Reliability Engineer",
        "Python Developer", "Java Developer", "React Developer", "Node.js Developer",
        "AI/ML Engineer", "Big Data Engineer", "Solutions Architect",
        "Technical Architect", "Lead Developer"
    ]
    
    companies = [
        "Infosys", "TCS", "Wipro", "HCL Technologies", "Tech Mahindra",
        "Accenture", "IBM", "Microsoft", "Google", "Amazon",
        "Flipkart", "Zomato", "PayTM", "Ola", "Swiggy",
        "BYJU'S", "Freshworks", "Zoho", "Mindtree", "Cognizant",
        "Oracle", "SAP", "Adobe", "Salesforce", "Dell",
        "HP", "Intel", "NVIDIA", "Qualcomm", "Cisco",
        "PhonePe", "Razorpay", "Cred", "Dream11", "MPL",
        "Urban Company", "BigBasket", "Nykaa", "PolicyBazaar",
        "MakeMyTrip", "BookMyShow", "Jio", "Airtel", "Vodafone"
    ]
    
    locations = [
        "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune",
        "Chennai", "Kolkata", "Gurgaon", "Noida", "Ahmedabad",
        "Kochi", "Thiruvananthapuram", "Indore", "Jaipur", "Chandigarh",
        "Remote", "Coimbatore", "Mysore", "Mangalore", "Bhopal"
    ]
    
    # Comprehensive skills database
    technical_skills = [
        # Programming Languages
        "Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "Kotlin",
        "Swift", "TypeScript", "PHP", "Ruby", "Scala", "R",
        
        # Web Technologies
        "React", "Angular", "Vue.js", "Node.js", "Express.js", "Django",
        "Flask", "Spring Boot", "Laravel", "Rails", "ASP.NET",
        
        # Databases
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
        "Oracle", "SQL Server", "Cassandra", "Neo4j", "DynamoDB",
        
        # Cloud & DevOps
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
        "Git", "CI/CD", "Terraform", "Ansible", "Linux", "Unix",
        
        # Data & AI/ML
        "Machine Learning", "Deep Learning", "Data Science", "TensorFlow",
        "PyTorch", "Pandas", "NumPy", "Scikit-learn", "Apache Spark",
        "Hadoop", "Kafka", "Airflow", "Power BI", "Tableau",
        
        # Mobile Development
        "Android", "iOS", "React Native", "Flutter", "Xamarin",
        
        # Other Technologies
        "Microservices", "REST APIs", "GraphQL", "Agile", "Scrum",
        "JIRA", "Confluence", "Selenium", "Jest", "JUnit"
    ]
    
    soft_skills = [
        "Communication", "Leadership", "Problem Solving", "Team Work",
        "Critical Thinking", "Time Management", "Adaptability",
        "Project Management", "Analytical Skills", "Creativity"
    ]
    
    # Generate sample jobs
    sample_jobs = []
    
    for i in range(500):  # Generate 500 sample jobs
        # Select random values
        title = random.choice(job_titles)
        company = random.choice(companies)
        location = random.choice(locations)
        
        # Generate skill combinations based on job title
        skills = generate_relevant_skills(title, technical_skills, soft_skills)
        
        # Generate salary range based on role and experience
        exp_min, exp_max, salary_min, salary_max = generate_salary_experience(title)
        
        # Experience level mapping
        avg_exp = (exp_min + exp_max) / 2
        if avg_exp <= 2:
            experience_level = "Entry Level (0-2 years)"
        elif avg_exp <= 5:
            experience_level = "Mid Level (3-5 years)"
        elif avg_exp <= 10:
            experience_level = "Senior Level (6-10 years)"
        else:
            experience_level = "Expert Level (10+ years)"
        
        # Generate posting date (within last 30 days)
        posted_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        job = {
            "job_title": title,
            "company": company,
            "location": location,
            "skills": ", ".join(skills),
            "experience": f"{exp_min}-{exp_max} years",
            "exp_min": exp_min,
            "exp_max": exp_max,
            "salary": f"₹{salary_min}-{salary_max} LPA",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": experience_level,
            "posted_date": posted_date,
            "description": generate_job_description(title, skills),
            "employment_type": random.choice(["Full-time", "Contract", "Internship"]),
            "industry": get_industry_for_company(company)
        }
        
        sample_jobs.append(job)
    
    return sample_jobs

def generate_relevant_skills(job_title: str, technical_skills: List[str], soft_skills: List[str]) -> List[str]:
    """Generate relevant skills based on job title"""
    
    # Define skill mappings for different roles
    role_skill_mapping = {
        "software engineer": ["Python", "Java", "JavaScript", "Git", "SQL", "Problem Solving"],
        "data scientist": ["Python", "R", "Machine Learning", "Pandas", "NumPy", "SQL", "Statistics"],
        "frontend developer": ["JavaScript", "React", "HTML", "CSS", "Vue.js", "TypeScript"],
        "backend developer": ["Python", "Java", "Node.js", "SQL", "REST APIs", "Microservices"],
        "devops engineer": ["AWS", "Docker", "Kubernetes", "Jenkins", "Linux", "CI/CD"],
        "mobile developer": ["Android", "iOS", "React Native", "Flutter", "Swift", "Kotlin"],
        "data engineer": ["Python", "SQL", "Apache Spark", "Hadoop", "Kafka", "AWS"],
        "machine learning engineer": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning"],
        "full stack developer": ["JavaScript", "React", "Node.js", "Python", "SQL", "Git"],
        "cloud architect": ["AWS", "Azure", "Google Cloud", "Microservices", "Docker", "Kubernetes"],
        "product manager": ["Agile", "Scrum", "JIRA", "Analytics", "Communication", "Leadership"],
        "qa engineer": ["Selenium", "Testing", "Automation", "JIRA", "Python", "Quality Assurance"]
    }
    
    # Get relevant skills for the role
    job_title_lower = job_title.lower()
    relevant_skills = []
    
    # Find matching skills
    for role_key, skills in role_skill_mapping.items():
        if role_key in job_title_lower or any(word in job_title_lower for word in role_key.split()):
            relevant_skills.extend(skills)
            break
    
    # Add some random technical and soft skills
    if not relevant_skills:
        relevant_skills = random.sample(technical_skills, random.randint(4, 8))
    
    # Add additional skills
    additional_technical = random.sample(
        [skill for skill in technical_skills if skill not in relevant_skills],
        random.randint(2, 4)
    )
    additional_soft = random.sample(soft_skills, random.randint(1, 3))
    
    all_skills = relevant_skills + additional_technical + additional_soft
    
    # Return 5-12 skills randomly
    return random.sample(all_skills, min(len(all_skills), random.randint(5, 12)))

def generate_salary_experience(job_title: str) -> tuple:
    """Generate salary and experience ranges based on job title"""
    
    # Define role categories with base salary and experience ranges
    role_categories = {
        "entry": {
            "roles": ["intern", "junior", "trainee", "associate"],
            "exp_range": (0, 2),
            "salary_base": (3, 8)
        },
        "mid": {
            "roles": ["developer", "engineer", "analyst", "specialist"],
            "exp_range": (2, 6),
            "salary_base": (8, 18)
        },
        "senior": {
            "roles": ["senior", "lead", "principal", "staff"],
            "exp_range": (5, 10),
            "salary_base": (15, 35)
        },
        "management": {
            "roles": ["manager", "director", "head", "vp", "architect"],
            "exp_range": (8, 15),
            "salary_base": (25, 60)
        }
    }
    
    job_title_lower = job_title.lower()
    
    # Determine category
    category = "mid"  # default
    for cat, data in role_categories.items():
        if any(role_keyword in job_title_lower for role_keyword in data["roles"]):
            category = cat
            break
    
    # Get base ranges
    exp_base = role_categories[category]["exp_range"]
    salary_base = role_categories[category]["salary_base"]
    
    # Add some randomness
    exp_min = max(0, exp_base[0] + random.randint(-1, 1))
    exp_max = exp_base[1] + random.randint(-1, 2)
    
    salary_min = salary_base[0] + random.randint(-2, 3)
    salary_max = salary_base[1] + random.randint(-5, 10)
    
    # Ensure logical ranges
    exp_max = max(exp_min + 1, exp_max)
    salary_max = max(salary_min + 2, salary_max)
    
    return exp_min, exp_max, salary_min, salary_max

def generate_job_description(job_title: str, skills: List[str]) -> str:
    """Generate a realistic job description"""
    
    descriptions = [
        f"We are looking for a talented {job_title} to join our dynamic team. The ideal candidate will have experience in {', '.join(skills[:3])} and be passionate about technology.",
        
        f"Join our innovative team as a {job_title}! You'll work on cutting-edge projects using {', '.join(skills[:4])} and collaborate with cross-functional teams.",
        
        f"Exciting opportunity for a {job_title} to work with modern technologies including {', '.join(skills[:3])}. We offer competitive compensation and growth opportunities.",
        
        f"We're seeking a skilled {job_title} with expertise in {', '.join(skills[:4])}. This role offers the chance to work on impactful projects and advance your career."
    ]
    
    return random.choice(descriptions)

def get_industry_for_company(company: str) -> str:
    """Get industry based on company name"""
    
    tech_companies = ["Infosys", "TCS", "Wipro", "HCL", "Microsoft", "Google", "Amazon", "IBM"]
    fintech_companies = ["PayTM", "Razorpay", "PhonePe", "Cred"]
    ecommerce_companies = ["Flipkart", "Amazon", "BigBasket", "Nykaa"]
    food_companies = ["Zomato", "Swiggy"]
    edtech_companies = ["BYJU'S"]
    
    if company in tech_companies:
        return "Technology"
    elif company in fintech_companies:
        return "Financial Technology"
    elif company in ecommerce_companies:
        return "E-commerce"
    elif company in food_companies:
        return "Food & Delivery"
    elif company in edtech_companies:
        return "Education Technology"
    else:
        return random.choice(["Technology", "Finance", "Healthcare", "Manufacturing", "Consulting"])
