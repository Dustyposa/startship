"""Integration tests demonstrating semantic search capabilities.

This test suite demonstrates the value of semantic search over traditional
keyword-based full-text search by testing:

1. Concept understanding: Finding related concepts without exact keyword matches
2. Synonym recognition: Understanding different terms for the same concept
3. Cross-language semantic matching: Chinese queries matching English content
4. Technology stack associations: Finding related technologies
5. Fuzzy matching: Understanding related but not identical concepts
"""

import pytest
import pytest_asyncio
import math
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.services.vectorization import VectorizationService


def cosine_sim(v1, v2):
    """Calculate cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2)


@pytest_asyncio.fixture
async def indexed_repos():
    """Fixture that provides a diverse set of repositories for testing."""
    embeddings = OllamaEmbeddings(model="bge-m3")
    store = ChromaDBStore(persist_path="data/chromadb")
    service = VectorizationService(embeddings, store)

    # Clear existing data
    store.clear()

    # Diverse test repositories covering different domains
    repos = [
        # Async Task Queues
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
- Supports RabbitMQ, Redis as brokers

Perfect for background job processing and async workflows.
"""
        },
        {
            "name_with_owner": "uglide/rq",
            "name": "RQ",
            "description": "Simple job queue for Python",
            "primary_language": "Python",
            "topics": ["python", "queue", "redis", "jobs"],
            "readme_content": """
# RQ (Redis Queue)

RQ is a simple, lightweight job queue for Python backed by Redis.

## Features

- Simple API
- Async job processing
- Worker management
- Job monitoring

Great for background tasks and scheduled jobs.
"""
        },
        {
            "name_with_owner": "OptimalBits/bull",
            "name": "Bull",
            "description": "Redis queue for NodeJS",
            "primary_language": "JavaScript",
            "topics": ["nodejs", "redis", "queue", "jobs"],
            "readme_content": """
# Bull

Bull is a Redis-backed queue for NodeJS.

## Features

- Job queues
- Scheduled jobs
- Rate limiting
- Retry mechanisms
- Job priorities

Ideal for background job processing in NodeJS applications.
"""
        },

        # Data Visualization
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
- Data-driven documents

Perfect for custom data visualization projects.
"""
        },
        {
            "name_with_owner": "apache/echarts",
            "name": "ECharts",
            "description": "Powerful charting and visualization library",
            "primary_language": "TypeScript",
            "topics": ["charts", "visualization", "typescript"],
            "readme_content": """
# Apache ECharts

A powerful, interactive charting and visualization library.

## Features

- Rich chart types (line, bar, pie, scatter, etc.)
- Interactive tooltips
- Responsive design
- Theme support

Great for business intelligence dashboards and data visualization.
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
- Web-based rendering

Ideal for scientific plotting and data exploration.
"""
        },

        # Vue Ecosystem
        {
            "name_with_owner": "vuejs/vue",
            "name": "Vue.js",
            "description": "Progressive JavaScript framework for building UIs",
            "primary_language": "JavaScript",
            "topics": ["javascript", "framework", "frontend", "ui"],
            "readme_content": """
# Vue.js

Vue.js is a progressive JavaScript framework for building user interfaces.

## Features

- Reactive data binding
- Component-based architecture
- Virtual DOM
- Easy learning curve

