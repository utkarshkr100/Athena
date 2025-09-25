from typing import Any, Dict, List, Optional
import asyncio
import uuid
import time
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from ..base_memory import BaseMemoryStore, MemoryItem, MemoryQuery, MemoryResult
from ...config import settings

class ChromaMemoryStore(BaseMemoryStore):
    def __init__(self, persist_directory: str = None, collection_name: str = "athena_memory"):
        super().__init__("ChromaMemory")

        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Athena research memory store"}
            )

    async def store(self, item: MemoryItem) -> bool:
        """Store a memory item with vector embedding"""
        try:
            # Generate embedding for the content
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.embedding_model.encode(item.content).tolist()
            )

            # Prepare metadata for Chroma
            chroma_metadata = {
                "memory_type": item.memory_type,
                "timestamp": item.timestamp.isoformat(),
                **{k: str(v) for k, v in item.metadata.items()}  # Convert all to strings
            }

            # Store in Chroma
            await loop.run_in_executor(
                None,
                lambda: self.collection.add(
                    embeddings=[embedding],
                    documents=[item.content],
                    metadatas=[chroma_metadata],
                    ids=[item.id]
                )
            )

            return True

        except Exception as e:
            print(f"Error storing memory item: {e}")
            return False

    async def retrieve(self, query: MemoryQuery) -> MemoryResult:
        """Retrieve memory items using vector similarity search"""
        start_time = time.time()

        try:
            # Generate embedding for the query
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None,
                lambda: self.embedding_model.encode(query.query).tolist()
            )

            # Prepare where clause for filtering
            where_clause = {}
            if query.memory_types:
                where_clause["memory_type"] = {"$in": query.memory_types}

            # Query Chroma
            results = await loop.run_in_executor(
                None,
                lambda: self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=query.limit,
                    where=where_clause if where_clause else None
                )
            )

            # Convert results to MemoryItem objects
            memory_items = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0.0

                    # Filter by similarity threshold
                    similarity = 1.0 - distance  # Convert distance to similarity
                    if similarity >= query.similarity_threshold:
                        # Parse metadata
                        parsed_metadata = {k: v for k, v in metadata.items()
                                         if k not in ['memory_type', 'timestamp']}

                        memory_item = MemoryItem(
                            id=results['ids'][0][i],
                            content=doc,
                            metadata=parsed_metadata,
                            timestamp=datetime.fromisoformat(metadata['timestamp']),
                            memory_type=metadata['memory_type']
                        )
                        memory_item.metadata['similarity_score'] = similarity
                        memory_items.append(memory_item)

            query_time = time.time() - start_time

            return MemoryResult(
                items=memory_items,
                total_count=len(memory_items),
                query_time=query_time
            )

        except Exception as e:
            print(f"Error retrieving memory items: {e}")
            return MemoryResult(items=[], total_count=0, query_time=0.0)

    async def update(self, item_id: str, item: MemoryItem) -> bool:
        """Update an existing memory item"""
        try:
            # Delete the old item
            await self.delete(item_id)

            # Store the updated item with the same ID
            updated_item = item.copy()
            updated_item.id = item_id
            return await self.store(updated_item)

        except Exception as e:
            print(f"Error updating memory item: {e}")
            return False

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.collection.delete(ids=[item_id])
            )
            return True

        except Exception as e:
            print(f"Error deleting memory item: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all memory items"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.delete_collection(name=self.collection_name)
            )

            # Recreate the collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Athena research memory store"}
            )
            return True

        except Exception as e:
            print(f"Error clearing memory store: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        try:
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(
                None,
                lambda: self.collection.count()
            )

            return {
                "total_items": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "embedding_model": "all-MiniLM-L6-v2"
            }

        except Exception as e:
            return {"error": str(e)}

    async def get_items_by_type(self, memory_type: str, limit: int = 100) -> List[MemoryItem]:
        """Get all items of a specific type"""
        query = MemoryQuery(
            query="",  # Empty query to get all items
            memory_types=[memory_type],
            limit=limit,
            similarity_threshold=0.0  # Get all items
        )

        # For type-based retrieval, we'll query without embedding similarity
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.collection.get(
                    where={"memory_type": memory_type},
                    limit=limit
                )
            )

            memory_items = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i]
                    parsed_metadata = {k: v for k, v in metadata.items()
                                     if k not in ['memory_type', 'timestamp']}

                    memory_item = MemoryItem(
                        id=results['ids'][i],
                        content=doc,
                        metadata=parsed_metadata,
                        timestamp=datetime.fromisoformat(metadata['timestamp']),
                        memory_type=metadata['memory_type']
                    )
                    memory_items.append(memory_item)

            return memory_items

        except Exception as e:
            print(f"Error getting items by type: {e}")
            return []