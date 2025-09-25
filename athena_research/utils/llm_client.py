from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from ..config import settings

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    AsyncAzureOpenAI = None

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4000
    ) -> str:
        pass

class GeminiClient(BaseLLMClient):
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        model: str = "gemini-1.5-flash"
    ) -> str:
        # Convert messages to Gemini format
        prompt = self._convert_messages_to_prompt(messages)

        # Create the model
        gemini_model = genai.GenerativeModel(model)

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Generate response
        response = await gemini_model.generate_content_async(
            prompt,
            generation_config=generation_config
        )

        return response.text

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        # Convert OpenAI-style messages to a single prompt for Gemini
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

class AzureOpenAIClient(BaseLLMClient):
    def __init__(self):
        if AsyncAzureOpenAI is None:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        model: str = None
    ) -> str:
        if model is None:
            model = settings.azure_openai_deployment_name

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

class LLMClientFactory:
    @staticmethod
    def create_client() -> BaseLLMClient:
        if settings.llm_provider == "gemini":
            return GeminiClient()
        elif settings.llm_provider == "azure_openai":
            if AsyncAzureOpenAI is None:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
            return AzureOpenAIClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

# Global client instance
llm_client = LLMClientFactory.create_client()