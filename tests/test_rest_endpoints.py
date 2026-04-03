def test_expense_crud_endpoints(client, auth_token):
    headers = {"Authorization": auth_token}

    create_response = client.post(
        "/api/v1/expenses",
        json={"title": "rent", "amount": 12000, "category": "housing"},
        headers=headers,
    )
    assert create_response.status_code == 201
    expense_id = create_response.json()["id"]

    list_response = client.get("/api/v1/expenses", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/v1/expenses/{expense_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "rent"

    update_response = client.put(
        f"/api/v1/expenses/{expense_id}",
        json={"amount": 12500, "category": "housing"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["expense"]["amount"] == "12500.00"

    total_response = client.get("/api/v1/expenses/summary/total", headers=headers)
    assert total_response.status_code == 200
    assert total_response.json()["total_expenses"] == "12500.00"

    delete_response = client.delete(f"/api/v1/expenses/{expense_id}", headers=headers)
    assert delete_response.status_code == 200


def test_budget_endpoints(client, auth_token):
    headers = {"Authorization": auth_token}

    create_response = client.post(
        "/api/v1/budgets",
        json={"category": "food", "monthly_limit": 5000},
        headers=headers,
    )
    assert create_response.status_code == 201

    status_response = client.get("/api/v1/budgets/food", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["budget"] == 5000.0

    warnings_response = client.get("/api/v1/budgets/status/warnings", headers=headers)
    assert warnings_response.status_code == 200
    assert warnings_response.json()["warnings"] == []

    update_response = client.put(
        "/api/v1/budgets/food",
        json={"monthly_limit": 5500},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["monthly_limit"] == 5500.0


def test_analytics_endpoints(client, auth_token):
    headers = {"Authorization": auth_token}

    client.post(
        "/api/v1/expenses",
        json={"title": "pizza", "amount": 250, "category": "food"},
        headers=headers,
    )
    client.post(
        "/api/v1/expenses",
        json={"title": "uber", "amount": 180, "category": "transport"},
        headers=headers,
    )

    monthly_summary = client.get("/api/v1/analytics/monthly-summary", headers=headers)
    assert monthly_summary.status_code == 200
    assert monthly_summary.json()["month_total"] == 430.0

    top_category = client.get("/api/v1/analytics/top-category", headers=headers)
    assert top_category.status_code == 200
    assert top_category.json()["top_category"] == "food"

    category_total = client.get("/api/v1/analytics/category-total/food", headers=headers)
    assert category_total.status_code == 200
    assert category_total.json()["total_spent"] == 250.0
