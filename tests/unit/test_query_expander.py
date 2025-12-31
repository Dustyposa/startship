import pytest
from src.services.query_expander import QueryExpander

@pytest.mark.asyncio
async def test_expand_with_synonyms():
    expander = QueryExpander()
    queries = await expander.expand("ml 项目")

    assert len(queries) > 1
    assert "ml 项目" in queries  # Original query preserved
    assert any("机器学习" in q for q in queries)

@pytest.mark.asyncio
async def test_expand_no_synonyms():
    expander = QueryExpander()
    queries = await expander.expand("random query")

    assert len(queries) == 1
    assert queries[0] == "random query"
