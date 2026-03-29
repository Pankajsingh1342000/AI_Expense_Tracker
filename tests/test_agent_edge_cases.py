from datetime import datetime

from api.v1 import expense_routes
from services import ai_insight_service


def async_return(value):
    async def _mock(_query):
        return value

    return _mock


def test_agent_requires_authentication(client):
    response = client.post("/api/v1/expenses/agent", json={"query": "pizza for 100"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_unknown_ai_action_returns_400(client, auth_token, monkeypatch):
    monkeypatch.setattr(
        expense_routes,
        "parse_user_command",
        async_return({"action": "unsupported_action"}),
    )

    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "do something strange"},
        headers={"Authorization": auth_token},
    )

    assert response.status_code == 400
    assert "unsupported_action" in response.json()["detail"]


def test_add_expense_normalizes_category_aliases(client, auth_token, monkeypatch):
    monkeypatch.setattr(
        expense_routes,
        "parse_user_command",
        async_return({
            "action": "add",
            "title": "Cold Brew",
            "amount": 90,
            "category": "drinks",
            "min_amount": None,
            "max_amount": None,
            "id": None,
        }),
    )

    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "log my coffee"},
        headers={"Authorization": auth_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "beverages"
    assert data["amount"] == "90.00"


def test_add_expense_uses_title_mapping_when_category_missing(client, auth_token, monkeypatch):
    monkeypatch.setattr(
        expense_routes,
        "parse_user_command",
        async_return({
            "action": "add",
            "title": "Uber",
            "amount": 240,
            "category": None,
            "min_amount": None,
            "max_amount": None,
            "id": None,
        }),
    )

    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "booked an uber"},
        headers={"Authorization": auth_token},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "transport"


def test_update_with_ambiguous_titles_requests_clarification(client, auth_token, monkeypatch):
    headers = {"Authorization": auth_token}

    for amount in (100, 120):
        monkeypatch.setattr(
            expense_routes,
            "parse_user_command",
            async_return({
                "action": "add",
                "title": "lunch",
                "amount": amount,
                "category": "food",
                "date": datetime(2024, 5, 20, 12, 0, 0),
                "min_amount": None,
                "max_amount": None,
                "id": None,
            }),
        )
        client.post("/api/v1/expenses/agent", json={"query": f"lunch for {amount}"}, headers=headers)

    monkeypatch.setattr(
        expense_routes,
        "parse_user_command",
        async_return({
            "action": "update",
            "title": "lunch",
            "amount": 150,
            "category": None,
            "min_amount": None,
            "max_amount": None,
            "id": None,
        }),
    )

    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "update lunch to 150"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert len(data["options"]) == 2


def test_budget_overview_returns_message_when_no_budgets_exist(client, auth_token, monkeypatch):
    monkeypatch.setattr(
        expense_routes,
        "parse_user_command",
        async_return({
            "action": "budget_overview",
            "title": None,
            "amount": None,
            "category": None,
            "min_amount": None,
            "max_amount": None,
            "id": None,
        }),
    )

    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "show budgets"},
        headers={"Authorization": auth_token},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "No budgets have been set."


def test_insights_returns_friendly_message_without_expenses(client, auth_token, monkeypatch):
    def fail_if_called(_summary: str) -> str:
        raise AssertionError("Insight generation should not run without expense data")

    monkeypatch.setattr(
        expense_routes,
        "parse_user_command",
        async_return({
            "action": "insights",
            "title": None,
            "amount": None,
            "category": None,
            "min_amount": None,
            "max_amount": None,
            "id": None,
        }),
    )
    monkeypatch.setattr(ai_insight_service, "generate_insight_from_summary", fail_if_called)

    response = client.post(
        "/api/v1/expenses/agent",
        json={"query": "give me insights"},
        headers={"Authorization": auth_token},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Not enough data for insights. Add some expenses first."
