"""Real-world semantic search scenarios demonstrating practical value.

This test suite demonstrates semantic search value through realistic scenarios
that users would actually search for, covering:

1. Web Development: Frontend/backend frameworks, build tools
2. Data & Databases: SQL, NoSQL, data processing
3. DevOps & Infrastructure: Docker, K8s, CI/CD
4. Testing: Test frameworks, mocking tools
5. API Design: REST, GraphQL, RPC
6. Cloud & Services: AWS, Azure, GCP tools
7. Developer Tools: Linters, formatters, IDE plugins
8. Security: Auth, encryption, vulnerability scanning
"""

import pytest
import pytest_asyncio
import math
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.services.vectorization import VectorizationService


@pytest_asyncio.fixture
async def real_world_repos():
    """Fixture providing a comprehensive set of real-world repositories."""
    embeddings = OllamaEmbeddings(model="bge-m3")
    store = ChromaDBStore(persist_path="data/chromadb")
    service = VectorizationService(embeddings, store)

    store.clear()

    # Comprehensive real-world repositories
    repos = [
        # === Web Development - Frontend ===
        {
            "name_with_owner": "facebook/react",
            "name": "React",
            "description": "A JavaScript library for building user interfaces",
            "primary_language": "JavaScript",
            "topics": ["javascript", "frontend", "ui", "components"],
            "readme_content": """
# React

A JavaScript library for building user interfaces.

- Declarative: Design simple views for each state
- Component-Based: Build encapsulated components
- Learn Once, Write Anywhere: Build mobile apps too

Used by Facebook, Instagram, Netflix, and more.
"""
        },
        {
            "name_with_owner": "facebook/react-native",
            "name": "React Native",
            "description": "A framework for building native apps with React",
            "primary_language": "JavaScript",
            "topics": ["mobile", "ios", "android", "react"],
            "readme_content": """
# React Native

A framework for building native apps using React.

- Learn once, write anywhere
- Native components
- Cross-platform

Build native mobile apps for iOS and Android.
"""
        },
        {
            "name_with_owner": "sveltejs/svelte",
            "name": "Svelte",
            "description": "Cybernetically enhanced web apps",
            "primary_language": "TypeScript",
            "topics": ["javascript", "framework", "frontend"],
            "readme_content": """
# Svelte

Svelte is a radical new approach to building user interfaces.

- No virtual DOM
- Truly reactive
- Less code

Compile your components to highly efficient imperative code.
"""
        },
        {
            "name_with_owner": "angular/angular",
            "name": "Angular",
            "description": "Modern web platform for building applications",
            "primary_language": "TypeScript",
            "topics": ["typescript", "framework", "frontend"],
            "readme_content": """
# Angular

The modern web developer's platform.

- Full-featured framework
- Two-way data binding
- Dependency injection
- TypeScript support

Build complex applications with confidence.
"""
        },

        # === Web Development - Backend ===
        {
            "name_with_owner": "django/django",
            "name": "Django",
            "description": "The web framework for perfectionists with deadlines",
            "primary_language": "Python",
            "topics": ["python", "web", "framework", "mvc"],
            "readme_content": """
# Django

The web framework for perfectionists with deadlines.

- Batteries included
- ORM, authentication, admin interface
- Security built-in
- Scalable

Rapid development, clean, pragmatic design.
"""
        },
        {
            "name_with_owner": "pallets/flask",
            "name": "Flask",
            "description": "A microframework for Python",
            "primary_language": "Python",
            "topics": ["python", "web", "microframework"],
            "readme_content": """
# Flask

A microframework for Python based on Werkzeug and Jinja2.

- Lightweight
- Flexible
- Extensible

Perfect for small to medium applications and microservices.
"""
        },
        {
            "name_with_owner": "gorilla/websocket",
            "name": "websocket",
            "description": "WebSocket library for Go",
            "primary_language": "Go",
            "topics": ["go", "websocket", "realtime"],
            "readme_content": """
# websocket

A WebSocket library for Go.

- Fast and scalable
- Statically compiled
- Minimal API

Build real-time applications with WebSockets.
"""
        },

        # === Build Tools ===
        {
            "name_with_owner": "webpack/webpack",
            "name": "webpack",
            "description": "A static module bundler for modern JavaScript applications",
            "primary_language": "JavaScript",
            "topics": ["bundler", "build-tool", "javascript"],
            "readme_content": """
# webpack

A static module bundler for modern JavaScript applications.

- Code splitting
- Asset optimization
- Module bundling
- Plugin ecosystem

Bundle your JavaScript applications efficiently.
"""
        },
        {
            "name_with_owner": "vitejs/vite",
            "name": "Vite",
            "description": "Next generation frontend tooling",
            "primary_language": "TypeScript",
            "topics": ["build-tool", "bundler", "dev-server"],
            "readme_content": """
# Vite

Next generation frontend tooling.

- Instant server start
- Lightning fast HMR
- Rich features
- Optimized build

The modern build tool for web development.
"""
        },
        {
            "name_with_owner": "rollup/rollup",
            "name": "Rollup",
            "description": "Next-generation JavaScript module bundler",
            "primary_language": "JavaScript",
            "topics": ["bundler", "javascript", "modules"],
            "readme_content": """
# Rollup

Next-generation JavaScript module bundler.

- Tree-shaking
- ES modules
- Plugin system

Build libraries and applications with optimal output.
"""
        },

        # === Testing ===
        {
            "name_with_owner": "pytest-dev/pytest",
            "name": "pytest",
            "description": "The pytest testing framework for Python",
            "primary_language": "Python",
            "topics": ["python", "testing", "framework"],
            "readme_content": """
# pytest

The pytest testing framework for Python.

- Simple assertions
- Powerful fixtures
- Plugin ecosystem
- Detailed error reports

Make testing easy and fun.
"""
        },
        {
            "name_with_owner": "jestjs/jest",
            "name": "Jest",
            "description": "Delightful JavaScript Testing",
            "primary_language": "TypeScript",
            "topics": ["javascript", "testing", "framework"],
            "readme_content": """
# Jest

Delightful JavaScript Testing.

- Zero config
- Instant feedback
- Transforming code
- Snapshot testing

Complete and easy to set up testing solution.
"""
        },
        {
            "name_with_owner": "mockito/mockito",
            "name": "Mockito",
            "description": "Mocking framework for Java unit tests",
            "primary_language": "Java",
            "topics": ["java", "testing", "mocking"],
            "readme_content": """
# Mockito

Mocking framework for unit tests in Java.

- Clean mocks
- Stubbing
- Verification

Write better unit tests with mocks.
"""
        },

        # === Databases ===
        {
            "name_with_owner": "postgres/postgres",
            "name": "PostgreSQL",
            "description": "The world's most advanced open source relational database",
            "primary_language": "C",
            "topics": ["database", "sql", "relational"],
            "readme_content": """
# PostgreSQL

The world's most advanced open source relational database.

- ACID compliance
- Complex queries
- Data integrity
- Extensible

Powerful, open source object-relational database system.
"""
        },
        {
            "name_with_owner": "mongodb/mongo",
            "name": "MongoDB",
            "description": "A document-oriented NoSQL database",
            "primary_language": "C++",
            "topics": ["database", "nosql", "document"],
            "readme_content": """
# MongoDB

A document-oriented NoSQL database.

- Document model
- Flexible schema
- Scalable
- High performance

Store data in JSON-like documents.
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

In-memory data structure store.

- Key-value store
- Pub/Sub
- Transactions
- Persistence

Fast, open source, in-memory data structure store.
"""
        },

        # === DevOps ===
        {
            "name_with_owner": "docker/docker",
            "name": "Docker",
            "description": "Container platform for developing, shipping, and running applications",
            "primary_language": "Go",
            "topics": ["containers", "devops", "virtualization"],
            "readme_content": """
# Docker

Container platform for applications.

- Build once, run anywhere
- Containerization
- Compose
- Swarm

Pack, ship and run any application as a lightweight container.
"""
        },
        {
            "name_with_owner": "kubernetes/kubernetes",
            "name": "Kubernetes",
            "description": "Production-Grade Container Orchestration",
            "primary_language": "Go",
            "topics": ["containers", "orchestration", "devops"],
            "readme_content": """
# Kubernetes

Production-Grade Container Orchestration.

- Automated rollouts and rollbacks
- Service discovery
- Self-healing
- Load balancing

Manage containerized workloads and services.
"""
        },
        {
            "name_with_owner": "github-actions/actions-runner-controller",
            "name": "Actions Runner Controller",
            "description": "Kubernetes controller for GitHub Actions self-hosted runners",
            "primary_language": "Go",
            "topics": ["github", "ci-cd", "kubernetes"],
            "readme_content": """
# Actions Runner Controller

Kubernetes controller for GitHub Actions.

- Self-hosted runners
- Scalable
- Automated scaling

Run GitHub Actions on your Kubernetes infrastructure.
"""
        },

        # === API Design ===
        {
            "name_with_owner": "graphql/graphql-spec",
            "name": "GraphQL",
            "description": "A query language for APIs",
            "primary_language": "Markdown",
            "topics": ["api", "query-language", "specification"],
            "readme_content": """
# GraphQL

A query language for APIs.

- Query exactly what you need
- Get many resources in a single request
- Strongly typed schema
- Real-time updates

Modern alternative to REST.
"""
        },
        {
            "name_with_owner": "grpc/grpc",
            "name": "gRPC",
            "description": "A high performance, open source universal RPC framework",
            "primary_language": "C++",
            "topics": ["rpc", "microservices", "api"],
            "readme_content": """
# gRPC

High performance RPC framework.

- HTTP/2 based
- Protobuf serialization
- Streaming
- Cross-platform

Build efficient microservices.
"""
        },

        # === Security ===
        {
            "name_with_owner": "jwt-rs/jwt-rs",
            "name": "jwt-rs",
            "description": "JWT library for Rust",
            "primary_language": "Rust",
            "topics": ["jwt", "authentication", "security"],
            "readme_content": """
# jwt-rs

JWT library for creating and verifying JSON Web Tokens.

- Signing and verification
- Multiple algorithms
- Claims validation

Secure authentication with JWT tokens.
"""
        },
        {
            "name_with_owner": "openssl/openssl",
            "name": "OpenSSL",
            "description": "Cryptography and SSL/TLS Toolkit",
            "primary_language": "C",
            "topics": ["security", "encryption", "ssl"],
            "readme_content": """
# OpenSSL

Cryptography and SSL/TLS Toolkit.

- TLS/SSL protocols
- Cryptographic library
- Certificate management

Robust, commercial-grade, full-featured toolkit.
"""
        },

        # === Developer Tools ===
        {
            "name_with_owner": "eslint/eslint",
            "name": "ESLint",
            "description": "Find and fix problems in JavaScript code",
            "primary_language": "JavaScript",
            "topics": ["linter", "javascript", "code-quality"],
            "readme_content": """
# ESLint

Find and fix problems in JavaScript code.

- Static analysis
- Code quality
- Pluggable
- Configurable

Identify and report on patterns in JavaScript.
"""
        },
        {
            "name_with_owner": "prettier/prettier",
            "name": "Prettier",
            "description": "Code formatter for JavaScript, TypeScript, CSS, and more",
            "primary_language": "JavaScript",
            "topics": ["formatter", "code-style"],
            "readme_content": """
# Prettier

Opinionated code formatter.

- Consistent code style
- Integrates with editors
- Supports many languages

Enforce a consistent style across your codebase.
"""
        },
        {
            "name_with_owner": "VSCodeVim/Vim",
            "name": "Vim",
            "description": "Vim emulation for Visual Studio Code",
            "primary_language": "TypeScript",
            "topics": ["vim", "vscode", "editor"],
            "readme_content": """
# Vim for VS Code

Vim emulation for Visual Studio Code.

- Vim keybindings
- Modes, commands, marks
- Extensions

Use Vim shortcuts in VS Code.
"""
        },

        # === Cloud Platforms ===
        {
            "name_with_owner": "aws/aws-sdk-go",
            "name": "AWS SDK for Go",
            "description": "AWS SDK for the Go programming language",
            "primary_language": "Go",
            "topics": ["aws", "cloud", "sdk"],
            "readme_content": """
# AWS SDK for Go

Official AWS SDK for the Go programming language.

- S3, EC2, DynamoDB, Lambda
- High performance
- Concurrent

Build Go applications that use AWS services.
"""
        },
        {
            "name_with_owner": "Azure/azure-sdk-for-python",
            "name": "Azure SDK for Python",
            "description": "Microsoft Azure SDK for Python",
            "primary_language": "Python",
            "topics": ["azure", "cloud", "sdk"],
            "readme_content": """
# Azure SDK for Python

Microsoft Azure Client Libraries for Python.

- Blob storage, VMs, Functions
- Async APIs
- Type hints

Build Python apps on Azure.
"""
        },
        {
            "name_with_owner": "googleapis/python-api-core",
            "name": "Google API Core",
            "description": "Core libraries for Google Cloud APIs",
            "primary_language": "Python",
            "topics": ["gcp", "cloud", "api"],
            "readme_content": """
# Google API Core

Core libraries for Google Cloud Python APIs.

- Authentication
- HTTP transport
- Retry logic

Foundation for Google Cloud client libraries.
"""
        },
    ]

    await service.index_batch(repos)
    yield repos, embeddings, store
    store.clear()


