import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.career import CareerRole
from app.models.learning import LearningRoadmap, RoadmapMilestone
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentOption
from app.services.career_seeder import CareerSeeder


@pytest.mark.asyncio
async def test_full_12_step_mvp_learner_journey(async_client: AsyncClient):
    """
    Validates the complete 12-step learner journey:
    1. Authenticate user (register & login)
    2. Confirm skills (JavaScript, React, HTML)
    3. Select target career (Full Stack Developer)
    4. Compute skill gap analysis and readiness score
    5. Generate personalized learning roadmap
    6. Verify curated learning resources linked
    7. Fetch milestone assessment quiz
    8. Submit failing assessment (< 70%) -> triggers adaptive replanning & REMEDIAL status
    9. Submit passing assessment (100%) -> updates milestone to COMPLETED, unlocks next milestone
    10. Verify roadmap progress calculation
    11. Verify progress dashboard telemetry
    12. Query AI Career Mentor and verify personalized contextual guidance
    """
    # Step 1: Ensure database is seeded with career roles
    async with AsyncSessionLocal() as session:
        await CareerSeeder.seed_career_data(session)

    # Register and login a unique learner
    user_email = f"learner_{uuid.uuid4().hex[:8]}@example.com"
    user_password = "SecurePassword123!"
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": user_password,
        "full_name": "Demo Learner",
        "role": "STUDENT"
    })
    assert reg_resp.status_code == 201, reg_resp.text

    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": user_password
    })
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Confirm User Skills
    confirm_payload = {
        "custom_skills": [
            {
                "canonical_name": "JavaScript",
                "category": "Web Development",
                "original_phrase": "JavaScript ES6+",
                "proficiency_level": 2,
                "confidence_score": 0.85,
                "evidence": [
                    {
                        "evidence_type": "PROJECT_DEMONSTRATED",
                        "source_section": "Projects",
                        "original_phrase": "JavaScript web app",
                        "description": "Built interactive client scripts",
                        "confidence_score": 0.85
                    }
                ]
            },
            {
                "canonical_name": "React",
                "category": "Web Development",
                "original_phrase": "React.js",
                "proficiency_level": 2,
                "confidence_score": 0.80,
                "evidence": [
                    {
                        "evidence_type": "PROJECT_DEMONSTRATED",
                        "source_section": "Projects",
                        "original_phrase": "React component architecture",
                        "description": "Component rendering",
                        "confidence_score": 0.80
                    }
                ]
            },
            {
                "canonical_name": "HTML",
                "category": "Web Development",
                "original_phrase": "HTML5",
                "proficiency_level": 3,
                "confidence_score": 0.90,
                "evidence": [
                    {
                        "evidence_type": "PROJECT_DEMONSTRATED",
                        "source_section": "Projects",
                        "original_phrase": "Semantic HTML5 layout",
                        "description": "Semantic layout",
                        "confidence_score": 0.90
                    }
                ]
            }
        ]
    }
    confirm_resp = await async_client.post("/api/v1/profiling/confirm", json=confirm_payload, headers=headers)
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirmed_data = confirm_resp.json()
    assert confirmed_data["persisted_count"] == 3

    # Step 3: List Career Roles & Pick "Full Stack Developer"
    roles_resp = await async_client.get("/api/v1/careers/roles", headers=headers)
    assert roles_resp.status_code == 200
    roles = roles_resp.json()
    assert len(roles) >= 1
    fs_role = next((r for r in roles if r["title"] == "Full Stack Developer"), roles[0])
    role_id = fs_role["id"]

    # Select target goal
    goal_resp = await async_client.post(
        "/api/v1/careers/goals",
        json={"career_role_id": role_id},
        headers=headers
    )
    assert goal_resp.status_code == 200
    assert goal_resp.json()["career_role_title"] == "Full Stack Developer"

    # Step 4: Run Skill Gap Analysis & Matching
    match_resp = await async_client.get(f"/api/v1/careers/roles/{role_id}/match", headers=headers)
    assert match_resp.status_code == 200
    match_data = match_resp.json()
    assert "match_percentage" in match_data
    assert match_data["matched_skills_count"] >= 1  # HTML is level 3, requirement is 3
    assert len(match_data["weak_skills"]) >= 1     # JS and React are level 2, requirement is 3
    assert len(match_data["missing_skills"]) >= 1    # Node.js, PostgreSQL, Docker, etc.
    assert match_data["gap_summary"]["role_title"] == "Full Stack Developer"

    # Step 5: Generate Personalized Roadmap
    roadmap_resp = await async_client.post(
        "/api/v1/roadmaps/generate",
        json={"career_role_id": role_id},
        headers=headers
    )
    assert roadmap_resp.status_code == 200
    roadmap_data = roadmap_resp.json()
    assert roadmap_data["title"] == "Personalized Pathway: Full Stack Developer"
    assert len(roadmap_data["milestones"]) == 4
    m1 = roadmap_data["milestones"][0]
    assert m1["order_index"] == 1
    assert m1["status"] == "IN_PROGRESS"
    m2 = roadmap_data["milestones"][1]
    assert m2["status"] == "LOCKED"

    # Step 6: Verify Curated Resources Attached
    assert len(m1["resources"]) >= 1
    assert m1["resources"][0]["is_free"] is True
    assert "http" in m1["resources"][0]["url"]

    # Step 7: Fetch Milestone 1 Assessment Quiz
    quiz_resp = await async_client.get(f"/api/v1/assessments/milestones/{m1['id']}", headers=headers)
    assert quiz_resp.status_code == 200
    quiz_data = quiz_resp.json()
    assert len(quiz_data["questions"]) >= 3
    q1 = quiz_data["questions"][0]
    assert len(q1["options"]) >= 2
    # Ensure is_correct is not leaked in the quiz questions
    assert "is_correct" not in q1["options"][0]

    # Step 8: Adaptive Replanning - Submit Failing Answers (< 70%)
    # Pick the last option for all questions (deliberate wrong answers)
    fail_answers = []
    for q in quiz_data["questions"]:
        fail_answers.append({
            "question_id": q["id"],
            "selected_option_id": q["options"][-1]["id"]
        })

    fail_submit_resp = await async_client.post(
        "/api/v1/assessments/submit",
        json={
            "assessment_id": quiz_data["id"],
            "answers": fail_answers
        },
        headers=headers
    )
    assert fail_submit_resp.status_code == 200
    fail_res = fail_submit_resp.json()
    assert fail_res["passed"] is False
    assert fail_res["status"] == "REMEDIAL_REQUIRED"
    assert "REMEDIAL" in fail_res["adaptive_action"]

    # Verify milestone is now marked REMEDIAL in the active roadmap
    active_rm_resp = await async_client.get("/api/v1/roadmaps/active", headers=headers)
    active_rm = active_rm_resp.json()
    assert active_rm["milestones"][0]["status"] == "REMEDIAL"
    assert active_rm["milestones"][0]["is_remedial"] is True

    # Step 9: Submit Passing Answers (100%)
    async with AsyncSessionLocal() as session:
        correct_answers = []
        for q in quiz_data["questions"]:
            corr_opt = (await session.execute(
                select(AssessmentOption).where(
                    AssessmentOption.question_id == uuid.UUID(q["id"]),
                    AssessmentOption.is_correct == True
                )
            )).scalar_one()
            correct_answers.append({
                "question_id": q["id"],
                "selected_option_id": str(corr_opt.id)
            })

    pass_submit_resp = await async_client.post(
        "/api/v1/assessments/submit",
        json={
            "assessment_id": quiz_data["id"],
            "answers": correct_answers
        },
        headers=headers
    )
    assert pass_submit_resp.status_code == 200
    pass_res = pass_submit_resp.json()
    assert pass_res["passed"] is True
    assert pass_res["percentage"] == 100.0
    assert pass_res["status"] == "PASSED"

    # Step 10: Verify Milestone 1 COMPLETED and Milestone 2 UNLOCKED to IN_PROGRESS
    active_rm_resp2 = await async_client.get("/api/v1/roadmaps/active", headers=headers)
    active_rm2 = active_rm_resp2.json()
    assert active_rm2["milestones"][0]["status"] == "COMPLETED"
    assert active_rm2["milestones"][1]["status"] == "IN_PROGRESS"
    assert active_rm2["progress_percentage"] == 25.0  # 1 of 4 completed = 25%

    # Step 11: Progress Dashboard Telemetry
    progress_resp = await async_client.get("/api/v1/assessments/progress/summary", headers=headers)
    assert progress_resp.status_code == 200
    prog = progress_resp.json()
    assert prog["target_career_title"] == "Full Stack Developer"
    assert prog["confirmed_skills_count"] == 3
    assert prog["roadmap_progress_percentage"] == 25.0
    assert prog["completed_milestones_count"] == 1
    assert prog["total_milestones_count"] == 4
    assert prog["assessments_taken_count"] >= 2
    assert prog["assessments_passed_count"] >= 1

    # Step 12: AI Mentor Contextual Mentorship
    mentor_resp = await async_client.post(
        "/api/v1/mentor/chat",
        json={"message": "What should I focus on next for my career?"},
        headers=headers
    )
    assert mentor_resp.status_code == 200
    mentor_data = mentor_resp.json()
    assert len(mentor_data["reply"]) > 20
    assert mentor_data["active_role"] == "Full Stack Developer"

    # Check conversation history
    history_resp = await async_client.get("/api/v1/mentor/history", headers=headers)
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert len(history_data["messages"]) >= 2
