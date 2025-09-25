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