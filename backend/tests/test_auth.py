import pytest
import uuid


@pytest.mark.asyncio
async def test_auth_registration_and_duplicate(async_client):
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": "Test Student",
        "role": "STUDENT"
    }

    # 1. Register successfully
    res = await async_client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == test_email.lower()
    assert data["full_name"] == "Test Student"
    assert data["role"] == "STUDENT"
    assert "id" in data

    # 2. Duplicate registration must fail with 400 or 409
    res_dup = await async_client.post("/api/v1/auth/register", json=payload)
    assert res_dup.status_code in [400, 409]
    assert "already exists" in res_dup.json()["detail"].lower()


@pytest.mark.asyncio
async def test_auth_login_and_token_refresh(async_client):
    test_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword456!"
    
    # Register
    await async_client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": password,
        "full_name": "Login User",
        "role": "STUDENT"
    })

    # 1. Invalid login
    res_fail = await async_client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": "WrongPassword999!"
    })
    assert res_fail.status_code == 401

    # 2. Valid login
    res_login = await async_client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": password
    })
    assert res_login.status_code == 200
    tokens = res_login.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"
    assert access_token is not None
    assert refresh_token is not None

    # 3. Access protected /me
    headers = {"Authorization": f"Bearer {access_token}"}
    res_me = await async_client.get("/api/v1/users/me", headers=headers)
    assert res_me.status_code == 200
    user_data = res_me.json()
    assert user_data["email"] == test_email

    # 4. Token refresh rotation
    res_refresh = await async_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert res_refresh.status_code == 200
    new_tokens = res_refresh.json()
    new_access = new_tokens["access_token"]
    new_refresh = new_tokens["refresh_token"]
    assert new_access != access_token
    assert new_refresh != refresh_token

    # 5. Old refresh token replay must fail
    res_replay = await async_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert res_replay.status_code == 401

    # 6. Logout with new access token
    res_logout = await async_client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_access}"})
    assert res_logout.status_code == 200

    # 7. Access with revoked access token must be rejected (blacklisted jti)
    res_revoked = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {new_access}"})
    assert res_revoked.status_code == 401


@pytest.mark.asyncio
async def test_auth_change_password(async_client):
    test_email = f"pwd_{uuid.uuid4().hex[:8]}@example.com"
    old_pw = "OriginalPass123!"
    new_pw = "BrandNewPass789!"

    # Register
    await async_client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": old_pw,
        "full_name": "Password User",
        "role": "STUDENT"
    })

    # Login
    res_login = await async_client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": old_pw
    })
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    res_change = await async_client.post("/api/v1/auth/change-password", headers=headers, json={
        "current_password": old_pw,
        "new_password": new_pw
    })
    assert res_change.status_code == 200

    # Login with old password fails
    res_old = await async_client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": old_pw
    })
    assert res_old.status_code == 401

    # Login with new password succeeds
    res_new = await async_client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": new_pw
    })
    assert res_new.status_code == 200