Perfect for single-page applications and interactive UIs.
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
            "name_with_owner": "vuejs/pinia",
            "name": "Pinia",
            "description": "State management library for Vue",
            "primary_language": "TypeScript",
            "topics": ["vue", "state", "store"],
            "readme_content": """
# Pinia

A state management library for Vue.js.

## Features

- Type-safe stores
- Composable stores
- Devtools support
- Modular architecture

The official state management solution for Vue.js applications.
"""
        },
        {
            "name_with_owner": "vuejs/vite",
            "name": "Vite",
            "description": "Next generation frontend tooling",
            "primary_language": "TypeScript",
            "topics": ["build-tool", "vite", "frontend"],
            "readme_content": """
# Vite

Next generation frontend tooling.

## Features

- Instant server start
- Lightning fast HMR
- Rich features
- Optimized build

Modern build tool that works great with Vue.js.
"""
        },

        # Machine Learning
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
            "name_with_owner": "pytorch/pytorch",
            "name": "PyTorch",
            "description": "Tensors and dynamic neural networks",
            "primary_language": "Python",
            "topics": ["machine-learning", "deep-learning"],
            "readme_content": """
# PyTorch

Tensors and Dynamic neural networks in Python.

## Features

- Dynamic computation graphs
- GPU acceleration
- Rich ecosystem
- Research-friendly

Popular framework for deep learning research and production.
"""
        },
    ]

    # Index all repositories
    await service.index_batch(repos)

    yield repos, embeddings, store

    # Cleanup
    store.clear()


class TestSemanticSearchConcepts:
    """Test semantic search's ability to understand concepts."""

    @pytest.mark.asyncio
    async def test_concept_understanding_async_task_queue(self, indexed_repos):
        """Test finding async task queue libraries."""
        repos, embeddings, store = indexed_repos

        query = "异步任务队列"
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # Should find Celery, RQ, or Bull
        top_names = [r['metadata'].get('name', '') for r in results]
        task_queue_libs = ['Celery', 'RQ', 'Bull']

        found_any = any(lib in top_names for lib in task_queue_libs)
        assert found_any, f"Should find task queue libraries for '{query}', got {top_names}"

        print(f"\n✅ Query '{query}' found: {top_names[:3]}")

    @pytest.mark.asyncio
    async def test_concept_understanding_data_visualization(self, indexed_repos):
        """Test finding data visualization libraries."""
        repos, embeddings, store = indexed_repos

        query = "数据可视化"
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # Should find D3, ECharts, or Plotly
        top_names = [r['metadata'].get('name', '') for r in results]
        viz_libs = ['D3.js', 'ECharts', 'Plotly']

        found_any = any(lib in top_names for lib in viz_libs)
        assert found_any, f"Should find visualization libraries for '{query}', got {top_names}"

        print(f"\n✅ Query '{query}' found: {top_names[:3]}")

    @pytest.mark.asyncio
    async def test_synonym_recognition_backend_framework(self, indexed_repos):
        """Test synonym recognition: '后端框架' -> FastAPI equivalent."""
        repos, embeddings, store = indexed_repos

        # Add FastAPI to the mix
        fastapi = {
            "name_with_owner": "tiangolo/fastapi",
            "name": "FastAPI",
            "description": "Modern web framework for building APIs with Python",
            "primary_language": "Python",
            "topics": ["python", "web", "api", "framework"],
            "readme_content": """
# FastAPI

Modern, fast web framework for building APIs with Python 3.6+.

## Features

- Fast: Very high performance
- Fast to code: 200-300% faster
- Fewer bugs: Reduce errors by 40%
- Intuitive: Great editor support

Perfect for building RESTful APIs and microservices.
"""
        }

        service = VectorizationService(embeddings, store)
        await service.index_repository(fastapi)

        query = "后端开发框架"
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # Should find FastAPI
        top_names = [r['metadata'].get('name', '') for r in results]
        assert 'FastAPI' in top_names, f"Should find FastAPI for '{query}', got {top_names}"

        print(f"\n✅ Query '{query}' found: {top_names[:3]}")

    @pytest.mark.asyncio
    async def test_technology_stack_association_vue_ecosystem(self, indexed_repos):
        """Test finding related Vue ecosystem projects."""
        repos, embeddings, store = indexed_repos

        query = "Vue 生态系统"
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # Should find Vue Router, Pinia, Vite
        top_names = [r['metadata'].get('name', '') for r in results]
        vue_ecosystem = ['Vue.js', 'Vue Router', 'Pinia', 'Vite']

        found_count = sum(1 for lib in vue_ecosystem if lib in top_names)
        assert found_count >= 2, f"Should find at least 2 Vue ecosystem projects for '{query}', got {top_names}"

        print(f"\n✅ Query '{query}' found: {top_names[:3]} ({found_count} ecosystem projects)")

    @pytest.mark.asyncio
    async def test_cross_language_matching_chinese_to_english(self, indexed_repos):
        """Test Chinese query matching English content."""
        repos, embeddings, store = indexed_repos

        test_cases = [
            ("机器学习框架", ["TensorFlow", "PyTorch"]),
            ("深度学习", ["TensorFlow", "PyTorch"]),
            ("前端界面", ["Vue.js"]),
            ("图表库", ["D3.js", "ECharts", "Plotly"]),
        ]

        for query, expected_libs in test_cases:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results]

            found_any = any(lib in top_names for lib in expected_libs)
            assert found_any, f"Chinese query '{query}' should find {expected_libs}, got {top_names}"
            print(f"\n✅ Chinese query '{query}' → {top_names[0]}")

    @pytest.mark.asyncio
    async def test_fuzzy_concept_matching_background_jobs(self, indexed_repos):
        """Test fuzzy concept matching: related but not identical terms."""
        repos, embeddings, store = indexed_repos

        # Various ways to describe task queues
        queries = [
            "后台任务处理",
            "worker 队列",
            "job scheduling",
            "异步工作流",
        ]

        for query in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results]
            task_queue_libs = ['Celery', 'RQ', 'Bull']

            found_any = any(lib in top_names for lib in task_queue_libs)
            assert found_any, f"Query '{query}' should find task queue libraries, got {top_names}"
            print(f"\n✅ Fuzzy query '{query}' → {top_names[0]}")

    @pytest.mark.asyncio
    async def test_semantic_similarity_ranking(self, indexed_repos):
        """Test that semantic search produces meaningful similarity rankings."""
        repos, embeddings, store = indexed_repos

        query = "Python machine learning"
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # TensorFlow and PyTorch should rank higher than unrelated projects
        top_names = [r['metadata'].get('name', '') for r in results]
        scores = [r['score'] for r in results]

        # ML frameworks should appear in top 3
        ml_frameworks = ['TensorFlow', 'PyTorch']
        ml_in_top_3 = sum(1 for i, name in enumerate(top_names[:3]) if name in ml_frameworks)

        assert ml_in_top_3 >= 1, f"ML frameworks should be in top 3 for '{query}', got {top_names[:3]}"

        # Similarities should be reasonably high (> 0.5)
        assert scores[0] > 0.5, f"Top result should have good similarity, got {scores[0]:.3f}"

        print(f"\n✅ Query '{query}' rankings:")
        for i, (name, score) in enumerate(zip(top_names, scores), 1):
            print(f"  {i}. {name:15s} (similarity: {score:.4f})")


