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


def _extract_first_amount(text: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _extract_category(text: str) -> Optional[str]:
    match = re.search(r"\bcategory\s+to\s+([a-zA-Z_ ]+)$", text)
    if match:
        return match.group(1).strip().lower()
    return None


def _extract_id(text: str) -> Optional[int]:
    match = re.search(r"\bexpense\s+id\s+(\d+)\b", text)
    return int(match.group(1)) if match else None


def _extract_title_for_update(text: str) -> Optional[str]:
    title_patterns = [
        r"^(?:update|change)\s+expense\s+id\s+\d+\s+(?:amount\s+to\s+\d+(?:\.\d+)?(?:\s+and\s+category\s+to\s+[a-zA-Z_ ]+)?)$",
        r"^(?:update|change)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)\s+amount\s+to\s+\d+(?:\.\d+)?(?:\s+and\s+category\s+to\s+[a-zA-Z_ ]+)?$",
        r"^(?:update|change)\s+([a-zA-Z][a-zA-Z0-9 _-]*?)\s+(?:expense\s+)?to\s+\d+(?:\.\d+)?(?:\s+and\s+category\s+to\s+[a-zA-Z_ ]+)?$",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match and match.lastindex:
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


def _extract_explicit_category_for_add(text: str) -> Optional[str]:
    match = re.search(r"\bcategory\s+([a-zA-Z_ ]+)$", text)
    if match:
        return match.group(1).strip().lower()
    return None


def _rule_based_parse(user_command: str) -> Optional[Dict[str, Any]]:
    normalized = " ".join(user_command.strip().lower().split())

    if normalized.startswith(("update ", "change ")):
        expense_id = _extract_id(normalized)
        amount = _extract_first_amount(re.sub(r"\bexpense\s+id\s+\d+\b", "", normalized))
        category = _extract_category(normalized)
        title = None if expense_id else _extract_title_for_update(normalized)

        if expense_id or title:
            return _build_validated_command(
                {
                    "action": "update",
                    "id": expense_id,
                    "title": title,
                    "amount": amount,
                    "category": category,
                }
            )

    if normalized.startswith(("delete ", "remove ")):
        expense_id = _extract_id(normalized)
        if expense_id:
            return _build_validated_command({"action": "delete", "id": expense_id})

    add_verbs = ("bought ", "ordered ", "purchased ", "spent ", "paid ")
    if normalized.startswith(add_verbs) or re.search(r"\s+for\s+\d", normalized):
        title = _extract_title_for_add(normalized)
        amount = _extract_amount_for_add(normalized)
        category = _extract_explicit_category_for_add(normalized)

        if title and amount:
            return _build_validated_command(
                {
                    "action": "add",
                    "title": title,
                    "amount": amount,
                    "category": category,
                }
            )

    return None


async def parse_user_command(user_command: str) -> dict:
    """
    Sends a natural language command to the configured LLM and returns validated JSON.
    """
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
                    "content": "You are a financial assistant. Always respond in valid JSON only. Do not include explanations.",
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
