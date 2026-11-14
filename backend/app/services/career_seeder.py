import logging
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.career import CareerCategory, CareerRole, CareerSkillRequirement, CareerBenchmark
from app.models.skill import Skill
from app.models.learning import ResourceCategory, LearningResource
from app.services.skill_seeder import SkillSeeder

logger = logging.getLogger(__name__)

CAREER_ROLES_TAXONOMY: Dict[str, Dict] = {
    "Full Stack Developer": {
        "category": "Software Engineering",
        "demand": "VERY_HIGH",
        "salary": "$90,000 - $145,000",
        "description": "Designs, builds, and maintains complete client-side and server-side web applications.",
        "skills": [
            ("JavaScript", 3, True, 1.2),
            ("React", 3, True, 1.2),
            ("Node.js", 3, True, 1.0),
            ("Python", 3, False, 0.9),
            ("HTML", 3, True, 0.8),
            ("CSS", 3, True, 0.8),
            ("PostgreSQL", 3, True, 1.1),
            ("Git", 2, True, 0.9),
            ("Docker", 2, False, 0.8),
            ("REST APIs", 3, True, 1.1),
        ]
    },
    "Frontend Developer": {
        "category": "Software Engineering",
        "demand": "HIGH",
        "salary": "$80,000 - $130,000",
        "description": "Architects responsive user interfaces and client-side applications.",
        "skills": [
            ("JavaScript", 3, True, 1.2),
            ("TypeScript", 3, True, 1.1),
            ("React", 3, True, 1.3),
            ("HTML", 3, True, 1.0),
            ("CSS", 3, True, 1.0),
            ("Tailwind CSS", 2, False, 0.8),
            ("Git", 2, True, 0.8),
        ]
    },
    "Backend Developer": {
        "category": "Software Engineering",
        "demand": "VERY_HIGH",
        "salary": "$95,000 - $150,000",
        "description": "Builds robust APIs, server logic, database architectures, and distributed systems.",
        "skills": [
            ("Python", 3, True, 1.2),
            ("FastAPI", 3, True, 1.1),
            ("PostgreSQL", 3, True, 1.2),
            ("Redis", 2, False, 0.9),
            ("Docker", 2, True, 1.0),
            ("Git", 2, True, 0.8),
            ("Linux", 2, True, 0.9),
        ]
    },
    "Python Developer": {
        "category": "Software Engineering",
        "demand": "HIGH",
        "salary": "$85,000 - $135,000",
        "description": "Builds backend services, automation scripts, and data workflows using Python.",
        "skills": [
            ("Python", 4, True, 1.4),
            ("FastAPI", 3, True, 1.1),
            ("PostgreSQL", 2, True, 1.0),
            ("Git", 2, True, 0.8),
            ("Docker", 2, False, 0.8),
        ]
    },
    "Data Scientist": {
        "category": "Data & Artificial Intelligence",
        "demand": "VERY_HIGH",
        "salary": "$100,000 - $160,000",
        "description": "Analyzes complex datasets and builds machine learning models to solve business problems.",
        "skills": [
            ("Python", 4, True, 1.3),
            ("Data Analysis", 3, True, 1.2),
            ("Pandas", 3, True, 1.1),
            ("NumPy", 3, True, 1.0),
            ("Machine Learning", 3, True, 1.3),
            ("Scikit-learn", 3, True, 1.1),
            ("PostgreSQL", 2, True, 0.9),
        ]
    },
    "Machine Learning Engineer": {
        "category": "Data & Artificial Intelligence",
        "demand": "EXTREME",
        "salary": "$115,000 - $180,000",
        "description": "Designs and deploys scalable machine learning pipelines, deep learning models, and LLM applications.",
        "skills": [
            ("Python", 4, True, 1.2),
            ("Machine Learning", 4, True, 1.3),
            ("Deep Learning", 3, True, 1.2),
            ("PyTorch", 3, True, 1.2),
            ("Docker", 3, True, 1.0),
            ("Linux", 2, True, 0.8),
            ("LangChain", 2, False, 0.9),
        ]
    },
    "DevOps Engineer": {
        "category": "Cloud & Infrastructure",
        "demand": "VERY_HIGH",
        "salary": "$105,000 - $165,000",
        "description": "Automates continuous integration, infrastructure provisioning, and container orchestration.",
        "skills": [
            ("Linux", 3, True, 1.2),
            ("Docker", 4, True, 1.3),
            ("Kubernetes", 3, True, 1.3),
            ("CI/CD", 3, True, 1.2),
            ("Git", 3, True, 1.0),
            ("Python", 2, False, 0.8),
            ("Amazon Web Services", 3, True, 1.1),
        ]
    }
}

