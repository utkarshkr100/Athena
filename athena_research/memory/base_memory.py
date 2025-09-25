from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class MemoryItem(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    memory_type: str  # "fact", "conversation", "source", "plan"

class MemoryQuery(BaseModel):
    query: str
    memory_types: Optional[List[str]] = None
    limit: int = 10
    similarity_threshold: float = 0.7

class MemoryResult(BaseModel):
    items: List[MemoryItem]
    total_count: int
    query_time: float

class BaseMemoryStore(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def store(self, item: MemoryItem) -> bool:
        """Store a memory item"""
        pass

    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> MemoryResult:
        """Retrieve memory items based on query"""
        pass

    @abstractmethod
    async def update(self, item_id: str, item: MemoryItem) -> bool:
        """Update an existing memory item"""
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all memory items"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        pass