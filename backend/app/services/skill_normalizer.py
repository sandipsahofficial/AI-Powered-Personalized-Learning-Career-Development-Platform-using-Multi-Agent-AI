import re
import difflib
import logging
from typing import Dict, Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.skill import Skill, SkillCategory
from app.schemas.profiling import NormalizedSkillResult

logger = logging.getLogger(__name__)

# Core alias mapping table
SKILL_ALIASES: Dict[str, Tuple[str, str]] = {
    # phrase (lower): (canonical_name, category)
    "js": ("JavaScript", "Programming Languages"),
    "javascript": ("JavaScript", "Programming Languages"),
    "ts": ("TypeScript", "Programming Languages"),
    "typescript": ("TypeScript", "Programming Languages"),
    "py": ("Python", "Programming Languages"),
    "python": ("Python", "Programming Languages"),
    "python3": ("Python", "Programming Languages"),
    "golang": ("Go", "Programming Languages"),
    "go": ("Go", "Programming Languages"),
    "cpp": ("C++", "Programming Languages"),
    "c++": ("C++", "Programming Languages"),
    "c#": ("C#", "Programming Languages"),
    "csharp": ("C#", "Programming Languages"),
    "c sharp": ("C#", "Programming Languages"),
    
    # Web Development
    "react": ("React", "Web Development"),
    "reactjs": ("React", "Web Development"),
    "react.js": ("React", "Web Development"),
    "next": ("Next.js", "Web Development"),
    "nextjs": ("Next.js", "Web Development"),
    "next.js": ("Next.js", "Web Development"),
    "node": ("Node.js", "Web Development"),
    "nodejs": ("Node.js", "Web Development"),
    "node.js": ("Node.js", "Web Development"),
    "fastapi": ("FastAPI", "Web Development"),
    "fast api": ("FastAPI", "Web Development"),
    "flask": ("Flask", "Web Development"),
    "django": ("Django", "Web Development"),
    "express": ("Express", "Web Development"),
    "expressjs": ("Express", "Web Development"),
    "express.js": ("Express", "Web Development"),
    "tailwind": ("Tailwind CSS", "Web Development"),
    "tailwindcss": ("Tailwind CSS", "Web Development"),
    "html5": ("HTML", "Web Development"),
    "html": ("HTML", "Web Development"),
    "css3": ("CSS", "Web Development"),
    "css": ("CSS", "Web Development"),

    # Databases
    "postgres": ("PostgreSQL", "Database Technologies"),
    "postgresql": ("PostgreSQL", "Database Technologies"),
    "postgre sql": ("PostgreSQL", "Database Technologies"),
    "psql": ("PostgreSQL", "Database Technologies"),
    "mysql": ("MySQL", "Database Technologies"),
    "mongo": ("MongoDB", "Database Technologies"),
    "mongodb": ("MongoDB", "Database Technologies"),
    "redis": ("Redis", "Database Technologies"),
    "sqlite": ("SQLite", "Database Technologies"),
    "sqlite3": ("SQLite", "Database Technologies"),
    "cassandra": ("Cassandra", "Database Technologies"),

    # AI & ML
    "ml": ("Machine Learning", "AI and Machine Learning"),
    "machine learning": ("Machine Learning", "AI and Machine Learning"),
    "dl": ("Deep Learning", "AI and Machine Learning"),
    "deep learning": ("Deep Learning", "AI and Machine Learning"),
    "nlp": ("Natural Language Processing", "AI and Machine Learning"),
    "natural language processing": ("Natural Language Processing", "AI and Machine Learning"),
    "cv": ("Computer Vision", "AI and Machine Learning"),
    "computer vision": ("Computer Vision", "AI and Machine Learning"),
    "pytorch": ("PyTorch", "AI and Machine Learning"),
    "torch": ("PyTorch", "AI and Machine Learning"),
    "tf": ("TensorFlow", "AI and Machine Learning"),
    "tensorflow": ("TensorFlow", "AI and Machine Learning"),
    "scikit-learn": ("Scikit-learn", "AI and Machine Learning"),
    "scikit learn": ("Scikit-learn", "AI and Machine Learning"),
    "sklearn": ("Scikit-learn", "AI and Machine Learning"),
    "pandas": ("Pandas", "AI and Machine Learning"),
    "numpy": ("NumPy", "AI and Machine Learning"),
    "langchain": ("LangChain", "AI and Machine Learning"),
    "data analysis": ("Data Analysis", "AI and Machine Learning"),

    # Tools & DevOps & Cloud
    "git": ("Git", "Development Tools & DevOps"),
    "github": ("GitHub", "Development Tools & DevOps"),
    "docker": ("Docker", "Development Tools & DevOps"),
    "k8s": ("Kubernetes", "Development Tools & DevOps"),
    "kubernetes": ("Kubernetes", "Development Tools & DevOps"),
    "linux": ("Linux", "Development Tools & DevOps"),
    "vs code": ("VS Code", "Development Tools & DevOps"),
    "vscode": ("VS Code", "Development Tools & DevOps"),
    "visual studio code": ("VS Code", "Development Tools & DevOps"),
    "aws": ("Amazon Web Services", "Cloud Platforms"),
    "amazon web services": ("Amazon Web Services", "Cloud Platforms"),
    "gcp": ("Google Cloud Platform", "Cloud Platforms"),
    "google cloud": ("Google Cloud Platform", "Cloud Platforms"),
    "google cloud platform": ("Google Cloud Platform", "Cloud Platforms"),
    "azure": ("Microsoft Azure", "Cloud Platforms"),
    "microsoft azure": ("Microsoft Azure", "Cloud Platforms"),
    "ci/cd": ("CI/CD", "Development Tools & DevOps"),
    "cicd": ("CI/CD", "Development Tools & DevOps"),

    # Soft Skills
    "communication": ("Communication", "Professional & Soft Skills"),
    "leadership": ("Leadership", "Professional & Soft Skills"),
    "problem solving": ("Problem Solving", "Professional & Soft Skills"),
    "problem-solving": ("Problem Solving", "Professional & Soft Skills"),
    "teamwork": ("Teamwork", "Professional & Soft Skills"),
    "critical thinking": ("Critical Thinking", "Professional & Soft Skills"),
    "agile": ("Agile Methodologies", "Professional & Soft Skills"),
    "scrum": ("Agile Methodologies", "Professional & Soft Skills"),
}