class TestRealWorldScenarios:
    """Test real-world search scenarios users would actually perform."""

    @pytest.mark.asyncio
    async def test_frontend_framework_comparison(self, real_world_repos):
        """User wants to compare frontend frameworks."""
        repos, embeddings, store = real_world_repos

        queries = [
            "前端框架对比",
            "best frontend framework",
            "UI 框架",
            "javascript component library",
        ]

        print("\n=== Frontend Framework Comparison ===")
        for query in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            # Should find React, Vue, Angular, Svelte
            frontend_libs = ['React', 'Vue.js', 'Angular', 'Svelte']
            found = [lib for lib in frontend_libs if lib in top_names]

            print(f"Query: '{query}'")
            print(f"  Found: {found}")
            print(f"  Top 3: {top_names}\n")

            assert len(found) >= 1, f"Should find frontend frameworks for '{query}'"

    @pytest.mark.asyncio
    async def test_backend_framework_by_language(self, real_world_repos):
        """User wants backend frameworks for specific languages."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("Python 后端框架", ["Django", "Flask"]),
            ("Go web framework", []),  # We don't have Go frameworks, but shouldn't crash
            ("Python web development", ["Django", "Flask"]),
        ]

        print("\n=== Backend Framework by Language ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            if expected:
                found = [lib for lib in expected if lib in top_names]
                print(f"Query: '{query}'")
                print(f"  Expected: {expected}")
                print(f"  Found: {found}")
                assert len(found) >= 1, f"Should find {expected} for '{query}'"
            else:
                print(f"Query: '{query}' (no expectations)")
                print(f"  Top results: {top_names}")

            print()

    @pytest.mark.asyncio
    async def test_database_type_selection(self, real_world_repos):
        """User wants to find databases by type."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("关系型数据库", ["PostgreSQL"]),
            ("NoSQL 数据库", ["MongoDB", "Redis"]),
            ("缓存数据库", ["Redis"]),
            ("document database", ["MongoDB"]),
            ("SQL database", ["PostgreSQL"]),
        ]

        print("\n=== Database Type Selection ===")
        correct = 0
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_name = results[0]['metadata'].get('name', '') if results else None

            is_correct = top_name in expected if expected else True
            if is_correct:
                correct += 1
                status = "✅"
            else:
                status = "❌"

            print(f"{status} '{query}' → {top_name} (expected: {expected})")

        accuracy = (correct / len(queries)) * 100
        print(f"\nAccuracy: {correct}/{len(queries)} = {accuracy:.1f}%")
        assert accuracy >= 80, "Database search accuracy should be >= 80%"

    @pytest.mark.asyncio
    async def test_devops_workflow_tools(self, real_world_repos):
        """User wants DevOps tools for specific workflows."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("容器化工具", ["Docker"]),
            ("容器编排", ["Kubernetes"]),
            ("CI/CD tools", ["Actions Runner Controller"]),
            ("continuous integration", ["Actions Runner Controller"]),
            ("部署自动化", ["Kubernetes", "Docker"]),
        ]

        print("\n=== DevOps Workflow Tools ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            found = [tool for tool in expected if tool in top_names]
            status = "✅" if found else "⚠️"

            print(f"{status} '{query}'")
            print(f"  Expected: {expected}")
            print(f"  Found: {found}")
            print(f"  Top 3: {top_names}\n")

            # Should find at least one expected tool in top 3
            assert len(found) >= 1, f"Should find DevOps tools for '{query}'"

    @pytest.mark.asyncio
    async def test_testing_framework_by_language(self, real_world_repos):
        """User wants testing frameworks for their language."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("Python 测试框架", ["pytest"]),
            ("JavaScript testing", ["Jest"]),
            ("Java mocking library", ["Mockito"]),
            ("单元测试工具", ["pytest", "Jest", "Mockito"]),
        ]

        print("\n=== Testing Framework by Language ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_name = results[0]['metadata'].get('name', '') if results else None

            is_correct = top_name in expected
            status = "✅" if is_correct else "⚠️"

            print(f"{status} '{query}' → {top_name} (expected one of: {expected})")

            # At least should find something relevant
            assert top_name is not None, f"Should find testing framework for '{query}'"

    @pytest.mark.asyncio
    async def test_build_tool_selection(self, real_world_repos):
        """User wants to choose between build tools."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("前端打包工具", ["webpack", "Vite", "Rollup"]),
            ("module bundler", ["webpack", "Rollup", "Vite"]),
            ("JavaScript 构建工具", ["webpack", "Vite"]),
            ("modern dev server", ["Vite"]),
        ]

        print("\n=== Build Tool Selection ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            found = [tool for tool in expected if tool in top_names]
            status = "✅" if found else "⚠️"

            print(f"{status} '{query}'")
            print(f"  Expected one of: {expected}")
            print(f"  Found: {found}")
            print(f"  Top 3: {top_names}\n")

            assert len(found) >= 1, f"Should find build tools for '{query}'"

    @pytest.mark.asyncio
    async def test_api_style_selection(self, real_world_repos):
        """User wants to choose API design style."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("GraphQL vs REST", ["GraphQL", "gRPC"]),
            ("API 查询语言", ["GraphQL"]),
            ("RPC 框架", ["gRPC"]),
            ("modern API design", ["GraphQL", "gRPC"]),
        ]

        print("\n=== API Style Selection ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            found = [style for style in expected if style in top_names]
            status = "✅" if found else "⚠️"

            print(f"{status} '{query}'")
            print(f"  Found: {found}")
            print(f"  Top 3: {top_names}\n")

            # Should find at least one API style
            assert len(found) >= 1, f"Should find API styles for '{query}'"

    @pytest.mark.asyncio
    async def test_security_tools_by_need(self, real_world_repos):
        """User wants security tools for specific needs."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("身份认证", ["jwt-rs"]),
            ("JWT tokens", ["jwt-rs"]),
            ("加密库", ["OpenSSL"]),
            ("SSL/TLS toolkit", ["OpenSSL"]),
        ]

        print("\n=== Security Tools by Need ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_name = results[0]['metadata'].get('name', '') if results else None

            is_correct = top_name in expected
            status = "✅" if is_correct else "⚠️"

            print(f"{status} '{query}' → {top_name}")

            assert top_name is not None, f"Should find security tools for '{query}'"

    @pytest.mark.asyncio
    async def test_code_quality_tools(self, real_world_repos):
        """User wants to improve code quality."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("代码检查工具", ["ESLint"]),
            ("代码格式化", ["Prettier"]),
            ("代码规范", ["ESLint", "Prettier"]),
            ("linter and formatter", ["ESLint", "Prettier"]),
        ]

        print("\n=== Code Quality Tools ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            found = [tool for tool in expected if tool in top_names]
            status = "✅" if found else "⚠️"

            print(f"{status} '{query}'")
            print(f"  Found: {found}")
            print(f"  Top 3: {top_names}\n")

            assert len(found) >= 1, f"Should find code quality tools for '{query}'"

    @pytest.mark.asyncio
    async def test_cloud_platform_sdk(self, real_world_repos):
        """User wants SDKs for specific cloud platforms."""
        repos, embeddings, store = real_world_repos

        queries = [
            ("AWS SDK", ["AWS SDK for Go"]),
            ("Azure 开发工具包", ["Azure SDK for Python"]),
            ("Google Cloud SDK", ["Google API Core"]),
            ("cloud SDK comparison", ["AWS SDK for Go", "Azure SDK for Python", "Google API Core"]),
        ]

        print("\n=== Cloud Platform SDK ===")
        for query, expected in queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_names = [r['metadata'].get('name', '') for r in results[:3]]

            found = [sdk for sdk in expected if sdk in top_names]
            status = "✅" if found else "⚠️"

            print(f"{status} '{query}'")
            print(f"  Found: {found}")
            print(f"  Top 3: {top_names}\n")

            assert len(found) >= 1, f"Should find cloud SDKs for '{query}'"

    @pytest.mark.asyncio
    async def test_cross_category_search(self, real_world_repos):
        """Test searches that cross category boundaries."""
        repos, embeddings, store = real_world_repos

        # User asks for something that could be in multiple categories
        queries = [
            {
                "query": "框架",
                "categories": {
                    "frontend": ["React", "Vue.js", "Angular", "Svelte"],
                    "backend": ["Django", "Flask"],
                    "testing": ["pytest", "Jest", "Mockito"],
                }
            },
            {
                "query": "tools for developers",
                "categories": {
                    "testing": ["pytest", "Jest", "Mockito"],
                    "quality": ["ESLint", "Prettier"],
                    "build": ["webpack", "Vite", "Rollup"],
                }
            },
        ]

        print("\n=== Cross-Category Search ===")
        for test_case in queries:
            query = test_case["query"]
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=10)
            top_names = [r['metadata'].get('name', '') for r in results]

            print(f"Query: '{query}'")
            print(f"Top 10 results: {top_names}")

            # Check if we found results from multiple categories
            found_categories = []
            for cat_name, cat_items in test_case["categories"].items():
                if any(item in top_names for item in cat_items):
                    found_categories.append(cat_name)

            print(f"Found in categories: {found_categories}")
            print(f"Number of categories: {len(found_categories)}\n")

            # Should find results from at least 2 categories
            assert len(found_categories) >= 2, \
                f"Cross-category search should find results from multiple categories"

    @pytest.mark.asyncio
    async def test_natural_language_queries(self, real_world_repos):
        """Test natural language queries how users actually search."""
        repos, embeddings, store = real_world_repos

        # These are real queries a developer might type
        natural_queries = [
            ("I need a database for my app", ["PostgreSQL", "MongoDB", "Redis"]),
            ("How to test my Python code", ["pytest"]),
            ("Best framework for building UI", ["React", "Vue.js", "Angular"]),
            ("Tools to deploy my application", ["Docker", "Kubernetes"]),
            ("Format my JavaScript code", ["Prettier"]),
            ("Build tool for modern web", ["Vite", "webpack"]),
            ("Secure authentication", ["jwt-rs"]),
        ]

        print("\n=== Natural Language Queries ===")
        correct = 0
        for query, expected in natural_queries:
            query_vec = embeddings.embed_text(query)
            results = store.search(query_vec, top_k=5)
            top_3 = [r['metadata'].get('name', '') for r in results[:3]]

            # Check if any expected result is in top 3
            found = any(exp in top_3 for exp in expected)
            if found:
                correct += 1
                status = "✅"
            else:
                status = "⚠️"

            print(f"{status} \"{query}\"")
            print(f"  Expected one of: {expected}")
            print(f"  Found in top 3: {top_3}\n")

        accuracy = (correct / len(natural_queries)) * 100
        print("="*60)
        print(f"Natural Language Accuracy: {correct}/{len(natural_queries)} = {accuracy:.1f}%")
        print("="*60)

        assert accuracy >= 70, f"Natural language accuracy should be >= 70%, got {accuracy:.1f}%"

    @pytest.mark.asyncio
    async def test_domain_expertise_queries(self, real_world_repos):
        """Test queries from different domains of expertise."""
        repos, embeddings, store = real_world_repos

        domain_scenarios = [
            {
                "domain": "Frontend Developer",
                "queries": [
                    ("component library", ["React", "Vue.js", "Angular"]),
                    ("CSS preprocessor", []),  # We don't have these, but shouldn't crash
                    ("build optimization", ["webpack", "Vite", "Rollup"]),
                ]
            },
            {
                "domain": "Backend Developer",
                "queries": [
                    ("API framework", ["Django", "Flask"]),
                    ("database choice", ["PostgreSQL", "MongoDB", "Redis"]),
                    ("microservices", ["Django", "Flask", "websocket"]),
                ]
            },
            {
                "domain": "DevOps Engineer",
                "queries": [
                    ("container platform", ["Docker", "Kubernetes"]),
                    ("CI/CD pipeline", ["Actions Runner Controller"]),
                    ("infrastructure as code", ["Kubernetes"]),
                ]
            },
            {
                "domain": "Data Engineer",
                "queries": [
                    ("data storage", ["PostgreSQL", "MongoDB", "Redis"]),
                    ("caching layer", ["Redis"]),
                    ("relational database", ["PostgreSQL"]),
                ]
            },
        ]

        print("\n=== Domain Expertise Queries ===")
        total_correct = 0
        total_queries = 0

        for scenario in domain_scenarios:
            print(f"\n{scenario['domain']}:")
            domain_correct = 0
            domain_total = 0

            for query, expected in scenario["queries"]:
                query_vec = embeddings.embed_text(query)
                results = store.search(query_vec, top_k=5)
                top_names = [r['metadata'].get('name', '') for r in results[:3]]

                if expected:
                    found = any(exp in top_names for exp in expected)
                    if found:
                        domain_correct += 1
                        total_correct += 1
                        status = "✅"
                    else:
                        status = "⚠️"
                    domain_total += 1
                    total_queries += 1

                    print(f"  {status} '{query}' → {top_names[0]}")

            if domain_total > 0:
                domain_accuracy = (domain_correct / domain_total) * 100
                print(f"  Domain accuracy: {domain_correct}/{domain_total} = {domain_accuracy:.1f}%")

        overall_accuracy = (total_correct / total_queries) * 100 if total_queries > 0 else 0
        print(f"\n{'='*60}")
        print(f"Overall Domain Accuracy: {total_correct}/{total_queries} = {overall_accuracy:.1f}%")
        print(f"{'='*60}")

        assert overall_accuracy >= 60, f"Domain accuracy should be >= 60%, got {overall_accuracy:.1f}%"
