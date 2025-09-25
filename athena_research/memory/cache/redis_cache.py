from typing import Any, Dict, List, Optional
import asyncio
import json
import time
from datetime import datetime, timedelta
import redis.asyncio as redis
from ..base_memory import BaseMemoryStore, MemoryItem, MemoryQuery, MemoryResult
from ...config import settings

class RedisCacheStore(BaseMemoryStore):
    def __init__(self, redis_url: str = None, prefix: str = "athena:memory:"):
        super().__init__("RedisCache")

        self.redis_url = redis_url or settings.redis_url
        self.prefix = prefix
        self.client = None

    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if self.client is None:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            try:
                await self.client.ping()
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                raise

    async def store(self, item: MemoryItem) -> bool:
        """Store a memory item in Redis with expiration"""
        try:
            await self._ensure_connection()

            key = f"{self.prefix}{item.id}"
            value = {
                "content": item.content,
                "metadata": item.metadata,
                "timestamp": item.timestamp.isoformat(),
                "memory_type": item.memory_type
            }

            # Store the item
            await self.client.hset(key, mapping={
                "data": json.dumps(value),
                "content": item.content,  # Store separately for text search
                "memory_type": item.memory_type,
                "timestamp": item.timestamp.isoformat()
            })

            # Add to type-based sets for efficient querying
            await self.client.sadd(f"{self.prefix}types:{item.memory_type}", item.id)

            # Set expiration (default 24 hours for cache)
            ttl = item.metadata.get("ttl", 86400)  # 24 hours in seconds
            await self.client.expire(key, ttl)

            return True

        except Exception as e:
            print(f"Error storing item in Redis: {e}")
            return False

    async def retrieve(self, query: MemoryQuery) -> MemoryResult:
        """Retrieve memory items from Redis"""
        start_time = time.time()

        try:
            await self._ensure_connection()

            # Get candidate items based on memory types
            candidate_ids = set()

            if query.memory_types:
                for memory_type in query.memory_types:
                    type_key = f"{self.prefix}types:{memory_type}"
                    ids = await self.client.smembers(type_key)
                    candidate_ids.update(ids)
            else:
                # Get all keys if no type filter
                pattern = f"{self.prefix}*"
                keys = await self.client.keys(pattern)
                candidate_ids = {key.replace(self.prefix, "") for key in keys
                               if not key.endswith(":types")}

            # Retrieve and filter items
            memory_items = []
            for item_id in candidate_ids:
                key = f"{self.prefix}{item_id}"
                item_data = await self.client.hgetall(key)

                if not item_data:
                    continue

                # Parse the stored data
                data = json.loads(item_data.get("data", "{}"))

                # Simple text matching for query
                content = data.get("content", "").lower()
                query_lower = query.query.lower()

                # Calculate simple relevance score
                relevance = 0.0
                if query.query:
                    query_terms = query_lower.split()
                    for term in query_terms:
                        relevance += content.count(term)
                    relevance = min(relevance / len(query_terms), 1.0)
                else:
                    relevance = 1.0  # If no query, all items are relevant

                if relevance >= query.similarity_threshold:
                    memory_item = MemoryItem(
                        id=item_id,
                        content=data["content"],
                        metadata=data.get("metadata", {}),
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        memory_type=data["memory_type"]
                    )
                    memory_item.metadata["relevance_score"] = relevance
                    memory_items.append(memory_item)

            # Sort by relevance and limit results
            memory_items.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
            memory_items = memory_items[:query.limit]

            query_time = time.time() - start_time

            return MemoryResult(
                items=memory_items,
                total_count=len(memory_items),
                query_time=query_time
            )

        except Exception as e:
            print(f"Error retrieving from Redis: {e}")
            return MemoryResult(items=[], total_count=0, query_time=0.0)

    async def update(self, item_id: str, item: MemoryItem) -> bool:
        """Update an existing memory item"""
        try:
            # Delete old item
            await self.delete(item_id)

            # Store updated item with same ID
            updated_item = item.copy()
            updated_item.id = item_id
            return await self.store(updated_item)

        except Exception as e:
            print(f"Error updating item in Redis: {e}")
            return False

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item from Redis"""
        try:
            await self._ensure_connection()

            key = f"{self.prefix}{item_id}"

            # Get the item to find its type
            item_data = await self.client.hgetall(key)
            if item_data:
                memory_type = item_data.get("memory_type")
                if memory_type:
                    # Remove from type set
                    await self.client.srem(f"{self.prefix}types:{memory_type}", item_id)

            # Delete the item
            deleted_count = await self.client.delete(key)
            return deleted_count > 0

        except Exception as e:
            print(f"Error deleting item from Redis: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all memory items"""
        try:
            await self._ensure_connection()

            # Get all keys with our prefix
            keys = await self.client.keys(f"{self.prefix}*")
            if keys:
                await self.client.delete(*keys)

            return True

        except Exception as e:
            print(f"Error clearing Redis cache: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            await self._ensure_connection()

            # Count all items
            keys = await self.client.keys(f"{self.prefix}*")
            data_keys = [k for k in keys if not ":types:" in k]

            # Get memory types
            type_keys = [k for k in keys if ":types:" in k]
            memory_types = [k.split(":types:")[-1] for k in type_keys]

            # Get Redis info
            info = await self.client.info()

            return {
                "total_items": len(data_keys),
                "memory_types": memory_types,
                "redis_memory_used": info.get("used_memory_human", "Unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
                "prefix": self.prefix
            }

        except Exception as e:
            return {"error": str(e)}

    async def set_ttl(self, item_id: str, ttl: int) -> bool:
        """Set TTL for a specific item"""
        try:
            await self._ensure_connection()
            key = f"{self.prefix}{item_id}"
            return await self.client.expire(key, ttl)

        except Exception as e:
            print(f"Error setting TTL: {e}")
            return False

    async def extend_ttl(self, item_id: str, additional_seconds: int) -> bool:
        """Extend TTL for a specific item"""
        try:
            await self._ensure_connection()
            key = f"{self.prefix}{item_id}"
            current_ttl = await self.client.ttl(key)

            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                return await self.client.expire(key, new_ttl)

            return False

        except Exception as e:
            print(f"Error extending TTL: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()