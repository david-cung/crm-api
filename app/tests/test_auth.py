import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register
        user_data = {
            "email": "test@example.com",
            "password": "secretpassword",
            "full_name": "Test User",
            "phone_number": "0123456789"
        }
        response = await ac.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

        # 2. Login
        login_data = {
            "email": "test@example.com",
            "password": "secretpassword"
        }
        response = await ac.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["user"]["email"] == "test@example.com"

        # 3. Login with wrong password
        login_data["password"] = "wrong"
        response = await ac.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 400
