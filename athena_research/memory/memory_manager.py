from typing import Any, Dict, List, Optional, Union
import asyncio
import uuid
from datetime import datetime
from .base_memory import BaseMemoryStore, MemoryItem, MemoryQuery, MemoryResult
from .vector_store.chroma_memory import ChromaMemoryStore
from .cache.redis_cache import RedisCacheStore

class MemoryManager:
    def __init__(
        self,
        vector_store: Optional[BaseMemoryStore] = None,
        cache_store: Optional[BaseMemoryStore] = None,
        use_cache: bool = True,
        use_vector_store: bool = True
    ):
        self.vector_store = vector_store
        self.cache_store = cache_store
        self.use_cache = use_cache and cache_store is not None
        self.use_vector_store = use_vector_store and vector_store is not None

        # Initialize default stores if not provided
        if self.use_vector_store and self.vector_store is None:
            try:
                self.vector_store = ChromaMemoryStore()
            except Exception as e:
                print(f"Failed to initialize Chroma: {e}")
                self.use_vector_store = False

        if self.use_cache and self.cache_store is None:
            try:
                self.cache_store = RedisCacheStore()
            except Exception as e:
                print(f"Failed to initialize Redis: {e}")
                self.use_cache = False

    async def store_fact(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a research fact"""
        item_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["importance"] = metadata.get("importance", "medium")

        item = MemoryItem(
            id=item_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(),
            memory_type="fact"
        )

        success = await self._store_item(item)
        return item_id if success else None

    async def store_conversation(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a conversation message"""
        item_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["role"] = role

        item = MemoryItem(
            id=item_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(),
            memory_type="conversation"
        )

        success = await self._store_item(item)
        return item_id if success else None

    async def store_source(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        source_type: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a research source"""
        item_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata.update({
            "title": title,
            "url": url,
            "source_type": source_type
        })

        item = MemoryItem(
            id=item_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(),
            memory_type="source"
        )

        success = await self._store_item(item)
        return item_id if success else None

    async def store_plan(
        self,
        plan_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a research plan"""
        item_id = str(uuid.uuid4())
        metadata = metadata or {}

        # Convert plan data to text for storage
        content = self._plan_to_text(plan_data)

        item = MemoryItem(
            id=item_id,
            content=content,
            metadata={**metadata, "plan_data": plan_data},
            timestamp=datetime.now(),
            memory_type="plan"
        )

        success = await self._store_item(item)
        return item_id if success else None

    async def retrieve_facts(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[MemoryItem]:
        """Retrieve relevant facts"""
        memory_query = MemoryQuery(
            query=query,
            memory_types=["fact"],
            limit=limit,
            similarity_threshold=similarity_threshold
        )

        return await self._retrieve_items(memory_query)

    async def retrieve_sources(
        self,
        query: str,
        source_types: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.6
    ) -> List[MemoryItem]:
        """Retrieve relevant sources"""
        memory_query = MemoryQuery(
            query=query,
            memory_types=["source"],
            limit=limit,
            similarity_threshold=similarity_threshold
        )

        sources = await self._retrieve_items(memory_query)

        # Filter by source type if specified
        if source_types:
            filtered_sources = []
            for source in sources:
                if source.metadata.get("source_type") in source_types:
                    filtered_sources.append(source)
            return filtered_sources

        return sources

    async def retrieve_conversation(
        self,
        limit: int = 20,
        role: Optional[str] = None
    ) -> List[MemoryItem]:
        """Retrieve conversation history"""
        memory_query = MemoryQuery(
            query="",  # Empty query to get all conversation items
            memory_types=["conversation"],
            limit=limit,
            similarity_threshold=0.0
        )

        conversations = await self._retrieve_items(memory_query)

        # Filter by role if specified
        if role:
            filtered_conversations = []
            for conv in conversations:
                if conv.metadata.get("role") == role:
                    filtered_conversations.append(conv)
            return filtered_conversations

        # Sort by timestamp
        conversations.sort(key=lambda x: x.timestamp, reverse=True)
        return conversations

    async def retrieve_plans(self, limit: int = 5) -> List[MemoryItem]:
        """Retrieve stored research plans"""
        memory_query = MemoryQuery(
            query="",
            memory_types=["plan"],
            limit=limit,
            similarity_threshold=0.0
        )

        return await self._retrieve_items(memory_query)

    async def search_all(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 20,
        similarity_threshold: float = 0.6
    ) -> List[MemoryItem]:
        """Search across all memory types"""
        memory_query = MemoryQuery(
            query=query,
            memory_types=memory_types,
            limit=limit,
            similarity_threshold=similarity_threshold
        )

        return await self._retrieve_items(memory_query)

    async def update_item(self, item_id: str, item: MemoryItem) -> bool:
        """Update a memory item in all stores"""
        success = True

        if self.use_vector_store:
            success &= await self.vector_store.update(item_id, item)

        if self.use_cache:
            success &= await self.cache_store.update(item_id, item)

        return success

    async def delete_item(self, item_id: str) -> bool:
        """Delete a memory item from all stores"""
        success = True

        if self.use_vector_store:
            success &= await self.vector_store.delete(item_id)

        if self.use_cache:
            success &= await self.cache_store.delete(item_id)

        return success

    async def clear_all(self) -> bool:
        """Clear all memory stores"""
        success = True

        if self.use_vector_store:
            success &= await self.vector_store.clear()

        if self.use_cache:
            success &= await self.cache_store.clear()

        return success

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics from all memory stores"""
        stats = {}

        if self.use_vector_store:
            stats["vector_store"] = await self.vector_store.get_stats()

        if self.use_cache:
            stats["cache_store"] = await self.cache_store.get_stats()

        return stats

    async def _store_item(self, item: MemoryItem) -> bool:
        """Store item in appropriate stores"""
        tasks = []

        if self.use_vector_store:
            tasks.append(self.vector_store.store(item))

        # Store in cache for recent items or specific types
        if self.use_cache and self._should_cache(item):
            tasks.append(self.cache_store.store(item))

        if not tasks:
            return False

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(result is True for result in results if not isinstance(result, Exception))

    async def _retrieve_items(self, query: MemoryQuery) -> List[MemoryItem]:
        """Retrieve items from appropriate stores"""
        all_items = []

        # Try vector store first for semantic search
        if self.use_vector_store and query.query:
            try:
                vector_result = await self.vector_store.retrieve(query)
                all_items.extend(vector_result.items)
            except Exception as e:
                print(f"Vector store retrieval error: {e}")

        # Try cache for recent items or when vector store fails
        if self.use_cache:
            try:
                cache_result = await self.cache_store.retrieve(query)
                # Merge with vector results, avoiding duplicates
                cache_ids = {item.id for item in all_items}
                for item in cache_result.items:
                    if item.id not in cache_ids:
                        all_items.append(item)
            except Exception as e:
                print(f"Cache store retrieval error: {e}")

        # Sort by relevance if available
        all_items.sort(
            key=lambda x: x.metadata.get("similarity_score", x.metadata.get("relevance_score", 0)),
            reverse=True
        )

        return all_items[:query.limit]

    def _should_cache(self, item: MemoryItem) -> bool:
        """Determine if an item should be cached"""
        # Cache recent conversation items
        if item.memory_type == "conversation":
            return True

        # Cache high-importance facts
        if item.memory_type == "fact" and item.metadata.get("importance") == "high":
            return True

        # Cache recent sources
        if item.memory_type == "source":
            return True

        return False

    def _plan_to_text(self, plan_data: Dict[str, Any]) -> str:
        """Convert plan data to searchable text"""
        parts = []

        if "topic" in plan_data:
            parts.append(f"Topic: {plan_data['topic']}")

        if "overview" in plan_data:
            parts.append(f"Overview: {plan_data['overview']}")

        if "sections" in plan_data:
            for section in plan_data["sections"]:
                parts.append(f"Section: {section.get('title', '')}")
                parts.append(f"Description: {section.get('description', '')}")
                if "queries" in section:
                    parts.append(f"Queries: {', '.join(section['queries'])}")

        return "\n".join(parts)

    async def close(self):
        """Close all connections"""
        if self.cache_store and hasattr(self.cache_store, 'close'):
            await self.cache_store.close()