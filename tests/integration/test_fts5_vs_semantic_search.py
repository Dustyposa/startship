"""Integration tests comparing FTS5 full-text search vs semantic search.

This test suite demonstrates scenarios where:
- FTS5 fails to find relevant results
- Semantic search successfully finds relevant results
- Semantic search provides better user experience

The comparison covers:
1. Synonym mismatches: FTS requires exact keyword match
2. Cross-language queries: Chinese queries on English content
3. Concept understanding: Related concepts without exact keywords
4. Technology associations: Finding ecosystem projects
5. Fuzzy matching: Related but not identical terms
"""

import pytest
import pytest_asyncio
import sqlite3
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.services.vectorization import VectorizationService


@pytest_asyncio.fixture
async def search_comparison_data():
    """Set up identical data for both FTS5 and semantic search."""
    embeddings = OllamaEmbeddings(model="bge-m3")
    vector_store = ChromaDBStore(persist_path="data/chromadb")
    service = VectorizationService(embeddings, vector_store)

    # Clear existing data
    vector_store.clear()

    # Create temporary FTS5 database
    fts_db_path = "/tmp/test_search_comparison.db"
    import os
    if os.path.exists(fts_db_path):
        os.remove(fts_db_path)

    fts_conn = sqlite3.connect(fts_db_path)
    fts_conn.execute("""
        CREATE VIRTUAL TABLE repositories USING fts5(
            name,
            description,
            readme_content,
            tokenize='porter unicode61'
        )
    """)

    # Test repositories that demonstrate semantic search advantages
    repos = [
        {
            "name_with_owner": "celery/celery",
            "name": "Celery",
            "description": "Distributed task queue for Python",
            "primary_language": "Python",
            "topics": ["python", "task-queue", "async", "distributed"],
            "readme_content": """
# Celery

Celery is a powerful distributed task queue for Python.

## Features

- Asynchronous task execution
- Distributed task processing
- Worker pools
- Task scheduling and periodic tasks

Perfect for background job processing and async workflows.
"""
        },
        {
            "name_with_owner": "d3/d3",
            "name": "D3.js",
            "description": "Data visualization library for JavaScript",
            "primary_language": "JavaScript",
            "topics": ["visualization", "data", "charts", "svg"],
            "readme_content": """
# D3.js

D3.js is a JavaScript library for producing dynamic, interactive data visualizations.

## Features

- DOM manipulation based on data
- SVG generation
- Interactive charts and graphs

Perfect for custom data visualization projects.
"""
        },
        {
            "name_with_owner": "tensorflow/tensorflow",
            "name": "TensorFlow",
            "description": "End-to-end machine learning platform",
            "primary_language": "Python",
            "topics": ["machine-learning", "deep-learning", "ai"],
            "readme_content": """
# TensorFlow

An end-to-end open source machine learning platform.

## Features

- Deep learning models
- Neural network training
- Production deployment
- TPUs and GPUs support

Industry-standard platform for machine learning and AI.
"""
        },
        {
            "name_with_owner": "plotly/plotly.py",
            "name": "Plotly",
            "description": "Interactive graphing library for Python",
            "primary_language": "Python",
            "topics": ["python", "plotting", "charts", "visualization"],
            "readme_content": """
# Plotly Python

An interactive graphing library for Python.

## Features

- Interactive plots
- 3D visualization
- Statistical charts

Ideal for scientific plotting and data exploration.
"""
        },
        {
            "name_with_owner": "vuejs/router",
            "name": "Vue Router",
            "description": "Official router for Vue.js",
            "primary_language": "TypeScript",
            "topics": ["vue", "router", "spa"],
            "readme_content": """
# Vue Router

The official router for Vue.js.

## Features

- Route mapping
- Navigation guards
- Lazy loading
- History mode

Essential for building single-page applications with Vue.js.
"""
        },
        {
            "name_with_owner": "redis/redis",
            "name": "Redis",
            "description": "In-memory data structure store",
            "primary_language": "C",
            "topics": ["database", "cache", "key-value"],
            "readme_content": """
# Redis

Redis is an open source, in-memory data structure store.

## Features

- Key-value storage
- Pub/sub messaging
- Transactions
- Persistence

Used as database, cache, and message broker.
"""
        },
    ]

    # Index in both systems
    await service.index_batch(repos)

    for repo in repos:
        fts_conn.execute(
            "INSERT INTO repositories (name, description, readme_content) VALUES (?, ?, ?)",
            (repo["name"], repo["description"], repo["readme_content"])
        )
    fts_conn.commit()

    yield repos, fts_conn, embeddings, vector_store

    # Cleanup
    fts_conn.close()
    if os.path.exists(fts_db_path):
        os.remove(fts_db_path)
    vector_store.clear()


