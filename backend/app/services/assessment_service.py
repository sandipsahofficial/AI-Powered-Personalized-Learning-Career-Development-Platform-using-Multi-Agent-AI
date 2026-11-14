import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.assessment import (
    Assessment,
    AssessmentQuestion,
    AssessmentOption,
    AssessmentAttempt,
    AssessmentAnswer,
    AssessmentResult
)
from app.models.learning import RoadmapMilestone, LearningRoadmap
from app.models.ai import AdaptiveReplanningEvent
from app.models.career import UserCareerGoal, CareerRole, CareerMatchingResult
from app.models.skill import UserSkill
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.schemas.assessment import (
    AssessmentDetailResponse,
    AssessmentQuestionItem,
    AssessmentOptionItem,
    AssessmentSubmissionRequest,
    AssessmentResultResponse,
    ProgressSummaryResponse
)
from app.services.roadmap_service import RoadmapService
from app.services.career_service import CareerService

logger = logging.getLogger(__name__)

MILESTONE_QUIZ_TEMPLATES = {
    1: {
        "title": "Phase 1: Core Web & Modern JavaScript Proficiency Check",
        "questions": [
            {
                "question": "What is the primary difference between 'let' and 'const' in modern JavaScript?",
                "points": 1.0,
                "options": [
                    ("Variables declared with 'let' can be reassigned, while 'const' identifiers cannot be reassigned.", True, "Correct. 'const' creates an immutable binding, though mutable objects may have properties modified."),
                    ("'let' is hoisted to the top of its scope, but 'const' is not hoisted.", False, "Both let and const are hoisted to the temporal dead zone."),
                    ("'const' has global scope, while 'let' only has function scope.", False, "Both let and const are block-scoped."),
                    ("'let' is deprecated in favor of 'var'.", False, "'var' is legacy; 'let' and 'const' are modern standard.")
                ]
            },
            {
                "question": "Which array method returns a new array with all elements that pass a test condition without mutating the original array?",
                "points": 1.0,
                "options": [
                    ("Array.prototype.filter()", True, "Correct. filter() performs a pure functional subset selection."),
                    ("Array.prototype.splice()", False, "splice() mutates the array in-place."),
                    ("Array.prototype.forEach()", False, "forEach() executes side effects and returns undefined."),
                    ("Array.prototype.push()", False, "push() adds elements to the end and returns length.")
                ]
            },
            {
                "question": "What does the JavaScript Event Loop do when handling asynchronous operations like fetch() or setTimeout()?",
                "points": 1.0,
                "options": [
                    ("It continuously monitors the Call Stack and moves callbacks from the Microtask/Callback Queue once the stack is empty.", True, "Correct. The event loop prioritizes synchronous execution stack before dequeuing callbacks."),
                    ("It spawns a new OS thread for every asynchronous function.", False, "JavaScript runs on a single-threaded event-driven concurrency model."),
                    ("It halts script execution until the network request finishes.", False, "Non-blocking I/O ensures script execution continues."),
                    ("It compiles JavaScript directly into machine bytecode at runtime.", False, "That is handled by the JIT compiler, not the event loop.")
                ]
            }
        ]
    },
    2: {
        "title": "Phase 2: React Component Architecture & State Management",
        "questions": [
            {
                "question": "Why should you never mutate state directly in React (e.g., state.count = 5)?",
                "points": 1.0,
                "options": [
                    ("Direct mutation skips React's reconciliation engine and fails to trigger a re-render.", True, "Correct. React relies on reference equality to schedule virtual DOM diffs and renders."),
                    ("Direct mutation causes immediate memory leaks in the browser.", False, "It causes stale UI bugs rather than OS memory corruption."),
                    ("React will automatically throw a syntax error in the browser console.", False, "JS allows object mutation; React simply won't know to re-render."),
                    ("Direct mutation is only forbidden in class components, not functional components.", False, "State immutability is required in all React components.")
                ]
            },
            {
                "question": "What is the purpose of the dependency array in useEffect(callback, [deps])?",
                "points": 1.0,
                "options": [
                    ("It instructs React to execute the effect only when specified values change between renders.", True, "Correct. Passing an empty array executes the effect only on mount."),
                    ("It imports external npm libraries into the component.", False, "Imports are declared at the top of the file."),
                    ("It binds Redux actions to the component props.", False, "useEffect is a native React Hook independent of Redux."),
                    ("It forces the component to unmount when dependencies change.", False, "It runs cleanup and the next effect cycle.")
                ]
            },
            {
                "question": "When should React Context be preferred over local state or external state management libraries?",
                "points": 1.0,
                "options": [
                    ("For low-frequency global data such as authenticated user context, theme settings, or locale preferences.", True, "Correct. Context avoids prop-drilling for stable global configuration."),
                    ("For high-frequency state updates like form input keystrokes or 60fps animations.", False, "Frequent Context updates cause broad subtree re-renders."),
                    ("To replace database migrations on the backend.", False, "Context is strictly a client-side React UI feature."),
                    ("Whenever a component has more than two child components.", False, "Local state should remain localized whenever practical.")
                ]
            }
        ]
    },
    3: {
        "title": "Phase 3: Backend REST APIs & Relational Database Engineering",
        "questions": [
            {
                "question": "What is the primary benefit of using database connection pooling in an asynchronous web framework like FastAPI?",
                "points": 1.0,
                "options": [
                    ("It reuses active database connections, eliminating the high TCP handshake and authentication overhead per request.", True, "Correct. Connection pooling significantly increases throughput and prevents connection exhaustion."),
                    ("It encrypts all database passwords stored in plaintext in the table.", False, "Pooling manages connection lifecycle, not column encryption."),
                    ("It automatically creates indexes on all foreign key columns.", False, "Indexes must be declared explicitly in migrations or DDL."),
                    ("It replaces the need for SQL queries altogether.", False, "SQL or ORM queries are still executed through pooled connections.")
                ]
            },
            {
                "question": "Which HTTP status code should a REST API return when a client provides malformed or invalid JSON input?",
                "points": 1.0,
                "options": [
                    ("422 Unprocessable Entity or 400 Bad Request", True, "Correct. 422 is standard for schema validation errors in FastAPI/Pydantic."),
                    ("500 Internal Server Error", False, "500 indicates unhandled server faults, not client validation issues."),
                    ("401 Unauthorized", False, "401 indicates missing or invalid credentials."),
                    ("404 Not Found", False, "404 indicates missing endpoint or resource.")
                ]
            },
            {
                "question": "In PostgreSQL, what is the primary role of a foreign key constraint with ON DELETE CASCADE?",
                "points": 1.0,
                "options": [
                    ("When a parent row is deleted, all associated child rows referencing it are automatically removed.", True, "Correct. ON DELETE CASCADE maintains referential integrity by cleaning orphan records."),
                    ("It prevents any records from ever being deleted from the parent table.", False, "That is ON DELETE RESTRICT or NO ACTION."),
                    ("It cascades password hashing to all user accounts.", False, "Foreign keys govern relational integrity, not authentication hashing."),
                    ("It converts SQL queries into GraphQL queries.", False, "Constraints are relational database primitives.")
                ]
            }
        ]
    },
    4: {
        "title": "Phase 4: Containerization & Cloud Deployment Architecture",
        "questions": [
            {
                "question": "Why is multi-stage Docker builds recommended for production deployments?",
                "points": 1.0,
                "options": [
                    ("They isolate build tools and compilers from the final image, yielding significantly smaller and more secure images.", True, "Correct. Only the compiled artifact and runtime dependencies are copied into the lean final image."),
                    ("They allow Docker containers to run without an operating system kernel.", False, "Containers always leverage the host OS kernel."),
                    ("They automatically deploy images directly to Kubernetes without a registry.", False, "Images must still be tagged and pushed to a registry."),
                    ("They bypass port exposure requirements.", False, "Exposed ports must still be configured.")
                ]
            },
            {
                "question": "What is the purpose of Docker Compose in a local development environment?",
                "points": 1.0,
                "options": [
                    ("To declaratively define, configure, and orchestrate multi-container services with shared networking and volumes.", True, "Correct. Compose simplifies running frontend, backend, database, and cache together."),
                    ("To compile Python code directly into C binaries.", False, "Docker Compose is an orchestration tool, not a compiler."),
                    ("To replace Git as a version control system.", False, "Docker Compose manages runtime infrastructure."),
                    ("To provide free cloud hosting on AWS.", False, "Compose runs containers on the local Docker daemon.")
                ]
            },
            {
                "question": "In production architectures, why should database credentials and API secret keys never be baked into Dockerfiles?",
                "points": 1.0,
                "options": [
                    ("Baked secrets persist in the image layer history and can be exposed if the image is pushed or inspected.", True, "Correct. Secrets should be injected at runtime via environment variables or secret managers."),
                    ("Docker will fail to compile any image that contains string variables.", False, "Docker permits ENV strings, which is why it is an architectural vulnerability."),
                    ("Databases automatically reject connections from containerized apps.", False, "Databases accept valid connections regardless of containerization."),
                    ("It causes CPU utilization to spike to 100%.", False, "It is a critical security vulnerability, not a CPU issue.")
                ]
            }
        ]
    }
}


