import pytest
from freezegun import freeze_time


def test_total_and_category_total(client, auth_token):
    """Tests the total expense and category-specific totals."""
    # --- ADD SETUP HERE ---
    headers = {"Authorization": auth_token}
    client.post("/api/v1/expenses/agent", json={"query": "pizza for 150"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "uber for 80"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "coffee for 50"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "another pizza for 120"}, headers=headers)
    # --- END SETUP ---

    # Test total (150+80+50+120 = 400)
    response = client.post("/api/v1/expenses/agent", json={"query": "total expenses"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert response.json()["total_expenses"] == "400.00"

    # Test category total for food (150+120 = 270)
    response = client.post("/api/v1/expenses/agent", json={"query": "how much spent on food"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert response.json()["total_spent"] == 270.0

def test_top_category(client, auth_token):
    """Tests finding the top spending category."""
    # --- ADD SETUP HERE ---
    headers = {"Authorization": auth_token}
    client.post("/api/v1/expenses/agent", json={"query": "pizza for 150"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "uber for 80"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "coffee for 50"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "another pizza for 120"}, headers=headers)
    # --- END SETUP ---

    response = client.post("/api/v1/expenses/agent", json={"query": "top spending category"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["top_category"] == "food"
    assert data["amount"] == 270.0

@freeze_time("2024-05-20 12:00:00")
def test_daily_and_monthly_summary(client, auth_token):
    """Tests daily and monthly summaries."""
    # --- ADD SETUP HERE ---
    headers = {"Authorization": auth_token}
    client.post("/api/v1/expenses/agent", json={"query": "pizza for 150"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "uber for 80"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "coffee for 50"}, headers=headers)
    client.post("/api/v1/expenses/agent", json={"query": "another pizza for 120"}, headers=headers)
    # --- END SETUP ---

    # Since all expenses are added 'today', these should be the same as total
    response = client.post("/api/v1/expenses/agent", json={"query": "today spending"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert response.json()["total_spent"] == 400.0

    response = client.post("/api/v1/expenses/agent", json={"query": "monthly summary"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert response.json()["month_total"] == 400.0
    assert len(response.json()["categories"]) == 3 # food, transport, beverages

def test_insights_endpoint(client, auth_token):
    """
    Tests that the insights endpoint runs without error and returns a string.
    """
    # --- ADD SETUP HERE ---
    headers = {"Authorization": auth_token}
    client.post("/api/v1/expenses/agent", json={"query": "pizza for 150"}, headers=headers)
    # --- END SETUP ---

    response = client.post("/api/v1/expenses/agent", json={"query": "give me insights"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert "insight" in data
    assert isinstance(data["insight"], str)
    assert len(data["insight"]) > 0