VERIFIED_LEARNING_RESOURCES = [
    {
        "category": "Web Development",
        "title": "MDN Web Docs: JavaScript Fundamentals",
        "url": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript",
        "resource_type": "DOCUMENTATION",
        "difficulty_level": 1,
        "estimated_minutes": 120,
        "provider_name": "Mozilla",
        "rating": 4.9,
        "content_summary": "Comprehensive reference and guides covering core JavaScript syntax, objects, and event loops.",
        "skill_name": "JavaScript"
    },
    {
        "category": "Web Development",
        "title": "React Official Documentation: Quick Start",
        "url": "https://react.dev/learn",
        "resource_type": "DOCUMENTATION",
        "difficulty_level": 2,
        "estimated_minutes": 180,
        "provider_name": "React Team",
        "rating": 4.9,
        "content_summary": "Interactive guide covering components, state, hooks, and modern React design patterns.",
        "skill_name": "React"
    },
    {
        "category": "Programming Languages",
        "title": "Official Python Tutorial",
        "url": "https://docs.python.org/3/tutorial/",
        "resource_type": "DOCUMENTATION",
        "difficulty_level": 1,
        "estimated_minutes": 150,
        "provider_name": "Python Software Foundation",
        "rating": 4.8,
        "content_summary": "Official tutorial introducing Python's basic and advanced concepts and features.",
        "skill_name": "Python"
    },
    {
        "category": "Web Development",
        "title": "FastAPI Tutorial - User Guide",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "resource_type": "DOCUMENTATION",
        "difficulty_level": 2,
        "estimated_minutes": 120,
        "provider_name": "tiangolo",
        "rating": 4.9,
        "content_summary": "Step-by-step tutorial for building high-performance REST APIs with Python, Pydantic, and OpenAPI.",
        "skill_name": "FastAPI"
    },
    {
        "category": "Database Technologies",
        "title": "PostgreSQL Tutorial",
        "url": "https://www.postgresqltutorial.com/",
        "resource_type": "TUTORIAL",
        "difficulty_level": 2,
        "estimated_minutes": 180,
        "provider_name": "PostgreSQL Tutorial",
        "rating": 4.7,
        "content_summary": "Practical tutorials on SQL queries, joins, indexing, transactions, and performance tuning.",
        "skill_name": "PostgreSQL"
    },
    {
        "category": "Development Tools & DevOps",
        "title": "Docker Get Started Guide",
        "url": "https://docs.docker.com/get-started/",
        "resource_type": "DOCUMENTATION",
        "difficulty_level": 2,
        "estimated_minutes": 90,
        "provider_name": "Docker",
        "rating": 4.8,
        "content_summary": "Hands-on guide to containerization, Dockerfiles, multi-stage builds, and Docker Compose.",
        "skill_name": "Docker"
    },
    {
        "category": "Web Development",
        "title": "freeCodeCamp: Responsive Web Design (HTML & CSS)",
        "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
        "resource_type": "TUTORIAL",
        "difficulty_level": 1,
        "estimated_minutes": 240,
        "provider_name": "freeCodeCamp",
        "rating": 4.9,
        "content_summary": "Free hands-on curriculum covering modern HTML5, CSS3, Flexbox, and CSS Grid layout systems.",
        "skill_name": "HTML"
    },
    {
        "category": "Web Development",
        "title": "Node.js Complete Guide (Official)",
        "url": "https://nodejs.org/en/learn",
        "resource_type": "DOCUMENTATION",
        "difficulty_level": 2,
        "estimated_minutes": 150,
        "provider_name": "Node.js Foundation",
        "rating": 4.8,
        "content_summary": "Learn asynchronous event-driven JavaScript runtime, buffers, streams, and HTTP servers.",
        "skill_name": "Node.js"
    }
]


