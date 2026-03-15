import pytest

def test_add_and_list_expense(client, auth_token):
    """
    Tests that an expense can be added and then appears in the list.
    """
    # Step 1: Add an expense
    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "bought pizza for 25.50"},
        headers={"Authorization": auth_token}
    )
    assert response.status_code == 200
    add_data = response.json()
    assert add_data["title"] == "pizza"
    assert add_data["amount"] == "25.50"
    assert add_data["category"] == "food"

    # Step 2: List expenses to verify
    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "show my expenses"},
        headers={"Authorization": auth_token}
    )
    assert response.status_code == 200
    list_data = response.json()
    assert len(list_data) == 1
    assert list_data[0]["title"] == "pizza"

def test_update_expense(client, auth_token):
    """
    Tests updating an expense's amount and category.
    """
    # Add an initial expense
    client.post("/api/v1/expenses/agent", json={"query": "movie ticket 150"}, headers={"Authorization": auth_token})
    
    # Update the expense
    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "update movie ticket amount to 160.75 and category to entertainment"},
        headers={"Authorization": auth_token}
    )
    assert response.status_code == 200
    update_data = response.json()["expense"]
    assert update_data["amount"] == "160.75"
    assert update_data["category"] == "entertainment"

def test_delete_ambiguity_and_resolution(client, auth_token):
    """
    Tests the full cycle of ambiguous deletion and then specific resolution.
    """
    # Step 1: Add two similar expenses
    client.post("/api/v1/expenses/agent", json={"query": "lunch for 100"}, headers={"Authorization": auth_token})
    client.post("/api/v1/expenses/agent", json={"query": "another lunch for 120"}, headers={"Authorization": auth_token})

    # Step 2: Attempt an ambiguous delete
    response = client.post("/api/v1/expenses/agent", json={"query": "delete lunch"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert len(data["options"]) == 2
    
    # Step 3: Resolve ambiguity using the ID from the previous response
    expense_id_to_delete = data["options"][0]["id"]
    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": f"delete expense id {expense_id_to_delete}"},
        headers={"Authorization": auth_token}
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Step 4: Verify only one expense remains
    response = client.post("/api/v1/expenses/agent", json={"query": "list expenses"}, headers={"Authorization": auth_token})
    assert len(response.json()) == 1

def test_filter_expenses(client, auth_token):
    """
    Tests filtering expenses by amount and category.
    """
    client.post("/api/v1/expenses/agent", json={"query": "snacks for 50 category food"}, headers={"Authorization": auth_token})
    client.post("/api/v1/expenses/agent", json={"query": "train ticket for 200 category transport"}, headers={"Authorization": auth_token})
    client.post("/api/v1/expenses/agent", json={"query": "dinner for 150 category food"}, headers={"Authorization": auth_token})
    
    # Filter by min_amount
    response = client.post("/api/v1/expenses/agent", json={"query": "show expenses above 100"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # dinner and train ticket

    # Filter by category
    response = client.post("/api/v1/expenses/agent", json={"query": "show food expenses"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # snacks and dinner