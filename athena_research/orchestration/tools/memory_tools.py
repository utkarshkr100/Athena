from typing import Any, Dict, List, Optional
from ag2 import Tool
from ...memory import MemoryManager, MemoryItem

class AthenaMemoryTools:
    """AG2 tools wrapper for Athena memory capabilities"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.tools = self._create_tools()

    def _create_tools(self) -> List[Tool]:
        """Create AG2 tools for memory operations"""
        tools = []

        # Store fact tool
        store_fact_tool = Tool(
            name="store_fact",
            description="Store an important research fact in memory",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The fact to store"
                    },
                    "importance": {
                        "type": "string",
                        "description": "Importance level",
                        "enum": ["low", "medium", "high"],
                        "default": "medium"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization"
                    }
                },
                "required": ["content"]
            }
        )(self._store_fact)

        tools.append(store_fact_tool)

        # Retrieve facts tool
        retrieve_facts_tool = Tool(
            name="retrieve_facts",
            description="Retrieve relevant facts from memory",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to search for facts"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of facts to return",
                        "default": 10
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity threshold",
                        "default": 0.7
                    }
                },
                "required": ["query"]
            }
        )(self._retrieve_facts)

        tools.append(retrieve_facts_tool)

        # Store source tool
        store_source_tool = Tool(
            name="store_source",
            description="Store a research source in memory",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Source title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Source content"
                    },
                    "url": {
                        "type": "string",
                        "description": "Source URL"
                    },
                    "source_type": {
                        "type": "string",
                        "description": "Type of source",
                        "default": "web"
                    }
                },
                "required": ["title", "content"]
            }
        )(self._store_source)

        tools.append(store_source_tool)

        # Retrieve sources tool
        retrieve_sources_tool = Tool(
            name="retrieve_sources",
            description="Retrieve relevant sources from memory",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to search for sources"
                    },
                    "source_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by source types"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of sources to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )(self._retrieve_sources)

        tools.append(retrieve_sources_tool)

        # Search all memory tool
        search_memory_tool = Tool(
            name="search_memory",
            description="Search across all memory types",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "memory_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Memory types to search: fact, source, conversation, plan"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        )(self._search_memory)

        tools.append(search_memory_tool)

        return tools

    async def _store_fact(
        self,
        content: str,
        importance: str = "medium",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Store a fact in memory"""
        try:
            metadata = {
                "importance": importance,
                "tags": tags or []
            }

            fact_id = await self.memory_manager.store_fact(content, metadata)

            return {
                "status": "success",
                "fact_id": fact_id,
                "content": content,
                "importance": importance,
                "tags": tags
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _retrieve_facts(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Retrieve facts from memory"""
        try:
            facts = await self.memory_manager.retrieve_facts(
                query, limit, similarity_threshold
            )

            return {
                "status": "success",
                "facts": [self._serialize_memory_item(fact) for fact in facts],
                "total_count": len(facts),
                "query": query
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _store_source(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        source_type: str = "web"
    ) -> Dict[str, Any]:
        """Store a source in memory"""
        try:
            source_id = await self.memory_manager.store_source(
                title, content, url, source_type
            )

            return {
                "status": "success",
                "source_id": source_id,
                "title": title,
                "url": url,
                "source_type": source_type
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _retrieve_sources(
        self,
        query: str,
        source_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Retrieve sources from memory"""
        try:
            sources = await self.memory_manager.retrieve_sources(
                query, source_types, limit
            )

            return {
                "status": "success",
                "sources": [self._serialize_memory_item(source) for source in sources],
                "total_count": len(sources),
                "query": query,
                "source_types": source_types
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _search_memory(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search across all memory types"""
        try:
            items = await self.memory_manager.search_all(
                query, memory_types, limit
            )

            return {
                "status": "success",
                "items": [self._serialize_memory_item(item) for item in items],
                "total_count": len(items),
                "query": query,
                "memory_types": memory_types
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _serialize_memory_item(self, item: MemoryItem) -> Dict[str, Any]:
        """Convert MemoryItem to serializable dict"""
        return {
            "id": item.id,
            "content": item.content,
            "memory_type": item.memory_type,
            "timestamp": item.timestamp.isoformat(),
            "metadata": item.metadata
        }

    def get_tools(self) -> List[Tool]:
        """Get all AG2 tools"""
        return self.tools