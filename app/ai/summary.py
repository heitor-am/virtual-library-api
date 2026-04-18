from app.ai.client import get_openrouter_client, openai_retry
from app.ai.prompts import SUMMARY_SYSTEM_PROMPT, build_summary_user_prompt
from app.config import get_settings


@openai_retry
async def generate_summary(title: str, author: str) -> str:
    settings = get_settings()
    client = get_openrouter_client()

    response = await client.chat.completions.create(
        model=settings.openrouter_chat_model,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": build_summary_user_prompt(title, author)},
        ],
        max_tokens=150,
        temperature=0.3,
    )

    return (response.choices[0].message.content or "").strip()
