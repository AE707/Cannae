"""
LLM Service abstraction layer supporting multiple providers.
Designed to be extended for different LLM backends (Anthropic, Ollama, OpenAI, etc.).
"""
import abc
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from core.config import get_settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when an LLM API call fails."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class BaseLLMService(abc.ABC):
    """Abstract base class for LLM services."""

    @abc.abstractmethod
    async def create_message(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Create a chat completion message.

        Returns:
            Dict with at least: {'content': str, 'usage': dict}
        """
        pass

    @abc.abstractmethod
    async def create_message_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a streaming chat completion message."""
        pass


class AnthropicLLMService(BaseLLMService):
    """Anthropic Claude API implementation."""

    def __init__(self) -> None:
        import anthropic
        self.settings = get_settings()
        if not self.settings.anthropic_api_key:
            raise LLMServiceError(
                "ANTHROPIC_API_KEY is not configured", retryable=False
            )
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self._anthropic = anthropic  # keep module ref for exception types

    async def create_message(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Create a message using Anthropic API.

        Raises LLMServiceError with context on failure.
        """
        from core.constants import CLAUDE_MODEL, MAX_TOKENS

        model = model or CLAUDE_MODEL
        max_tokens = max_tokens or MAX_TOKENS

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
        except self._anthropic.RateLimitError as exc:
            raise LLMServiceError(
                f"Anthropic rate limit exceeded: {exc}", retryable=True
            ) from exc
        except self._anthropic.AuthenticationError as exc:
            raise LLMServiceError(
                f"Anthropic authentication failed — check ANTHROPIC_API_KEY: {exc}",
                retryable=False,
            ) from exc
        except self._anthropic.APIConnectionError as exc:
            raise LLMServiceError(
                f"Cannot reach Anthropic API: {exc}", retryable=True
            ) from exc
        except self._anthropic.APIError as exc:
            raise LLMServiceError(
                f"Anthropic API error: {exc}", retryable=False
            ) from exc

        if not response.content:
            raise LLMServiceError("Anthropic returned an empty response")

        return {
            "content": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        }

    async def create_message_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a streaming message using Anthropic API.

        Raises LLMServiceError on connection/auth failures.
        """
        from core.constants import CLAUDE_MODEL, MAX_TOKENS

        model = model or CLAUDE_MODEL
        max_tokens = max_tokens or MAX_TOKENS

        try:
            async with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        yield {
                            "type": "content_block_delta",
                            "delta": event.delta.text
                        }
                    elif event.type == "message_stop":
                        yield {
                            "type": "message_stop",
                            "usage": {
                                "input_tokens": event.message.usage.input_tokens,
                                "output_tokens": event.message.usage.output_tokens,
                                "total_tokens": event.message.usage.input_tokens + event.message.usage.output_tokens
                            }
                        }
        except self._anthropic.RateLimitError as exc:
            raise LLMServiceError(
                f"Anthropic rate limit exceeded during stream: {exc}", retryable=True
            ) from exc
        except self._anthropic.AuthenticationError as exc:
            raise LLMServiceError(
                f"Anthropic authentication failed: {exc}", retryable=False
            ) from exc
        except self._anthropic.APIConnectionError as exc:
            raise LLMServiceError(
                f"Connection lost during Anthropic stream: {exc}", retryable=True
            ) from exc
        except self._anthropic.APIError as exc:
            raise LLMServiceError(
                f"Anthropic API error during stream: {exc}", retryable=False
            ) from exc


class OllamaLLMService(BaseLLMService):
    """Ollama API implementation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = getattr(self.settings, 'ollama_base_url', "http://localhost:11434")
        self.default_model = getattr(self.settings, 'ollama_model', "llama3")

    def _build_prompt(self, messages: List[Dict[str, str]]) -> tuple[str, str]:
        """Convert messages list to Ollama prompt format.

        Returns (system_msg, prompt).
        """
        system_msg = ""
        user_msgs: List[str] = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_msgs.append(msg["content"])
            elif msg["role"] == "assistant":
                user_msgs.append(msg["content"])

        prompt = f"{system_msg}\n\n{' '.join(user_msgs)}".strip()
        return system_msg, prompt

    async def create_message(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Create a message using Ollama API.

        Raises LLMServiceError on connection or HTTP errors.
        """
        import httpx

        model = model or self.default_model
        system_msg, prompt = self._build_prompt(messages)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "system": system_msg if system_msg else None,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens or 100,
                        }
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMServiceError(
                f"Cannot connect to Ollama at {self.base_url}: {exc}",
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMServiceError(
                f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text[:200]}",
                retryable=exc.response.status_code >= 500,
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMServiceError(
                f"Ollama request timed out: {exc}", retryable=True
            ) from exc

        result = response.json()
        content = result.get("response", "")
        if not content:
            raise LLMServiceError("Ollama returned an empty response")

        return {
            "content": content,
            "usage": {
                "input_tokens": len(prompt) // 4,
                "output_tokens": len(content) // 4,
                "total_tokens": (len(prompt) + len(content)) // 4
            }
        }

    async def create_message_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a streaming message using Ollama API.

        Raises LLMServiceError on connection failures. Logs and skips
        malformed JSON lines rather than silently discarding them.
        """
        import httpx
        import json

        model = model or self.default_model
        system_msg, prompt = self._build_prompt(messages)

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "system": system_msg if system_msg else None,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens or 100,
                        }
                    },
                    timeout=120.0,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(
                                "Ollama stream: malformed JSON line skipped: %r",
                                line[:100],
                            )
                            continue
                        if "response" in data:
                            yield {
                                "type": "content_block_delta",
                                "delta": data["response"]
                            }
                        if data.get("done", False):
                            yield {
                                "type": "message_stop",
                                "usage": {
                                    "input_tokens": len(prompt) // 4,
                                    "output_tokens": len(data.get("response", "")) // 4,
                                    "total_tokens": (len(prompt) + len(data.get("response", ""))) // 4
                                }
                            }
        except httpx.ConnectError as exc:
            raise LLMServiceError(
                f"Cannot connect to Ollama at {self.base_url}: {exc}",
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMServiceError(
                f"Ollama stream returned HTTP {exc.response.status_code}",
                retryable=exc.response.status_code >= 500,
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMServiceError(
                f"Ollama stream timed out: {exc}", retryable=True
            ) from exc


# Factory function to get the appropriate LLM service
def get_llm_service() -> BaseLLMService:
    """Get LLM service based on configuration.

    For now, defaults to Anthropic. Can be extended to read from config.
    """
    # In the future, this could read from settings to choose provider
    # For MVP, we'll use Anthropic as specified in CLAUDE.md
    settings = get_settings()

    # Check if we should use Ollama (for local development/testing)
    if getattr(settings, 'use_ollama', False):
        return OllamaLLMService()
    else:
        # Default to Anthropic as per CLAUDE.md spec
        return AnthropicLLMService()


# Backward compatibility wrapper
class LLMService:
    """Wrapper for backward compatibility with existing code."""

    def __init__(self) -> None:
        self.service = get_llm_service()

    async def create_message(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Delegate to the underlying service implementation."""
        """Delegate to the underlying provider service."""
        return await self.service.create_message(
            messages=messages, model=model, max_tokens=max_tokens, temperature=temperature
        )

    async def create_message_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Delegate streaming to the underlying provider service."""
        async for chunk in self.service.create_message_stream(
            messages=messages, model=model, max_tokens=max_tokens, temperature=temperature
        ):
            yield chunk

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from a prompt (legacy interface)."""
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = await self.service.create_message(messages)
        return result["content"]