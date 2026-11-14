import logging
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.skill import SkillCategory, Skill

logger = logging.getLogger(__name__)

CANONICAL_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Kotlin", "Swift"
    ],
    "Web Development": [
        "React", "Node.js", "FastAPI", "Flask", "Django", "HTML", "CSS", "Next.js", "Express", "Tailwind CSS", "Vue.js", "Angular"
    ],
    "Database Technologies": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Cassandra", "Elasticsearch", "Neo4j", "Oracle Database"
    ],
    "AI and Machine Learning": [
        "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", "Data Analysis",
        "PyTorch", "TensorFlow", "Scikit-learn", "LangChain", "Pandas", "NumPy", "HuggingFace"
    ],
    "Development Tools & DevOps": [
        "Git", "GitHub", "Docker", "Linux", "Kubernetes", "VS Code", "CI/CD", "Terraform", "Nginx", "Jenkins"
    ],
    "Cloud Platforms": [
        "Amazon Web Services", "Google Cloud Platform", "Microsoft Azure"
    ],
    "Professional & Soft Skills": [
        "Communication", "Leadership", "Problem Solving", "Teamwork", "Critical Thinking", "Agile Methodologies", "Project Management"
    ]
}


class SkillSeeder:
    @staticmethod
    async def seed_canonical_skills(db: AsyncSession) -> int:
        """
        Idempotently seeds categories and canonical skills into the database.
        Returns the number of new skills inserted.
        """
        inserted_count = 0
        for category_name, skills in CANONICAL_TAXONOMY.items():
            # Check or create category
            result = await db.execute(select(SkillCategory).where(SkillCategory.name == category_name))
            cat = result.scalar_one_or_none()
            if not cat:
                cat = SkillCategory(name=category_name, description=f"Canonical {category_name} skills")
                db.add(cat)
                await db.flush()

            for skill_name in skills:
                skill_slug = skill_name.lower().replace(" ", "-").replace("+", "p").replace("#", "sharp")
                skill_res = await db.execute(select(Skill).where(Skill.name == skill_name))
                existing_skill = skill_res.scalar_one_or_none()
                if not existing_skill:
                    new_skill = Skill(
                        category_id=cat.id,
                        name=skill_name,
                        slug=skill_slug,
                        description=f"Core industry skill: {skill_name}"
                    )
                    db.add(new_skill)
                    inserted_count += 1

        if inserted_count > 0:
            await db.commit()
            logger.info("Successfully seeded %d canonical skills into taxonomy", inserted_count)

        return inserted_count