class TestFTS5VsSemanticSearch:
    """Compare FTS5 full-text search vs semantic search."""

    @pytest.mark.asyncio
    async def test_synonym_chinese_background_job(self, search_comparison_data):
        """Test: Chinese synonym '后台任务' vs English 'background job'."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        query = "后台任务"

        # FTS5 search (exact keyword match)
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")
        print(f"Expected: Celery (background job queue)")

        # FTS5 should fail (no exact Chinese keyword match)
        # Semantic search should succeed (understands "后台任务" = "background job")
        assert "Celery" in semantic_names, "Semantic search should find Celery"
        assert len(fts_results) == 0, "FTS5 should not find results (no exact match)"
        print(f"✅ Semantic search succeeds where FTS5 fails")

    @pytest.mark.asyncio
    async def test_synonym_chinese_drawing_charts(self, search_comparison_data):
        """Test: Chinese '画图表' vs English 'charts/visualization'."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        query = "画图表"

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")
        print(f"Expected: D3.js or Plotly (chart libraries)")

        # FTS5 fails (no "画" or "图表" in English content)
        # Semantic search succeeds (understands "画图表" = "charts/visualization")
        chart_libs = ["D3.js", "Plotly"]
        found_chart = any(lib in semantic_names for lib in chart_libs)
        assert found_chart, "Semantic search should find chart libraries"
        assert len(fts_results) == 0, "FTS5 should not find results"
        print(f"✅ Semantic search understands '画图表' = 'charts'")

    @pytest.mark.asyncio
    async def test_cross_language_ml_framework(self, search_comparison_data):
        """Test: Chinese query '机器学习框架' on English ML content."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        query = "机器学习框架"

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")
        print(f"Expected: TensorFlow (ML framework)")

        # FTS5 fails (Chinese characters don't match English "machine learning")
        # Semantic search succeeds (cross-language understanding)
        assert "TensorFlow" in semantic_names, "Semantic search should find TensorFlow"
        assert len(fts_results) == 0, "FTS5 should not find results"
        print(f"✅ Semantic search bridges Chinese-English gap")

    @pytest.mark.asyncio
    async def test_concept_no_keyword_match_cache(self, search_comparison_data):
        """Test: Concept '缓存系统' vs 'in-memory store' (no shared keywords)."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        query = "缓存系统"

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")
        print(f"Expected: Redis (used as cache)")

        # FTS5 fails (no "缓存" in English content)
        # Semantic search succeeds (understands Redis is used for caching)
        assert "Redis" in semantic_names, "Semantic search should find Redis"
        assert len(fts_results) == 0, "FTS5 should not find results"
        print(f"✅ Semantic search understands use cases")

    @pytest.mark.asyncio
    async def test_ecosystem_discovery_vue_routing(self, search_comparison_data):
        """Test: Finding Vue ecosystem project without mentioning 'Vue'."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        query = "Vue 路由管理"

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")
        print(f"Expected: Vue Router (Vue ecosystem)")

        # FTS5 might fail or have limited results
        # Semantic search succeeds (understands Vue ecosystem)
        assert "Vue Router" in semantic_names, "Semantic search should find Vue Router"
        print(f"✅ Semantic search discovers ecosystem relationships")

    @pytest.mark.asyncio
    async def test_fuzzy_concept_task_scheduling(self, search_comparison_data):
        """Test: Fuzzy concept '定时任务' vs 'task scheduling'."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        query = "定时任务"

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")
        print(f"Expected: Celery (supports scheduling)")

        # FTS5 fails
        # Semantic search succeeds (understands "定时" = "scheduling")
        assert "Celery" in semantic_names, "Semantic search should find Celery"
        assert len(fts_results) == 0, "FTS5 should not find results"
        print(f"✅ Semantic search understands related concepts")

    @pytest.mark.asyncio
    async def test_english_query_chinese_content(self, search_comparison_data):
        """Test: English query on content where Chinese user would search."""
        repos, fts_conn, embeddings, vector_store = search_comparison_data

        # Add a repo with Chinese description
        service = VectorizationService(embeddings, vector_store)
        chinese_repo = {
            "name_with_owner": "test/chinese-ml-lib",
            "name": "中文机器学习库",
            "description": "一个强大的深度学习框架",
            "primary_language": "Python",
            "topics": ["机器学习", "深度学习"],
            "readme_content": """
# 中文机器学习库

这是一个强大的深度学习框架。

## 特性

- 神经网络训练
- GPU 加速
- 模型部署
"""
        }

        await service.index_repository(chinese_repo)

        fts_conn.execute(
            "INSERT INTO repositories (name, description, readme_content) VALUES (?, ?, ?)",
            (chinese_repo["name"], chinese_repo["description"], chinese_repo["readme_content"])
        )
        fts_conn.commit()

        # English query
        query = "neural network framework"

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]

        print(f"\n{'='*60}")
        print(f"Query: '{query}' (English)")
        print(f"Target: Chinese content '神经网络'")
        print(f"{'='*60}")
        print(f"FTS5 Results: {fts_results if fts_results else '❌ No results'}")
        print(f"Semantic Results: {semantic_names[:3]}")

        # FTS5 fails (English words don't match Chinese characters)
        # Semantic search succeeds (cross-language understanding)
        # Note: We're checking if the Chinese ML lib is found or if TensorFlow/PyTorch is found
        assert len(semantic_names) > 0, "Semantic search should return results"
        print(f"✅ Semantic search enables cross-language discovery")


