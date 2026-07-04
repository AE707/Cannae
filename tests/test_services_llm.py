"""Tests for services/llm.py"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from services.llm import (
    BaseLLMService,
    AnthropicLLMService,
    OllamaLLMService,
    LLMService,
    get_llm_service,
)


class TestBaseLLMService:
    def test_is_abstract(self):
        # Cannot instantiate directly
        with pytest.raises(TypeError):
            BaseLLMService()


class TestGetLLMService:
    def test_returns_anthropic_by_default(self):
        with patch("services.llm.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                anthropic_api_key="test-key",
                use_ollama=False,
            )
            with patch("services.llm.AnthropicLLMService") as MockAnth:
                MockAnth.return_value = MagicMock()
                service = get_llm_service()
                MockAnth.assert_called_once()

    def test_returns_ollama_when_configured(self):
        with patch("services.llm.get_settings") as mock_settings:
            settings = MagicMock()
            settings.use_ollama = True
            mock_settings.return_value = settings
            with patch("services.llm.OllamaLLMService") as MockOllama:
                MockOllama.return_value = MagicMock()
                service = get_llm_service()
                MockOllama.assert_called_once()


class TestLLMServiceWrapper:
    def test_creates_internal_service(self):
        with patch("services.llm.get_llm_service") as mock_factory:
            mock_factory.return_value = MagicMock()
            wrapper = LLMService()
            assert wrapper.service is not None

    @pytest.mark.asyncio
    async def test_generate_builds_messages(self):
        with patch("services.llm.get_llm_service") as mock_factory:
            mock_service = MagicMock()
            mock_service.create_message = AsyncMock(return_value={"content": "Hello!"})
            mock_factory.return_value = mock_service

            wrapper = LLMService()
            result = await wrapper.generate("Hi there", system_prompt="Be helpful")
            assert result == "Hello!"

            call_args = mock_service.create_message.call_args
            # create_message is called with positional arg: messages list
            messages = call_args[0][0]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "Be helpful"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Hi there"

    @pytest.mark.asyncio
    async def test_generate_without_system_prompt(self):
        with patch("services.llm.get_llm_service") as mock_factory:
            mock_service = MagicMock()
            mock_service.create_message = AsyncMock(return_value={"content": "Response"})
            mock_factory.return_value = mock_service

            wrapper = LLMService()
            result = await wrapper.generate("Just a question")
            assert result == "Response"

            call_args = mock_service.create_message.call_args
            messages = call_args[0][0]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"


class TestOllamaLLMService:
    def test_init_sets_defaults(self):
        with patch("services.llm.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(spec=[])
            service = OllamaLLMService()
            assert service.base_url == "http://localhost:11434"
            assert service.default_model == "llama3"

    @pytest.mark.asyncio
    async def test_create_message_formats_response(self):
        with patch("services.llm.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(spec=[])
            service = OllamaLLMService()

            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "Generated text"}
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as MockClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.post = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
                mock_client_instance.__aexit__ = AsyncMock(return_value=False)
                MockClient.return_value = mock_client_instance

                result = await service.create_message(
                    messages=[{"role": "user", "content": "Hello"}],
                    model="llama3",
                    max_tokens=100,
                )
                assert result["content"] == "Generated text"
                assert "usage" in result
                assert "input_tokens" in result["usage"]
                assert "output_tokens" in result["usage"]
