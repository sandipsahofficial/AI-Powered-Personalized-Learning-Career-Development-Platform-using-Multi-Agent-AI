import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.redis import redis_manager
from app.models.user import User, UserProfile
from app.models.skill import Skill, SkillCategory, UserSkill
from app.schemas.profiling import (
    DocumentUploadResponse,
    ProfilePreviewResponse,
    ExtractedSkillItem,
    SkillReviewUpdateRequest,
    ProfileConfirmRequest,
    ProfileConfirmResponse,
    ProfilingStatusResponse
)
from app.services.document_parser import DocumentParser
from app.services.skill_seeder import SkillSeeder
from app.services.skill_normalizer import SkillNormalizer
from app.agents.profiler_agent import ProfilerAgent

logger = logging.getLogger(__name__)

# Redis Cache Keys
REDIS_RESUME_PREFIX = "profiling:resume:"
REDIS_PREVIEW_PREFIX = "profiling:preview:"
CACHE_TTL_SECONDS = 86400  # 24 Hours

# In-memory fallback if Redis connection is not established
_LOCAL_RESUME_STORE: Dict[str, Dict[str, Any]] = {}
_LOCAL_PREVIEW_STORE: Dict[str, Dict[str, Any]] = {}


class ProfilingService:
    @classmethod
    async def process_and_cache_resume(
        cls,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str = ""
    ) -> DocumentUploadResponse:
        parsed_doc = DocumentParser.parse_document(filename, content, content_type)

        cache_data = {
            "filename": parsed_doc.filename,
            "file_type": parsed_doc.file_type,
            "size_bytes": parsed_doc.size_bytes,
            "char_count": parsed_doc.char_count,
            "sections": [s.model_dump() for s in parsed_doc.sections],
            "upload_timestamp": parsed_doc.upload_timestamp.isoformat(),
            "extracted_text_preview": parsed_doc.extracted_text_preview
        }

        # Cache in Redis with local fallback
        user_key = f"{REDIS_RESUME_PREFIX}{str(user_id)}"
        try:
            if redis_manager.is_connected:
                await redis_manager.client.setex(user_key, CACHE_TTL_SECONDS, json.dumps(cache_data))
            else:
                _LOCAL_RESUME_STORE[str(user_id)] = cache_data
        except Exception as e:
            logger.warning("Redis caching failed, using local store: %s", str(e))
            _LOCAL_RESUME_STORE[str(user_id)] = cache_data

        return parsed_doc

    @classmethod
    async def get_cached_resume(cls, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        user_key = f"{REDIS_RESUME_PREFIX}{str(user_id)}"
        try:
            if redis_manager.is_connected:
                raw = await redis_manager.client.get(user_key)
                if raw:
                    return json.loads(raw)
        except Exception:
            pass
        return _LOCAL_RESUME_STORE.get(str(user_id))

    @classmethod
    async def extract_and_preview(
        cls,
        user_id: uuid.UUID,
        raw_text: Optional[str] = None,
        use_cached_resume: bool = True,
        target_role: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> ProfilePreviewResponse:
        # Seed canonical taxonomy if not seeded
        if db:
            await SkillSeeder.seed_canonical_skills(db)

        sections = []
        full_text = ""

        if use_cached_resume:
            cached_doc = await cls.get_cached_resume(user_id)
            if cached_doc and "sections" in cached_doc:
                from app.schemas.profiling import DocumentSection
                for s in cached_doc["sections"]:
                    sections.append(DocumentSection(
                        title=s["title"],
                        content=s["content"],
                        char_count=s["char_count"]
                    ))
                full_text = "\n\n".join(s.content for s in sections)

        if not full_text and raw_text:
            cleaned = DocumentParser.sanitize_and_clean_text(raw_text)
            sections = DocumentParser.segment_sections(cleaned)
            full_text = cleaned

        if not full_text:
            # Empty fallback preview
            return ProfilePreviewResponse(
                user_id=user_id,
                extracted_skills=[],
                total_skills_count=0,
                categories_breakdown={},
                ai_model_used="none",
                is_fallback=True,
                extraction_timestamp=datetime.now(timezone.utc),
                document_summary={"headline": "No document uploaded", "summary": "Please upload a resume or provide profile text."}
            )

        preview = await ProfilerAgent.extract_skills(
            user_id=user_id,
            sections=sections,
            full_text=full_text,
            db=db,
            target_role=target_role
        )

        # Cache preview
        await cls._save_preview(user_id, preview)
        return preview

    @classmethod
    async def _save_preview(cls, user_id: uuid.UUID, preview: ProfilePreviewResponse) -> None:
        user_key = f"{REDIS_PREVIEW_PREFIX}{str(user_id)}"
        data_str = preview.model_dump_json()
        try:
            if redis_manager.is_connected:
                await redis_manager.client.setex(user_key, CACHE_TTL_SECONDS, data_str)
            else:
                _LOCAL_PREVIEW_STORE[str(user_id)] = json.loads(data_str)
        except Exception:
            _LOCAL_PREVIEW_STORE[str(user_id)] = json.loads(data_str)

    @classmethod
    async def get_preview(cls, user_id: uuid.UUID) -> Optional[ProfilePreviewResponse]:
        user_key = f"{REDIS_PREVIEW_PREFIX}{str(user_id)}"
        data = None
        try:
            if redis_manager.is_connected:
                raw = await redis_manager.client.get(user_key)
                if raw:
                    data = json.loads(raw)
        except Exception:
            pass

        if not data:
            data = _LOCAL_PREVIEW_STORE.get(str(user_id))

        if data:
            return ProfilePreviewResponse.model_validate(data)
        return None

    @classmethod
    async def update_extracted_skill(
        cls,
        user_id: uuid.UUID,
        skill_id: str,
        update_data: SkillReviewUpdateRequest
    ) -> Optional[ExtractedSkillItem]:
        preview = await cls.get_preview(user_id)
        if not preview:
            return None

        target_skill = None
        for skill in preview.extracted_skills:
            if skill.id == skill_id:
                if update_data.proficiency_level is not None:
                    skill.proficiency_level = update_data.proficiency_level
                    skill.proficiency_status = "USER_OVERRIDDEN"
                if update_data.is_confirmed is not None:
                    skill.is_confirmed = update_data.is_confirmed
                if update_data.is_rejected is not None:
                    skill.is_rejected = update_data.is_rejected
                if update_data.user_notes is not None:
                    skill.user_notes = update_data.user_notes
                target_skill = skill
                break

        if target_skill:
            await cls._save_preview(user_id, preview)

        return target_skill

    @classmethod
    async def confirm_and_persist_skills(
        cls,
        user_id: uuid.UUID,
        confirm_data: ProfileConfirmRequest,
        db: AsyncSession
    ) -> ProfileConfirmResponse:
        preview = await cls.get_preview(user_id)
        skills_to_persist: List[ExtractedSkillItem] = []

        if preview:
            confirmed_set = set(confirm_data.confirmed_skill_ids or [])
            for s in preview.extracted_skills:
                # If specific IDs provided, match them; otherwise take all unrejected
                if confirmed_set:
                    if s.id in confirmed_set and not s.is_rejected:
                        skills_to_persist.append(s)
                elif not s.is_rejected:
                    skills_to_persist.append(s)

        if confirm_data.custom_skills:
            skills_to_persist.extend(confirm_data.custom_skills)

        # Make sure taxonomy exists
        await SkillSeeder.seed_canonical_skills(db)

        persisted_count = 0
        updated_count = 0

        for item in skills_to_persist:
            # 1. Resolve or create Skill entity in taxonomy
            skill_res = await db.execute(select(Skill).where(Skill.name.ilike(item.canonical_name)))
            skill_entity = skill_res.scalar_one_or_none()

            if not skill_entity:
                # Resolve category
                cat_res = await db.execute(select(SkillCategory).where(SkillCategory.name == item.category))
                cat_entity = cat_res.scalar_one_or_none()
                if not cat_entity:
                    cat_entity = SkillCategory(name=item.category, description="Discovered Category")
                    db.add(cat_entity)
                    await db.flush()

                slug = item.canonical_name.lower().replace(" ", "-")
                skill_entity = Skill(
                    category_id=cat_entity.id,
                    name=item.canonical_name,
                    slug=slug,
                    description=f"Skill: {item.canonical_name}"
                )
                db.add(skill_entity)
                await db.flush()

            # 2. Check existing UserSkill
            user_skill_res = await db.execute(
                select(UserSkill).where(
                    UserSkill.user_id == user_id,
                    UserSkill.skill_id == skill_entity.id
                )
            )
            existing_user_skill = user_skill_res.scalar_one_or_none()

            # Map 1-5 scale to DB 1-4 scale (1->1, 2->2, 3->3, 4/5->4)
            db_level = min(4, max(1, item.proficiency_level or 2))

            if existing_user_skill:
                existing_user_skill.proficiency_level = db_level
                existing_user_skill.confidence_score = item.confidence_score
                existing_user_skill.source = "AI_EXTRACTED_USER_CONFIRMED"
                existing_user_skill.last_assessed_at = datetime.now(timezone.utc)
                updated_count += 1
            else:
                new_user_skill = UserSkill(
                    user_id=user_id,
                    skill_id=skill_entity.id,
                    proficiency_level=db_level,
                    confidence_score=item.confidence_score,
                    is_verified=False,
                    source="AI_EXTRACTED_USER_CONFIRMED",
                    last_assessed_at=datetime.now(timezone.utc)
                )
                db.add(new_user_skill)
                persisted_count += 1

        # 3. Update User Profile resume text and headline if summary available
        if preview and preview.document_summary:
            prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
            user_prof = prof_res.scalar_one_or_none()
            if user_prof:
                headline = preview.document_summary.get("headline")
                if headline and not user_prof.headline:
                    user_prof.headline = headline[:250]
                cached_resume = await cls.get_cached_resume(user_id)
                if cached_resume and cached_resume.get("extracted_text_preview"):
                    user_prof.raw_resume_text = cached_resume.get("extracted_text_preview")[:2000]

        await db.commit()

        # Count total skills in profile
        total_res = await db.execute(select(UserSkill).where(UserSkill.user_id == user_id))
        total_count = len(total_res.scalars().all())

        return ProfileConfirmResponse(
            user_id=user_id,
            persisted_count=persisted_count,
            updated_count=updated_count,
            total_skills_in_profile=total_count,
            status="CONFIRMED",
            message=f"Successfully confirmed and persisted {persisted_count + updated_count} skills into profile."
        )

    @classmethod
    async def get_profiling_status(cls, user_id: uuid.UUID, db: AsyncSession) -> ProfilingStatusResponse:
        cached_resume = await cls.get_cached_resume(user_id)
        preview = await cls.get_preview(user_id)

        # Count persisted skills in DB
        db_skills_res = await db.execute(select(UserSkill).where(UserSkill.user_id == user_id))
        persisted_skills = db_skills_res.scalars().all()

        total_preview = len(preview.extracted_skills) if preview else 0
        confirmed_count = sum(1 for s in preview.extracted_skills if s.is_confirmed) if preview else 0
        pending_count = sum(1 for s in preview.extracted_skills if not s.is_confirmed and not s.is_rejected) if preview else 0

        return ProfilingStatusResponse(
            has_uploaded_resume=cached_resume is not None,
            last_uploaded_filename=cached_resume.get("filename") if cached_resume else None,
            last_extracted_at=preview.extraction_timestamp if preview else None,
            total_skills_in_preview=total_preview,
            confirmed_skills_count=confirmed_count,
            pending_review_count=pending_count,
            total_persisted_skills=len(persisted_skills)
        )