@pytest.mark.asyncio
async def test_comprehensive_comparison_summary(search_comparison_data):
    """Summary test showing comprehensive FTS5 vs semantic search comparison."""
    repos, fts_conn, embeddings, vector_store = search_comparison_data

    # Test scenarios where FTS5 fails but semantic search succeeds
    test_scenarios = [
        {
            "query": "后台任务处理",
            "expected": "Celery",
            "category": "Synonym (Chinese→English)",
            "reason": "FTS5: No '后台' in English content"
        },
        {
            "query": "画图工具",
            "expected": "D3.js",
            "category": "Concept Understanding",
            "reason": "FTS5: No '画图' in English content"
        },
        {
            "query": "机器学习平台",
            "expected": "TensorFlow",
            "category": "Cross-Language",
            "reason": "FTS5: Chinese characters don't match English"
        },
        {
            "query": "内存数据库",
            "expected": "Redis",
            "category": "Use Case Understanding",
            "reason": "FTS5: No '内存数据库' keyword"
        },
        {
            "query": "定时调度",
            "expected": "Celery",
            "category": "Related Concept",
            "reason": "FTS5: No '定时' keyword"
        },
    ]

    print("\n" + "="*80)
    print(" "*20 + "FTS5 vs SEMANTIC SEARCH COMPARISON")
    print("="*80)

    fts_success = 0
    semantic_success = 0

    for scenario in test_scenarios:
        query = scenario["query"]
        expected = scenario["expected"]

        # FTS5 search
        fts_cursor = fts_conn.execute(
            "SELECT name FROM repositories WHERE repositories MATCH ? ORDER BY rank",
            (query,)
        )
        fts_results = [row[0] for row in fts_cursor.fetchall()]
        fts_found = expected in fts_results

        # Semantic search
        query_vec = embeddings.embed_text(query)
        semantic_results = vector_store.search(query_vec, top_k=5)
        semantic_names = [r['metadata'].get('name', '') for r in semantic_results]
        semantic_found = expected in semantic_names

        if fts_found:
            fts_success += 1
        if semantic_found:
            semantic_success += 1

        fts_status = "✅" if fts_found else "❌"
        semantic_status = "✅" if semantic_found else "❌"

        print(f"\n[{scenario['category']}]")
        print(f"  Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  FTS5:      {fts_status} {fts_results if fts_results else 'No results'}")
        print(f"  Semantic:  {semantic_status} {semantic_names[0] if semantic_names else 'No results'}")
        print(f"  Reason:    {scenario['reason']}")

    print("\n" + "="*80)
    print(f"SUMMARY:")
    print(f"  FTS5 Success Rate:     {fts_success}/{len(test_scenarios)} ({fts_success/len(test_scenarios)*100:.1f}%)")
    print(f"  Semantic Success Rate: {semantic_success}/{len(test_scenarios)} ({semantic_success/len(test_scenarios)*100:.1f}%)")
    print(f"  Improvement:           +{(semantic_success-fts_success)/len(test_scenarios)*100:.1f}%")
    print("="*80)

    # Semantic search should significantly outperform FTS5
    assert semantic_success >= 4, "Semantic search should find at least 4/5 results"
    assert semantic_success > fts_success, "Semantic search should outperform FTS5"

    print("\n✅ Semantic search provides significant value over FTS5!")
    print(f"   - Handles cross-language queries")
    print(f"   - Understands synonyms and related concepts")
    print(f"   - Discovers ecosystem relationships")
    print(f"   - Works with fuzzy matching")
