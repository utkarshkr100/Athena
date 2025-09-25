from .base_search import BaseSearchTool
from .web_search.tavily_search_tool import TavilySearchTool
from .web_search.bing_search_tool import BingSearchTool

# Optional Azure imports
try:
    from .azure_search.azure_search_tool import AzureSearchTool
    _AZURE_AVAILABLE = True
except ImportError:
    AzureSearchTool = None
    _AZURE_AVAILABLE = False

__all__ = [
    "BaseSearchTool",
    "TavilySearchTool",
    "BingSearchTool"
]

if _AZURE_AVAILABLE:
    __all__.append("AzureSearchTool")