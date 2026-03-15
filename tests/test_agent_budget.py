import pytest
from freezegun import freeze_time

@freeze_time("2024-05-20 12:00:00")
def test_set_and_get_budget_status(client, auth_token):
    """
    Tests setting a budget and then checking its status.
    """
    client.post("/api/v1/expenses/agent", json={"query": "coffee for 10"}, headers={"Authorization": auth_token})
    
    # Set a budget for the 'beverages' category
    response = client.post("/api/v1/expenses/agent", json={"query": "set beverages budget to 100"}, headers={"Authorization": auth_token})
    assert response.status_code == 200

    # Check the budget status
    response = client.post("/api/v1/expenses/agent", json={"query": "what is my beverages budget?"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "beverages"
    assert data["budget"] == 100.0  # Note: Pydantic may cast simple decimals to float
    assert data["spent"] == 10.0
    assert data["remaining"] == 90.0

@freeze_time("2024-05-20 12:00:00")
def test_budget_warning_and_overview(client, auth_token):
    """
    Tests that budget warnings are triggered correctly and that the overview works.
    """
    # Set budgets
    client.post("/api/v1/expenses/agent", json={"query": "set food budget 200"}, headers={"Authorization": auth_token})
    client.post("/api/v1/expenses/agent", json={"query": "set transport budget 300"}, headers={"Authorization": auth_token})

    # Add expense below threshold
    client.post("/api/v1/expenses/agent", json={"query": "pizza for 100"}, headers={"Authorization": auth_token})
    response = client.post("/api/v1/expenses/agent", json={"query": "any budget warning?"}, headers={"Authorization": auth_token})
    assert response.json()["warnings"] == []

    # Add expense to trigger warning (100+70 = 170, which is > 80% of 200)
    client.post("/api/v1/expenses/agent", json={"query": "groceries for 70"}, headers={"Authorization": auth_token})
    response = client.post("/api/v1/expenses/agent", json={"query": "am I near my budget limits?"}, headers={"Authorization": auth_token})
    data = response.json()
    assert len(data["warnings"]) == 1
    assert data["warnings"][0]["category"] == "food"

    # Check overview
    response = client.post("/api/v1/expenses/agent", json={"query": "show all budgets"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert len(response.json()["budgets"]) == 2

def test_delete_budget(client, auth_token):
    """
    Tests deleting a budget.
    """
    client.post("/api/v1/expenses/agent", json={"query": "set entertainment budget to 500"}, headers={"Authorization": auth_token})
    
    # Delete it
    response = client.post("/api/v1/expenses/agent", json={"query": "delete entertainment budget"}, headers={"Authorization": auth_token})
    assert response.status_code == 200

    # Verify it's gone
    response = client.post("/api/v1/expenses/agent", json={"query": "what is my entertainment budget"}, headers={"Authorization": auth_token})
    assert "No budget set" in response.json()["message"]