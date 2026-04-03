import json
import logging
import re
from typing import Any, Dict, Optional

from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from ai.prompt import get_expense_prompt
from core.config import settings
from schemas.ai import AIResponse

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.ai_api_key or "missing-api-key",
    base_url=settings.ai_base_url,
    timeout=settings.ai_timeout_seconds,
)


class AIProcessingError(Exception):
    pass


def _extract_validated_command(raw_content: str) -> Dict[str, Any]:
    raw_json = json.loads(raw_content)
    validated_data = AIResponse(**raw_json)
    return validated_data.model_dump()


def _build_validated_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    defaults = {
        "action": "unknown",
        "id": None,
        "title": None,
        "amount": None,
        "category": None,
        "min_amount": None,
        "max_amount": None,
    }
    defaults.update(payload)
    return AIResponse(**defaults).model_dump()


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _extract_first_amount(text: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _extract_id(text: str) -> Optional[int]:
    match = re.search(r"\bexpense\s+id\s+(\d+)\b", text)
    return int(match.group(1)) if match else None


def _extract_category_for_update(text: str) -> Optional[str]:
    match = re.search(r"\bcategory\s+to\s+([a-zA-Z_ ]+)$", text)
    return match.group(1).strip().lower() if match else None


def _extract_explicit_category_for_add(text: str) -> Optional[str]:
    match = re.search(r"\bcategory\s+([a-zA-Z_ ]+)$", text)
    return match.group(1).strip().lower() if match else None


def _extract_title_for_update(text: str) -> Optional[str]:
    patterns = [
        r"^(?:update|change)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)\s+amount\s+to\s+\d+(?:\.\d+)?(?:\s+and\s+category\s+to\s+[a-zA-Z_ ]+)?$",
        r"^(?:update|change)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)\s+(?:expense\s+)?to\s+\d+(?:\.\d+)?(?:\s+and\s+category\s+to\s+[a-zA-Z_ ]+)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().lower()
    return None


def _extract_title_for_add(text: str) -> Optional[str]:
    patterns = [
        r"^(?:bought|ordered|purchased)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)\s+for\s+\d+(?:\.\d+)?(?:\s+category\s+[a-zA-Z_ ]+)?$",
        r"^(?:spent|paid)\s+\d+(?:\.\d+)?\s+(?:on|for)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)$",
        r"^([a-zA-Z][a-zA-Z0-9 _-]*?)\s+for\s+\d+(?:\.\d+)?(?:\s+category\s+[a-zA-Z_ ]+)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().lower()
    return None


def _extract_amount_for_add(text: str) -> Optional[float]:
    if text.startswith(("spent ", "paid ")):
        match = re.search(r"^(?:spent|paid)\s+(\d+(?:\.\d+)?)\b", text)
        if match:
            return float(match.group(1))
    return _extract_first_amount(text)


def _extract_category_query(text: str) -> Optional[str]:
    patterns = [
        r"how much(?: did i)? spend on ([a-zA-Z_ ]+)$",
        r"how much spent on ([a-zA-Z_ ]+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().lower()
    return None


def _extract_budget_category(text: str) -> Optional[str]:
    patterns = [
        r"^(?:set|update|increase)\s+([a-zA-Z_ ]+?)\s+budget(?:\s+to)?\s+\d+(?:\.\d+)?$",
        r"^(?:delete|remove)\s+([a-zA-Z_ ]+?)\s+budget$",
        r"^what is my\s+([a-zA-Z_ ]+?)\s+budget\??$",
        r"^([a-zA-Z_ ]+?)\s+budget status$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().lower()
    return None


def _extract_budget_amount(text: str) -> Optional[float]:
    match = re.search(r"budget(?:\s+to)?\s+(\d+(?:\.\d+)?)$", text)
    return float(match.group(1)) if match else None


def _rule_based_parse(user_command: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize(user_command)

    if normalized.startswith(("update ", "change ")):
        expense_id = _extract_id(normalized)
        amount = _extract_first_amount(re.sub(r"\bexpense\s+id\s+\d+\b", "", normalized))
        category = _extract_category_for_update(normalized)
        title = None if expense_id else _extract_title_for_update(normalized)
        if expense_id or title:
            return _build_validated_command(
                {"action": "update", "id": expense_id, "title": title, "amount": amount, "category": category}
            )

    if normalized.startswith(("delete ", "remove ")):
        if "budget" in normalized:
            category = _extract_budget_category(normalized)
            if category:
                return _build_validated_command({"action": "delete_budget", "category": category})
        expense_id = _extract_id(normalized)
        if expense_id:
            return _build_validated_command({"action": "delete", "id": expense_id})
        match = re.search(r"^(?:delete|remove)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)(?:\s+expense)?$", normalized)
        if match:
            return _build_validated_command({"action": "delete", "title": match.group(1).strip().lower()})

    if normalized.startswith(("set ", "update ", "increase ")) and " budget" in normalized:
        category = _extract_budget_category(normalized)
        amount = _extract_budget_amount(normalized)
        if category and amount is not None:
            action = "update_budget" if normalized.startswith(("update ", "increase ")) else "set_budget"
            return _build_validated_command({"action": action, "category": category, "amount": amount})

    if " budget" in normalized:
        if normalized in {"any budget", "show budgets", "list budgets", "show all budgets", "what budgets do i have"}:
            return _build_validated_command({"action": "budget_overview"})
        if "warning" in normalized or "near my budget" in normalized or "budget limit" in normalized:
            return _build_validated_command({"action": "budget_warning"})
        category = _extract_budget_category(normalized)
        if category:
            return _build_validated_command({"action": "budget_status", "category": category})

    if normalized in {"show my expenses", "list expenses", "list all expenses", "show expenses"}:
        return _build_validated_command({"action": "list"})

    if normalized in {"total expenses", "how much did i spend", "how much have i spent"}:
        return _build_validated_command({"action": "total"})

    category_query = _extract_category_query(normalized)
    if category_query:
        return _build_validated_command({"action": "category", "category": category_query})

    if normalized.startswith("show ") and " expenses above " in normalized:
        amount = _extract_first_amount(normalized)
        if amount is not None:
            return _build_validated_command({"action": "filter", "min_amount": amount})

    if normalized.startswith("show ") and normalized.endswith(" expenses"):
        category = normalized.removeprefix("show ").removesuffix(" expenses").strip()
        if category and category not in {"my", "all"}:
            return _build_validated_command({"action": "filter", "category": category})

    if normalized in {"monthly summary", "month summary"}:
        return _build_validated_command({"action": "monthly_summary"})
    if normalized in {"today spending", "daily spending", "today's spending"}:
        return _build_validated_command({"action": "daily_spending"})
    if normalized == "top spending category":
        return _build_validated_command({"action": "top_category"})
    if normalized == "spending trend":
        return _build_validated_command({"action": "spending_trend"})
    if normalized in {"give me insights", "give insights", "insights"}:
        return _build_validated_command({"action": "insights"})

    add_verbs = ("bought ", "ordered ", "purchased ", "spent ", "paid ")
    if normalized.startswith(add_verbs) or re.search(r"\s+for\s+\d", normalized):
        title = _extract_title_for_add(normalized)
        amount = _extract_amount_for_add(normalized)
        category = _extract_explicit_category_for_add(normalized)
        if title and amount:
            return _build_validated_command(
                {"action": "add", "title": title, "amount": amount, "category": category}
            )

    return None


async def parse_user_command(user_command: str) -> dict:
    rule_based_result = _rule_based_parse(user_command)
    if rule_based_result is not None:
        return rule_based_result

    if not settings.ai_api_key:
        raise AIProcessingError("AI provider is not configured.")

    prompt = get_expense_prompt(user_command)

    try:
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only for the expense command.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return _extract_validated_command(response.choices[0].message.content)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("LLM output failed validation", exc_info=exc)
        raise AIProcessingError("AI provider returned an invalid command format.") from exc
    except APITimeoutError as exc:
        logger.warning("Timed out while parsing user command with AI provider", exc_info=exc)
        raise AIProcessingError("AI provider timed out while parsing the request.") from exc
    except OpenAIError as exc:
        logger.exception("AI provider error while parsing user command")
        raise AIProcessingError("AI provider could not process the request.") from exc
    except Exception as exc:
        logger.exception("Unexpected error while parsing user command")
        raise AIProcessingError("Unexpected AI parsing failure.") from exc
