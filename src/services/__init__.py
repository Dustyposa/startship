"""Services package for business logic."""

# Try to import services, handle missing dependencies gracefully
try:
    from .init import InitializationService
except ImportError:
    InitializationService = None

try:
    from .query_expander import QueryExpander
except ImportError:
    QueryExpander = None

try:
    from .search import SearchService
except ImportError:
    SearchService = None

__all__ = []

if InitializationService is not None:
    __all__.append("InitializationService")

if QueryExpander is not None:
    __all__.append("QueryExpander")

if SearchService is not None:
    __all__.append("SearchService")
