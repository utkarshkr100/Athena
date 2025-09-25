from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import asyncio

class AgentMessage(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    success: bool
    data: Any
    sources: List[Dict[str, Any]] = []
    error: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, model: str, temperature: float = 0.3):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.conversation_history: List[AgentMessage] = []

    @abstractmethod
    async def process(self, input_data: Any) -> AgentResponse:
        pass

    def add_message(self, message: AgentMessage):
        self.conversation_history.append(message)

    def get_conversation_context(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.conversation_history]

    def clear_history(self):
        self.conversation_history = []

    async def generate_llm_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response using the configured LLM"""
        from ..utils.llm_client import llm_client
        from ..config import settings

        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(self.get_conversation_context())

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        response = await llm_client.generate_response(
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or settings.max_tokens,
            model=self.model
        )

        return response