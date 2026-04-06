def test_login_returns_access_and_refresh_tokens(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "refresh@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_refresh_endpoint_issues_new_tokens(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh2@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "refresh2@example.com", "password": "password123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert "access_token" in refreshed
    assert "refresh_token" in refreshed
    assert refreshed["token_type"] == "bearer"


def test_refresh_endpoint_rejects_access_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh3@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "refresh3@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid refresh token"