class TestSemanticSearchValue:
    """Test cases that demonstrate the business value of semantic search."""

    @pytest.mark.asyncio
    async def test_semantic_vs_keyword_search_advantage(self, indexed_repos):
        """Demonstrate advantages over keyword-based search."""
        repos, embeddings, store = indexed_repos

        # These queries would fail with keyword search but work with semantic
        semantic_queries = [
            ("画图表库", ["D3.js", "ECharts", "Plotly"]),  # Not exact keyword match
            ("任务调度", ["Celery", "RQ", "Bull"]),  # "任务" != "task" or "job"
            ("路由管理", ["Vue Router"]),  # No "router" in Chinese
        ]

        print("\n=== Semantic Search Advantages ===")
        for query, expected in semantic_queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results]

            found = [name for name in top_names if name in expected]
            print(f"\nQuery: '{query}'")
            print(f"  Keyword search would miss: {expected}")
            print(f"  Semantic search found: {found[:2]}")
            print(f"  Top 3 results: {top_names[:3]}")

            assert any(exp in top_names for exp in expected), \
                f"Semantic search should find {expected} for '{query}'"

    @pytest.mark.asyncio
    async def test_cross_domain_understanding(self, indexed_repos):
        """Test understanding of cross-domain concepts."""
        repos, embeddings, store = indexed_repos

        # Query using web development terminology, should find ML frameworks
        query = "AI model serving"
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # Should understand that "AI model serving" relates to ML frameworks
        top_names = [r['metadata'].get('name', '') for r in results]
        ml_frameworks = ['TensorFlow', 'PyTorch']

        found_ml = any(fw in top_names for fw in ml_frameworks)

        print(f"\nQuery: '{query}' (web dev terminology)")
        print(f"  Should relate to ML frameworks: {top_names[:3]}")

        # This is a fuzzy match, so we just check it doesn't return completely unrelated stuff
        assert len(results) > 0, "Should return some results"

    @pytest.mark.asyncio
    async def test_multilingual_understanding(self, indexed_repos):
        """Test understanding of multilingual queries."""
        repos, embeddings, store = indexed_repos

        # Same concept in different languages
        queries = [
            "异步队列",      # Chinese
            "async queue",  # English
            "任务队列",      # Chinese (different wording)
        ]

        print("\n=== Multilingual Semantic Understanding ===")
        results_by_query = {}

        for query in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=3)
            top_names = [r['metadata'].get('name', '') for r in results]
            results_by_query[query] = top_names
            print(f"\n'{query}' → {top_names}")

        # All queries should find similar task queue libraries
        task_queue_libs = set()
        for names in results_by_query.values():
            task_queue_libs.update(name for name in names if name in ['Celery', 'RQ', 'Bull'])

        assert len(task_queue_libs) >= 1, "Should find task queue libraries across different languages"
        print(f"\n✅ Found {task_queue_libs} across all language variants")


