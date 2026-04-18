from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.prompts import SUMMARY_SYSTEM_PROMPT, build_summary_user_prompt
from app.ai.summary import generate_summary
from app.config import get_settings


@pytest.fixture(autouse=True)
def _openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_CHAT_MODEL", "openai/gpt-4o-mini")
    get_settings.cache_clear()


def _make_mock_client(content: str) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]

    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


class TestPrompts:
    def test_system_prompt_mentions_portuguese(self) -> None:
        assert "Portuguese" in SUMMARY_SYSTEM_PROMPT or "português" in SUMMARY_SYSTEM_PROMPT.lower()

    def test_user_prompt_includes_title_and_author(self) -> None:
        prompt = build_summary_user_prompt("O Hobbit", "Tolkien")
        assert "O Hobbit" in prompt
        assert "Tolkien" in prompt


class TestGenerateSummary:
    async def test_returns_generated_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = _make_mock_client("Uma aventura épica na Terra Média.")
        monkeypatch.setattr("app.ai.summary.get_openrouter_client", lambda: mock_client)

        result = await generate_summary("O Hobbit", "Tolkien")
        assert result == "Uma aventura épica na Terra Média."

    async def test_strips_whitespace_from_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = _make_mock_client("  Resumo  \n\n")
        monkeypatch.setattr("app.ai.summary.get_openrouter_client", lambda: mock_client)

        assert await generate_summary("X", "Y") == "Resumo"

    async def test_handles_empty_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = _make_mock_client("")
        monkeypatch.setattr("app.ai.summary.get_openrouter_client", lambda: mock_client)

        assert await generate_summary("X", "Y") == ""

    async def test_sends_configured_model_and_messages(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_client = _make_mock_client("ok")
        monkeypatch.setattr("app.ai.summary.get_openrouter_client", lambda: mock_client)

        await generate_summary("O Hobbit", "Tolkien")

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "openai/gpt-4o-mini"
        assert kwargs["max_tokens"] == 150
        messages = kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "O Hobbit" in messages[1]["content"]