class CareerSeeder:
    @staticmethod
    async def seed_career_data(db: AsyncSession) -> None:
        """
        Idempotently seeds career roles, skill requirements, and verified learning resources.
        """
        # Ensure canonical skills exist first
        await SkillSeeder.seed_canonical_skills(db)

        # 1. Seed Career Roles & Requirements
        for role_title, role_data in CAREER_ROLES_TAXONOMY.items():
            cat_name = role_data["category"]
            cat_res = await db.execute(select(CareerCategory).where(CareerCategory.name == cat_name))
            cat = cat_res.scalar_one_or_none()
            if not cat:
                cat = CareerCategory(name=cat_name, description=f"Career domain: {cat_name}")
                db.add(cat)
                await db.flush()

            role_slug = role_title.lower().replace(" ", "-")
            role_res = await db.execute(select(CareerRole).where(CareerRole.title == role_title))
            role = role_res.scalar_one_or_none()
            if not role:
                role = CareerRole(
                    category_id=cat.id,
                    title=role_title,
                    slug=role_slug,
                    description=role_data["description"],
                    industry_demand_level=role_data["demand"],
                    average_salary_range=role_data["salary"]
                )
                db.add(role)
                await db.flush()

            # Seed skill requirements for role
            for skill_name, req_level, is_mandatory, weight in role_data["skills"]:
                skill_res = await db.execute(select(Skill).where(Skill.name.ilike(skill_name)))
                skill = skill_res.scalar_one_or_none()
                if skill:
                    req_check = await db.execute(
                        select(CareerSkillRequirement).where(
                            CareerSkillRequirement.career_role_id == role.id,
                            CareerSkillRequirement.skill_id == skill.id
                        )
                    )
                    if not req_check.scalar_one_or_none():
                        new_req = CareerSkillRequirement(
                            career_role_id=role.id,
                            skill_id=skill.id,
                            required_proficiency=req_level,
                            importance_weight=weight,
                            is_mandatory=is_mandatory
                        )
                        db.add(new_req)

        # 2. Seed Learning Resources
        for res_data in VERIFIED_LEARNING_RESOURCES:
            cat_name = res_data["category"]
            cat_res = await db.execute(select(ResourceCategory).where(ResourceCategory.name == cat_name))
            cat = cat_res.scalar_one_or_none()
            if not cat:
                cat = ResourceCategory(name=cat_name, description=f"Learning materials for {cat_name}")
                db.add(cat)
                await db.flush()

            res_check = await db.execute(select(LearningResource).where(LearningResource.title == res_data["title"]))
            if not res_check.scalar_one_or_none():
                new_resource = LearningResource(
                    category_id=cat.id,
                    title=res_data["title"],
                    url=res_data["url"],
                    resource_type=res_data["resource_type"],
                    difficulty_level=res_data["difficulty_level"],
                    estimated_minutes=res_data["estimated_minutes"],
                    provider_name=res_data["provider_name"],
                    rating=res_data["rating"],
                    is_free=True,
                    content_summary=res_data["content_summary"]
                )
                db.add(new_resource)

        await db.commit()
        logger.info("Career taxonomy and verified learning resources successfully seeded.")