class AssessmentService:
    @staticmethod
    async def get_or_create_milestone_assessment(milestone_id: uuid.UUID, db: AsyncSession) -> AssessmentDetailResponse:
        # Check if assessment exists
        ms_res = await db.execute(select(RoadmapMilestone).where(RoadmapMilestone.id == milestone_id))
        milestone = ms_res.scalar_one_or_none()
        if not milestone:
            raise ResourceNotFoundException(f"Milestone with id '{milestone_id}' not found.")

        assess_res = await db.execute(select(Assessment).where(Assessment.milestone_id == milestone_id))
        assessment = assess_res.scalar_one_or_none()

        if not assessment:
            # Create standard assessment based on phase number
            phase_num = milestone.phase_number if milestone.phase_number in MILESTONE_QUIZ_TEMPLATES else 1
            template = MILESTONE_QUIZ_TEMPLATES[phase_num]

            assessment = Assessment(
                milestone_id=milestone_id,
                title=f"{milestone.title}: Competency Assessment",
                assessment_type="QUIZ",
                passing_score=70.0,
                time_limit_minutes=15
            )
            db.add(assessment)
            await db.flush()

            for idx, q_data in enumerate(template["questions"], start=1):
                question = AssessmentQuestion(
                    assessment_id=assessment.id,
                    question_text=q_data["question"],
                    question_type="MCQ",
                    points=q_data["points"],
                    order_index=idx
                )
                db.add(question)
                await db.flush()

                for opt_text, is_corr, explanation in q_data["options"]:
                    option = AssessmentOption(
                        question_id=question.id,
                        option_text=opt_text,
                        is_correct=is_corr,
                        explanation=explanation
                    )
                    db.add(option)

            await db.commit()
            await db.refresh(assessment)

        # Build response with questions and options (without is_correct revealed)
        q_res = await db.execute(
            select(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment.id)
            .order_by(AssessmentQuestion.order_index)
        )
        questions = q_res.scalars().all()

        question_items = []
        for q in questions:
            opt_res = await db.execute(
                select(AssessmentOption)
                .where(AssessmentOption.question_id == q.id)
            )
            options = opt_res.scalars().all()
            opt_items = [
                AssessmentOptionItem(id=o.id, option_text=o.option_text)
                for o in options
            ]
            question_items.append(AssessmentQuestionItem(
                id=q.id,
                question_text=q.question_text,
                points=q.points,
                order_index=q.order_index,
                options=opt_items
            ))

        return AssessmentDetailResponse(
            id=assessment.id,
            milestone_id=milestone.id,
            milestone_title=milestone.title,
            title=assessment.title,
            passing_score=assessment.passing_score,
            time_limit_minutes=assessment.time_limit_minutes,
            questions=question_items
        )

    @staticmethod
    async def submit_assessment(
        user_id: uuid.UUID,
        request: AssessmentSubmissionRequest,
        db: AsyncSession
    ) -> AssessmentResultResponse:
        assess_res = await db.execute(select(Assessment).where(Assessment.id == request.assessment_id))
        assessment = assess_res.scalar_one_or_none()
        if not assessment:
            raise ResourceNotFoundException(f"Assessment with id '{request.assessment_id}' not found.")

        ms_res = await db.execute(select(RoadmapMilestone).where(RoadmapMilestone.id == assessment.milestone_id))
        milestone = ms_res.scalar_one_or_none()
        if not milestone:
            raise ResourceNotFoundException("Milestone linked to assessment not found.")

        # Load all questions and options with correctness
        q_res = await db.execute(
            select(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment.id)
        )
        questions = q_res.scalars().all()
        q_map = {q.id: q for q in questions}

        opt_res = await db.execute(
            select(AssessmentOption)
            .join(AssessmentQuestion, AssessmentOption.question_id == AssessmentQuestion.id)
            .where(AssessmentQuestion.assessment_id == assessment.id)
        )
        options = opt_res.scalars().all()
        opt_map = {o.id: o for o in options}

        answers_given = {a.question_id: a.selected_option_id for a in request.answers}

        total_points = sum(q.points for q in questions)
        earned_points = 0.0

        now_utc = datetime.now(timezone.utc)
        attempt = AssessmentAttempt(
            assessment_id=assessment.id,
            user_id=user_id,
            started_at=now_utc,
            submitted_at=now_utc,
            status="GRADED"
        )
        db.add(attempt)
        await db.flush()

        for q in questions:
            sel_opt_id = answers_given.get(q.id)
            is_correct = False
            awarded = 0.0
            if sel_opt_id and sel_opt_id in opt_map:
                opt = opt_map[sel_opt_id]
                if opt.is_correct:
                    is_correct = True
                    awarded = q.points
                    earned_points += awarded

            answer_record = AssessmentAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option_id=sel_opt_id,
                is_correct=is_correct,
                awarded_points=awarded
            )
            db.add(answer_record)

        percentage = round((earned_points / total_points * 100.0) if total_points > 0 else 0.0, 1)
        passed = percentage >= assessment.passing_score

        # Feedback & Adaptive Replanning
        if passed:
            feedback = (
                f"Outstanding performance! You scored {percentage}% ({earned_points}/{total_points} pts). "
                f"You have demonstrated proficiency in '{milestone.title}' and are cleared to advance to the next milestone."
            )
            adaptive_action = "MILESTONE_UNLOCKED: Next milestone activated in your roadmap."
            # Complete milestone and unlock next
            await RoadmapService.update_milestone_status(user_id, milestone.id, "COMPLETED", db)
        else:
            feedback = (
                f"Assessment score: {percentage}% ({earned_points}/{total_points} pts). Passing threshold is {assessment.passing_score}%. "
                f"Gaps identified in core competencies. The AI replanner has flagged '{milestone.title}' for targeted remedial revision."
            )
            adaptive_action = "ADAPTIVE_REPLANNING: Milestone transitioned to REMEDIAL. Review curated documentation before retesting."
            # Set milestone to REMEDIAL
            milestone.status = "REMEDIAL"
            milestone.is_remedial = True

            # Record Adaptive Replanning Event
            ms_count_res = await db.execute(
                select(func.count(RoadmapMilestone.id))
                .where(RoadmapMilestone.roadmap_id == milestone.roadmap_id)
            )
            ms_count = ms_count_res.scalar() or 4

            replan_event = AdaptiveReplanningEvent(
                roadmap_id=milestone.roadmap_id,
                trigger_reason="ASSESSMENT_FAILURE",
                prior_milestone_count=ms_count,
                new_milestone_count=ms_count,
                replanned_at=now_utc
            )
            db.add(replan_event)

        result = AssessmentResult(
            attempt_id=attempt.id,
            user_id=user_id,
            total_score=earned_points,
            max_score=total_points,
            percentage=percentage,
            passed=passed,
            ai_evaluator_feedback=feedback,
            evaluated_at=now_utc
        )
        db.add(result)
        await db.commit()

        return AssessmentResultResponse(
            attempt_id=attempt.id,
            assessment_id=assessment.id,
            milestone_id=milestone.id,
            total_score=earned_points,
            max_score=total_points,
            percentage=percentage,
            passed=passed,
            status="PASSED" if passed else "REMEDIAL_REQUIRED",
            ai_evaluator_feedback=feedback,
            adaptive_action=adaptive_action,
            evaluated_at=now_utc
        )

    @staticmethod
    async def get_progress_summary(user_id: uuid.UUID, db: AsyncSession) -> ProgressSummaryResponse:
        # Active Goal & Match
        goal = await CareerService.get_active_goal(user_id, db)
        career_title = goal.career_role_title if goal else None
        readiness_pct = goal.match_percentage if (goal and goal.match_percentage is not None) else 0.0

        # Confirmed Skills Count
        skills_res = await db.execute(
            select(func.count(UserSkill.id)).where(UserSkill.user_id == user_id)
        )
        skills_count = skills_res.scalar() or 0

        # Active Roadmap
        roadmap_res = await db.execute(
            select(LearningRoadmap)
            .where(LearningRoadmap.user_id == user_id, LearningRoadmap.status == "ACTIVE")
            .order_by(LearningRoadmap.created_at.desc())
        )
        roadmap = roadmap_res.scalar_one_or_none()

        roadmap_title = roadmap.title if roadmap else None
        roadmap_pct = roadmap.progress_percentage if roadmap else 0.0

        total_ms = 0
        comp_ms = 0
        if roadmap:
            ms_res = await db.execute(
                select(RoadmapMilestone)
                .where(RoadmapMilestone.roadmap_id == roadmap.id)
            )
            milestones = ms_res.scalars().all()
            total_ms = len(milestones)
            comp_ms = sum(1 for m in milestones if m.status == "COMPLETED")

        # Assessment Stats
        results_res = await db.execute(
            select(AssessmentResult)
            .where(AssessmentResult.user_id == user_id)
            .order_by(AssessmentResult.evaluated_at.desc())
        )
        results = results_res.scalars().all()
        taken_count = len(results)
        passed_count = sum(1 for r in results if r.passed)

        recent_res = None
        if results:
            latest = results[0]
            # Find linked milestone
            attempt_res = await db.execute(
                select(AssessmentAttempt, Assessment)
                .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
                .where(AssessmentAttempt.id == latest.attempt_id)
            )
            row = attempt_res.first()
            milestone_id = row[1].milestone_id if row else uuid.uuid4()
            assessment_id = row[1].id if row else uuid.uuid4()

            recent_res = AssessmentResultResponse(
                attempt_id=latest.attempt_id,
                assessment_id=assessment_id,
                milestone_id=milestone_id,
                total_score=latest.total_score,
                max_score=latest.max_score,
                percentage=latest.percentage,
                passed=latest.passed,
                status="PASSED" if latest.passed else "REMEDIAL_REQUIRED",
                ai_evaluator_feedback=latest.ai_evaluator_feedback or "",
                evaluated_at=latest.evaluated_at
            )

        return ProgressSummaryResponse(
            user_id=user_id,
            target_career_title=career_title,
            readiness_percentage=readiness_pct,
            confirmed_skills_count=skills_count,
            active_roadmap_title=roadmap_title,
            roadmap_progress_percentage=roadmap_pct,
            completed_milestones_count=comp_ms,
            total_milestones_count=total_ms,
            assessments_taken_count=taken_count,
            assessments_passed_count=passed_count,
            recent_assessment=recent_res
        )
