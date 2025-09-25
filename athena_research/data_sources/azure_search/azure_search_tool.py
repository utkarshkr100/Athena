from typing import List, Dict, Any, Optional
import asyncio
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
from ..base_search import BaseSearchTool
from ...agents.research.research_agent import SearchResult
from ...config import settings

class AzureSearchTool(BaseSearchTool):
    def __init__(self, service_name: str = None, api_key: str = None, index_name: str = None):
        super().__init__("AzureSearch")

        self.service_name = service_name or settings.azure_search_service_name
        self.api_key = api_key or settings.azure_search_api_key
        self.index_name = index_name or settings.azure_search_index_name

        if not all([self.service_name, self.api_key, self.index_name]):
            raise ValueError("Azure Search configuration is incomplete")

        self.endpoint = f"https://{self.service_name}.search.windows.net"
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.api_key)
        )

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search the Azure Search index"""
        try:
            # Perform the search
            results = await self.search_client.search(
                search_text=query,
                top=max_results,
                include_total_count=True,
                search_mode="all"
            )

            search_results = []
            async for result in results:
                search_result = self._convert_azure_result(result)
                search_results.append(search_result)

            return search_results

        except Exception as e:
            print(f"Azure Search error: {e}")
            return []

    async def vector_search(
        self,
        query: str,
        vector: List[float],
        max_results: int = 10
    ) -> List[SearchResult]:
        """Perform vector search using embeddings"""
        try:
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=max_results,
                fields="content_vector"  # Assuming your index has this field
            )

            results = await self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                top=max_results,
                include_total_count=True
            )

            search_results = []
            async for result in results:
                search_result = self._convert_azure_result(result)
                search_results.append(search_result)

            return search_results

        except Exception as e:
            print(f"Azure Vector Search error: {e}")
            return []

    async def hybrid_search(
        self,
        query: str,
        vector: Optional[List[float]] = None,
        max_results: int = 10
    ) -> List[SearchResult]:
        """Perform hybrid search combining text and vector search"""
        if vector:
            return await self.vector_search(query, vector, max_results)
        else:
            return await self.search(query, max_results)

    def _convert_azure_result(self, result: Dict[str, Any]) -> SearchResult:
        """Convert Azure Search result to our SearchResult format"""
        title = result.get("title", "Untitled Document")
        content = result.get("content", "")
        url = result.get("url", result.get("metadata_storage_path", ""))

        # Extract score if available
        score = result.get("@search.score", 0.0)

        metadata = {
            "search_score": score,
            "document_id": result.get("id", ""),
            "last_modified": result.get("last_modified", ""),
            "size": result.get("size", 0)
        }

        # Add any additional metadata fields
        for key, value in result.items():
            if key.startswith("metadata_") and key not in metadata:
                metadata[key] = value

        return self._create_search_result(
            title=title,
            content=content,
            url=url,
            source_type="azure_search",
            metadata=metadata
        )

    async def is_available(self) -> bool:
        """Check if Azure Search is properly configured and accessible"""
        try:
            # Try to get the index statistics
            result = await self.search_client.get_document_count()
            return isinstance(result, int) and result >= 0
        except Exception as e:
            print(f"Azure Search availability check failed: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index"""
        try:
            doc_count = await self.search_client.get_document_count()
            return {
                "document_count": doc_count,
                "service_name": self.service_name,
                "index_name": self.index_name,
                "endpoint": self.endpoint
            }
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        """Clean up the search client"""
        if hasattr(self.search_client, 'close'):
            await self.search_client.close()