class SkillNormalizer:
    @classmethod
    def clean_phrase(cls, phrase: str) -> str:
        """
        Strips punctuation, trailing versions (e.g. 'Python 3.10' -> 'python', 'React v18' -> 'react')
        """
        p = phrase.strip().lower()
        # Remove version numbers at the end (e.g. 'python 3.9' -> 'python')
        p = re.sub(r"\s+v?\d+(\.\d+)*$", "", p).strip()
        # Remove common qualifiers
        p = re.sub(r"\s+(?:basics?|fundamentals?|framework|library|programming)$", "", p).strip()
        return p

    @classmethod
    async def normalize_phrase(
        cls,
        raw_phrase: str,
        db: Optional[AsyncSession] = None
    ) -> NormalizedSkillResult:
        """
        Normalizes a raw skill phrase against alias dictionary and canonical database taxonomy.
        """
        if not raw_phrase or not raw_phrase.strip():
            return NormalizedSkillResult(
                original_phrase=raw_phrase,
                canonical_name="Unknown",
                category="General",
                confidence_score=0.0,
                match_type="UNMATCHED"
            )

        cleaned = cls.clean_phrase(raw_phrase)

        # 1. Direct Alias Table Check (O(1) lookup)
        if cleaned in SKILL_ALIASES:
            canonical_name, category = SKILL_ALIASES[cleaned]
            match_type = "EXACT" if raw_phrase.strip().lower() == canonical_name.lower() else "ALIAS"
            score = 1.0 if match_type == "EXACT" else 0.95
            return NormalizedSkillResult(
                original_phrase=raw_phrase,
                canonical_name=canonical_name,
                category=category,
                confidence_score=score,
                match_type=match_type
            )

        # 2. Database Taxonomy Check (if db session provided)
        if db:
            result = await db.execute(
                select(Skill, SkillCategory.name)
                .join(SkillCategory, Skill.category_id == SkillCategory.id, isouter=True)
                .where(
                    (Skill.name.ilike(cleaned)) | 
                    (Skill.slug == cleaned.replace(" ", "-"))
                )
            )
            row = result.first()
            if row:
                skill, cat_name = row
                return NormalizedSkillResult(
                    original_phrase=raw_phrase,
                    canonical_name=skill.name,
                    category=cat_name or "General",
                    confidence_score=0.98,
                    match_type="EXACT"
                )

        # 3. Fuzzy String Similarity Match against known aliases
        all_alias_keys = list(SKILL_ALIASES.keys())
        matches = difflib.get_close_matches(cleaned, all_alias_keys, n=1, cutoff=0.82)
        if matches:
            best_key = matches[0]
            canonical_name, category = SKILL_ALIASES[best_key]
            similarity = difflib.SequenceMatcher(None, cleaned, best_key).ratio()
            return NormalizedSkillResult(
                original_phrase=raw_phrase,
                canonical_name=canonical_name,
                category=category,
                confidence_score=round(similarity * 0.90, 2),
                match_type="FUZZY"
            )

        # 4. Fallback - Title-cased representation
        capitalized = " ".join(word.capitalize() for word in raw_phrase.strip().split())
        return NormalizedSkillResult(
            original_phrase=raw_phrase,
            canonical_name=capitalized,
            category="Technical Skills",
            confidence_score=0.60,
            match_type="UNMATCHED"
        )

    @classmethod
    async def normalize_batch(
        cls,
        phrases: List[str],
        db: Optional[AsyncSession] = None
    ) -> List[NormalizedSkillResult]:
        results = []
        for p in phrases:
            res = await cls.normalize_phrase(p, db=db)
            results.append(res)
        return results
