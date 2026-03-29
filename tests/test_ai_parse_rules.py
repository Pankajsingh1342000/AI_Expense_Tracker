import asyncio

from ai.parse import parse_user_command


def test_rule_based_update_by_title_parses_without_ai():
    parsed = asyncio.run(parse_user_command("update pizza amount to 300 and category to food"))

    assert parsed["action"] == "update"
    assert parsed["title"] == "pizza"
    assert parsed["amount"] == 300.0
    assert parsed["category"] == "food"
    assert parsed["id"] is None


def test_rule_based_update_by_id_parses_without_ai():
    parsed = asyncio.run(parse_user_command("update expense id 1 to 300"))

    assert parsed["action"] == "update"
    assert parsed["id"] == 1
    assert parsed["amount"] == 300.0
    assert parsed["title"] is None


def test_rule_based_delete_by_id_parses_without_ai():
    parsed = asyncio.run(parse_user_command("delete expense id 1"))

    assert parsed["action"] == "delete"
    assert parsed["id"] == 1
    assert parsed["title"] is None


def test_rule_based_spent_on_phrase_parses_without_ai():
    parsed = asyncio.run(parse_user_command("spent 90 on coffee"))

    assert parsed["action"] == "add"
    assert parsed["title"] == "coffee"
    assert parsed["amount"] == 90.0


def test_rule_based_bought_for_phrase_parses_without_ai():
    parsed = asyncio.run(parse_user_command("bought groceries for 700"))

    assert parsed["action"] == "add"
    assert parsed["title"] == "groceries"
    assert parsed["amount"] == 700.0
