import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.learning import (
    LearningRoadmap,
    RoadmapMilestone,
    MilestoneResource,
    LearningResource,
    ResourceCategory
)
from app.models.career import CareerRole
from app.models.skill import UserSkill, Skill
from app.services.career_service import CareerService
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.schemas.roadmap import (
    LearningRoadmapResponse,
    MilestoneResponse,
    CuratedResourceItem,
    MilestoneStatusUpdateRequest
)

logger = logging.getLogger(__name__)


class RoadmapService:
    @staticmethod
    async def generate_or_get_roadmap(
        user_id: uuid.UUID,
        career_role_id: uuid.UUID,
        db: AsyncSession,
        force_recreate: bool = False
    ) -> LearningRoadmapResponse:
        # Check if active roadmap exists
        existing_res = await db.execute(
            select(LearningRoadmap)
            .where(
                LearningRoadmap.user_id == user_id,
                LearningRoadmap.career_role_id == career_role_id,
                LearningRoadmap.status == "ACTIVE"
            )
        )
        existing = existing_res.scalar_one_or_none()

        if existing and not force_recreate:
            return await RoadmapService.get_roadmap_by_id(existing.id, db)

        # Archive prior active roadmaps for this role if force_recreate
        if existing and force_recreate:
            existing.status = "ARCHIVED"
            await db.flush()

        # Run career matching to identify actual gaps
        match_data = await CareerService.match_career(user_id, career_role_id, db)
        role_res = await db.execute(select(CareerRole).where(CareerRole.id == career_role_id))
        role = role_res.scalar_one_or_none()
        if not role:
            raise ResourceNotFoundException(f"Career role with id '{career_role_id}' not found.")

        # Also register career goal if not yet active
        await CareerService.set_career_goal(user_id, career_role_id, None, db)

        # Collect missing and weak skill names
        gap_names = [s.skill_name.lower() for s in (match_data.missing_skills + match_data.weak_skills)]

        # Find matching resources in the library
        all_resources_res = await db.execute(select(LearningResource))
        all_resources = all_resources_res.scalars().all()
        res_by_keyword: Dict[str, List[LearningResource]] = {}
        for r in all_resources:
            text = (r.title + " " + (r.content_summary or "")).lower()
            for kw in ["javascript", "react", "html", "css", "python", "fastapi", "postgresql", "docker", "git", "rest api"]:
                if kw in text:
                    res_by_keyword.setdefault(kw, []).append(r)

        # Define 4 structured, progressive milestones
        milestone_templates = [
            {
                "phase": 1,
                "order": 1,
                "title": "Phase 1: Core Engineering Foundations & Clean Code",
                "desc": "Master foundational syntax, modern async paradigms, semantic standards, and version control hygiene.",
                "deliverable_title": "Interactive Vanilla Web App / CLI Utility",
                "deliverable_criteria": "Build a modular application with clean Git commits, unit tests, and comprehensive documentation.",
                "hours": 16,
                "keywords": ["html", "css", "javascript", "git", "python"],
                "status": "IN_PROGRESS"  # First milestone unlocked
            },
            {
                "phase": 2,
                "order": 2,
                "title": "Phase 2: Modern Frontend Architecture & Component State",
                "desc": "Architect component-driven UIs, manage declarative state, optimize renders, and integrate REST endpoints.",
                "deliverable_title": "Responsive Single-Page Application",
                "deliverable_criteria": "Implement stateful dashboard with search, filtering, error boundaries, and accessible UI controls.",
                "hours": 24,
                "keywords": ["react", "javascript", "css"],
                "status": "LOCKED"
            },
            {
                "phase": 3,
                "order": 3,
                "title": "Phase 3: Backend API Architecture & Database Engineering",
                "desc": "Develop secure asynchronous REST services, relational schema models, connection pooling, and caching.",
                "deliverable_title": "Production-Ready REST Service with Persistence",
                "deliverable_criteria": "Create normalized relational schema, JWT authenticated endpoints, and CRUD operations with input validation.",
                "hours": 28,
                "keywords": ["python", "fastapi", "postgresql", "rest api"],
                "status": "LOCKED"
            },
            {
                "phase": 4,
                "order": 4,
                "title": "Phase 4: Containerization, Testing & Capstone Deployment",
                "desc": "Containerize full-stack services with Docker Compose, configure CI testing pipelines, and deploy production builds.",
                "deliverable_title": "Full-Stack Containerized Capstone Platform",
                "deliverable_criteria": "Compose multi-tier web application in Docker, write automated integration tests, and produce deployment runbook.",
                "hours": 20,
                "keywords": ["docker", "fastapi", "react", "postgresql"],
                "status": "LOCKED"
            }
        ]

        # Create Roadmap
        new_roadmap = LearningRoadmap(
            user_id=user_id,
            career_role_id=career_role_id,
            title=f"Personalized Pathway: {role.title}",
            status="ACTIVE",
            version=1,
            total_estimated_hours=sum(m["hours"] for m in milestone_templates),
            progress_percentage=0.0
        )
        db.add(new_roadmap)
        await db.flush()

        # Create Milestones & link resources
        for m_data in milestone_templates:
            ms = RoadmapMilestone(
                roadmap_id=new_roadmap.id,
                phase_number=m_data["phase"],
                order_index=m_data["order"],
                title=m_data["title"],
                description=m_data["desc"],
                deliverable_title=m_data["deliverable_title"],
                deliverable_criteria=m_data["deliverable_criteria"],
                estimated_hours=m_data["hours"],
                status=m_data["status"],
                is_remedial=False
            )
            db.add(ms)
            await db.flush()

            # Attach matching resources
            attached_ids = set()
            display_order = 1
            for kw in m_data["keywords"]:
                for res in res_by_keyword.get(kw, []):
                    if res.id not in attached_ids:
                        mr = MilestoneResource(
                            milestone_id=ms.id,
                            resource_id=res.id,
                            display_order=display_order,
                            is_mandatory=True
                        )
                        db.add(mr)
                        attached_ids.add(res.id)
                        display_order += 1
                        if display_order > 3:
                            break
                if display_order > 3:
                    break

        await db.commit()
        return await RoadmapService.get_roadmap_by_id(new_roadmap.id, db)

    @staticmethod
    async def get_roadmap_by_id(roadmap_id: uuid.UUID, db: AsyncSession) -> LearningRoadmapResponse:
        roadmap_res = await db.execute(
            select(LearningRoadmap)
            .where(LearningRoadmap.id == roadmap_id)
        )
        roadmap = roadmap_res.scalar_one_or_none()
        if not roadmap:
            raise ResourceNotFoundException(f"Roadmap with id '{roadmap_id}' not found.")

        role_res = await db.execute(select(CareerRole).where(CareerRole.id == roadmap.career_role_id))
        role = role_res.scalar_one_or_none()
        role_title = role.title if role else "Target Career"

        # Fetch milestones ordered
        ms_res = await db.execute(
            select(RoadmapMilestone)
            .where(RoadmapMilestone.roadmap_id == roadmap.id)
            .order_by(RoadmapMilestone.order_index)
        )
        milestones = ms_res.scalars().all()

        milestone_responses = []
        for ms in milestones:
            # Fetch attached resources
            r_res = await db.execute(
                select(LearningResource)
                .join(MilestoneResource, MilestoneResource.resource_id == LearningResource.id)
                .where(MilestoneResource.milestone_id == ms.id)
                .order_by(MilestoneResource.display_order)
            )
            resources = r_res.scalars().all()

            curated_list = [
                CuratedResourceItem(
                    id=r.id,
                    title=r.title,
                    url=r.url,
                    resource_type=r.resource_type,
                    provider_name=r.provider_name,
                    rating=r.rating,
                    estimated_minutes=r.estimated_minutes,
                    is_free=r.is_free,
                    content_summary=r.content_summary
                )
                for r in resources
            ]

            milestone_responses.append(MilestoneResponse(
                id=ms.id,
                phase_number=ms.phase_number,
                order_index=ms.order_index,
                title=ms.title,
                description=ms.description,
                deliverable_title=ms.deliverable_title,
                deliverable_criteria=ms.deliverable_criteria,
                estimated_hours=ms.estimated_hours,
                status=ms.status,
                is_remedial=ms.is_remedial,
                resources=curated_list,
                created_at=ms.created_at
            ))

        return LearningRoadmapResponse(
            id=roadmap.id,
            user_id=roadmap.user_id,
            career_role_id=roadmap.career_role_id,
            career_role_title=role_title,
            title=roadmap.title,
            status=roadmap.status,
            version=roadmap.version,
            total_estimated_hours=roadmap.total_estimated_hours,
            progress_percentage=roadmap.progress_percentage,
            milestones=milestone_responses,
            created_at=roadmap.created_at,
            updated_at=roadmap.updated_at
        )

    @staticmethod
    async def get_active_roadmap(user_id: uuid.UUID, db: AsyncSession) -> Optional[LearningRoadmapResponse]:
        roadmap_res = await db.execute(
            select(LearningRoadmap)
            .where(LearningRoadmap.user_id == user_id, LearningRoadmap.status == "ACTIVE")
            .order_by(LearningRoadmap.created_at.desc())
        )
        roadmap = roadmap_res.scalar_one_or_none()
        if not roadmap:
            return None
        return await RoadmapService.get_roadmap_by_id(roadmap.id, db)

    @staticmethod
    async def update_milestone_status(
        user_id: uuid.UUID,
        milestone_id: uuid.UUID,
        new_status: str,
        db: AsyncSession
    ) -> LearningRoadmapResponse:
        ms_res = await db.execute(
            select(RoadmapMilestone)
            .join(LearningRoadmap, RoadmapMilestone.roadmap_id == LearningRoadmap.id)
            .where(
                RoadmapMilestone.id == milestone_id,
                LearningRoadmap.user_id == user_id
            )
        )
        milestone = ms_res.scalar_one_or_none()
        if not milestone:
            raise ResourceNotFoundException(f"Milestone with id '{milestone_id}' not found for user.")

        milestone.status = new_status
        if new_status == "COMPLETED":
            milestone.is_remedial = False
            # Unlock next milestone if locked
            next_res = await db.execute(
                select(RoadmapMilestone)
                .where(
                    RoadmapMilestone.roadmap_id == milestone.roadmap_id,
                    RoadmapMilestone.order_index == milestone.order_index + 1
                )
            )
            next_ms = next_res.scalar_one_or_none()
            if next_ms and next_ms.status == "LOCKED":
                next_ms.status = "IN_PROGRESS"

        # Recalculate roadmap progress
        all_ms_res = await db.execute(
            select(RoadmapMilestone)
            .where(RoadmapMilestone.roadmap_id == milestone.roadmap_id)
        )
        all_milestones = all_ms_res.scalars().all()
        completed_count = sum(1 for m in all_milestones if m.status == "COMPLETED")
        total_count = len(all_milestones)

        roadmap_res = await db.execute(select(LearningRoadmap).where(LearningRoadmap.id == milestone.roadmap_id))
        roadmap = roadmap_res.scalar_one_or_none()
        if roadmap:
            roadmap.progress_percentage = round((completed_count / float(total_count) * 100.0) if total_count > 0 else 0.0, 1)
            if completed_count == total_count and total_count > 0:
                roadmap.status = "COMPLETED"

        await db.commit()
        return await RoadmapService.get_roadmap_by_id(milestone.roadmap_id, db)

    @staticmethod
    async def get_recommended_resources(user_id: uuid.UUID, db: AsyncSession) -> List[CuratedResourceItem]:
        # Fetch user's active goal
        goal = await CareerService.get_active_goal(user_id, db)
        if not goal:
            # Fallback to top rated resources
            res = await db.execute(select(LearningResource).order_by(LearningResource.rating.desc()).limit(6))
            resources = res.scalars().all()
        else:
            match = await CareerService.match_career(user_id, goal.career_role_id, db)
            missing_names = [s.skill_name.lower() for s in match.missing_skills + match.weak_skills]
            
            all_res = await db.execute(select(LearningResource))
            all_list = all_res.scalars().all()
            filtered = []
            for r in all_list:
                text = (r.title + " " + (r.content_summary or "")).lower()
                if any(m in text for m in missing_names):
                    filtered.append(r)
            resources = filtered if filtered else all_list[:6]

        return [
            CuratedResourceItem(
                id=r.id,
                title=r.title,
                url=r.url,
                resource_type=r.resource_type,
                provider_name=r.provider_name,
                rating=r.rating,
                estimated_minutes=r.estimated_minutes,
                is_free=r.is_free,
                content_summary=r.content_summary
            )
            for r in resources
        ]
