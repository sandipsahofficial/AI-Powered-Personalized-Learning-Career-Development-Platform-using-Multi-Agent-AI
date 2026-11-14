import pytest
import uuid


@pytest.mark.asyncio
async def test_rbac_unauthenticated_blocked(async_client):
    res = await async_client.get("/api/v1/users")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_rbac_student_forbidden_from_admin_endpoints(async_client):
    email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    password = "StudentPassword123!"

    # Register as STUDENT
    await async_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Student User",
        "role": "STUDENT"
    })

    # Login
    res_login = await async_client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Accessing /api/v1/users (Admin only) must return 403 Forbidden
    res_admin = await async_client.get("/api/v1/users", headers=headers)
    assert res_admin.status_code == 403
    assert "Operation not permitted" in res_admin.json()["detail"]


@pytest.mark.asyncio
async def test_rbac_admin_allowed(async_client):
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "AdminPassword123!"

    # Register as ORG_ADMIN
    await async_client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": password,
        "full_name": "Org Admin User",
        "role": "ORG_ADMIN"
    })

    # Login
    res_login = await async_client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": password
    })
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Accessing /api/v1/users must succeed (200)
    res_admin = await async_client.get("/api/v1/users", headers=headers)
    assert res_admin.status_code == 200
    users = res_admin.json()
    assert isinstance(users, list)
    assert len(users) >= 1
