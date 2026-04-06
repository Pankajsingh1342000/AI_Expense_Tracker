import logging

from openai import APITimeoutError, OpenAI, OpenAIError

from ai.parse import AIProcessingError
from core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.ai_api_key or "missing-api-key",
    base_url=settings.ai_base_url,
    timeout=settings.ai_timeout_seconds,
)


def _truncate_summary(summary: str) -> str:
    if len(summary) <= settings.ai_insight_summary_max_chars:
        return summary
    return summary[: settings.ai_insight_summary_max_chars].rstrip() + "\n- ..."


def generate_insight_from_summary(summary: str) -> str:
    if not settings.ai_api_key:
        raise AIProcessingError("AI provider is not configured.")

    concise_summary = _truncate_summary(summary)

    try:
        response = client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial advisor for users in India. "
                        "All monetary amounts are in Indian Rupees (INR). "
                        "Give short, practical insights and suggestions. "
                        "Limit the answer to 4 concise bullet points. "
                        "When mentioning money, use Rs. or INR."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "User spending summary (all amounts are in Indian Rupees, INR):\n"
                        f"{concise_summary}\n\n"
                        "Give concise financial insights. Use Rs. or INR when referring to money."
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=settings.ai_insight_max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            raise AIProcessingError("AI provider returned an empty insight response.")
        return content
    except APITimeoutError as exc:
        logger.warning("Timed out while generating AI insight", exc_info=exc)
        raise AIProcessingError("AI provider timed out while generating insights.") from exc
    except OpenAIError as exc:
        logger.exception("AI provider error while generating insights")
        raise AIProcessingError("AI provider could not generate insights.") from exc
