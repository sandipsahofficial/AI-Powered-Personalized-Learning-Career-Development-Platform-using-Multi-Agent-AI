import pytest
import uuid
from app.models.skill import SkillCategory, Skill
from app.db.session import AsyncSessionLocal


@pytest.mark.asyncio
async def test_skills_catalog_and_user_skills(async_client):
    # Seed a category and skill directly in DB for testing
    category_name = f"Backend Development {uuid.uuid4().hex[:6]}"
    skill_name = f"Python Programming {uuid.uuid4().hex[:4]}"
    
    async with AsyncSessionLocal() as session:
        cat = SkillCategory(name=category_name, description="Server-side programming")
        session.add(cat)
        await session.flush()
        
        skill = Skill(category_id=cat.id, name=skill_name, slug=skill_name.lower().replace(" ", "-"))
        session.add(skill)
        await session.commit()
        skill_id = str(skill.id)

    # 1. List categories
    res_cats = await async_client.get("/api/v1/skills/categories")
    assert res_cats.status_code == 200
    categories = res_cats.json()
    assert any(c["name"] == category_name for c in categories)

    # 2. Search skills catalog
    res_skills = await async_client.get(f"/api/v1/skills?search={skill_name}")
    assert res_skills.status_code == 200
    skills = res_skills.json()
    assert any(s["name"] == skill_name for s in skills)

    # 3. Register user and add skill to profile
    email = f"skill_user_{uuid.uuid4().hex[:8]}@example.com"
    pw = "SkillPassword123!"
    await async_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pw,
        "full_name": "Skill Tester",
        "role": "STUDENT"
    })
    res_login = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add skill
    res_add = await async_client.post("/api/v1/skills/me", headers=headers, json={
        "skill_id": skill_id,
        "proficiency_level": 2
    })
    assert res_add.status_code == 200
    added = res_add.json()
    assert added["skill_id"] == skill_id
    assert added["proficiency_level"] == 2

    # List my skills
    res_my_skills = await async_client.get("/api/v1/skills/me", headers=headers)
    assert res_my_skills.status_code == 200
    my_skills = res_my_skills.json()
    assert len(my_skills) == 1
    assert my_skills[0]["skill_id"] == skill_id

    # Update skill proficiency
    res_update = await async_client.patch(f"/api/v1/skills/me/{skill_id}", headers=headers, json={
        "proficiency_level": 3
    })
    assert res_update.status_code == 200
    assert res_update.json()["proficiency_level"] == 3

    # Remove skill
    res_del = await async_client.delete(f"/api/v1/skills/me/{skill_id}", headers=headers)
    assert res_del.status_code == 200

    # Verify skill removed
    res_empty = await async_client.get("/api/v1/skills/me", headers=headers)
    assert len(res_empty.json()) == 0