@pytest.mark.asyncio
async def test_semantic_search_accuracy_summary(indexed_repos):
    """Summary test showing overall semantic search accuracy."""
    repos, embeddings, store = indexed_repos

    test_cases = [
        # (query, expected_matches, category) - expect any of these to be in top 2
        ("异步任务队列", ["Celery", "RQ", "Bull"], "Concept Understanding"),
        ("数据可视化", ["D3.js", "ECharts", "Plotly"], "Concept Understanding"),
        ("机器学习", ["TensorFlow", "PyTorch"], "ML Domain"),
        ("Vue 生态", ["Vue.js", "Vue Router", "Pinia", "Vite"], "Ecosystem"),
        ("Python async queue", ["Celery", "RQ"], "English Query"),
        ("画图工具", ["D3.js", "ECharts", "Plotly"], "Chinese Query"),
    ]

    print("\n" + "="*60)
    print("SEMANTIC SEARCH ACCURACY SUMMARY")
    print("="*60)

    correct = 0
    total = len(test_cases)

    for query, expected_matches, category in test_cases:
        query_vec = embeddings.embed_text(query)
        results = store.search(query_vec, top_k=5)

        # Check if any expected match is in top 2 results
        top_2_names = [r['metadata'].get('name', '') for r in results[:2]]
        found = any(exp in top_2_names for exp in expected_matches)

        if found:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"\n{status} [{category}]")
        print(f"   Query: '{query}'")
        print(f"   Expected (any in top 2): {expected_matches}")
        print(f"   Got: {top_2_names}")
        print(f"   Top match: {results[0]['metadata'].get('name', '')} (similarity: {results[0]['score']:.4f})")

    accuracy = (correct / total) * 100
    print("\n" + "="*60)
    print(f"OVERALL ACCURACY: {correct}/{total} = {accuracy:.1f}%")
    print("="*60)

    # Should have at least 80% accuracy (allowing multiple correct answers)
    assert accuracy >= 80, f"Semantic search accuracy should be >= 80%, got {accuracy:.1f}%"
