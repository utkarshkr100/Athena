from pydantic import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AthenaSettings(BaseSettings):
    # Azure OpenAI
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

    # Azure AI Search
    azure_search_service_name: str = os.getenv("AZURE_SEARCH_SERVICE_NAME", "")
    azure_search_api_key: str = os.getenv("AZURE_SEARCH_API_KEY", "")
    azure_search_index_name: str = os.getenv("AZURE_SEARCH_INDEX_NAME", "")

    # Web Search
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    bing_search_api_key: str = os.getenv("BING_SEARCH_API_KEY", "")

    # Memory
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")

    # Advanced Memory
    mem0_api_key: Optional[str] = os.getenv("MEM0_API_KEY")

    # Model Configuration
    planning_model: str = os.getenv("PLANNING_MODEL", "gpt-4o")
    writing_model: str = os.getenv("WRITING_MODEL", "gpt-4")
    research_model: str = os.getenv("RESEARCH_MODEL", "gpt-3.5-turbo")
    default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4000"))

    class Config:
        env_file = ".env"

settings = AthenaSettings()