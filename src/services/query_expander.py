import json
from pathlib import Path


class QueryExpander:
    """Expands queries using synonym library."""

    def __init__(self, synonyms_path: str | None = None) -> None:
        if synonyms_path is None:
            synonyms_path = Path(__file__).parent.parent / "data" / "synonyms.json"
        self.synonyms_path = Path(synonyms_path)
        self._synonyms = self._load_synonyms()

    def _load_synonyms(self) -> dict[str, list[str]]:
        """Load synonyms from JSON file."""
        if not self.synonyms_path.exists():
            return {}
        with open(self.synonyms_path, encoding="utf-8") as f:
            return json.load(f)

    async def expand(self, query: str, max_expansions: int = 3) -> list[str]:
        """
        Expand query using synonyms.

        Args:
            query: Original query
            max_expansions: Maximum number of expanded queries

        Returns:
            List of expanded queries (original + variations)
        """
        expansions = [query]

        for term, synonyms in self._synonyms.items():
            if term.lower() in query.lower():
                for synonym in synonyms[:max_expansions]:
                    expanded = query.lower().replace(term.lower(), synonym)
                    if expanded not in expansions:
                        expansions.append(expanded)

        return expansions
