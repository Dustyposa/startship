# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Setup
```bash
# Python backend (uses uv)
# Note: Project is configured to use Tsinghua mirror for faster downloads in China
uv pip install -e .
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8889

# Frontend (Vue 3 + TypeScript)
cd frontend
npm install
npm run dev -- --port 3001

# Testing
pytest tests/unit/  # Unit tests only
pytest tests/integration/  # Integration tests only
pytest --cov=src tests/  # With coverage
```

### Docker Development
```bash
# One-click deployment (recommended)
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop services
docker compose down

# Rebuild and redeploy
docker compose up -d --build
```

### Code Quality
```bash
# Python formatting (requires uv)
black src/
ruff check src/ --fix

# TypeScript formatting (in frontend directory)
cd frontend
npm run lint
npm run format

# Frontend testing
cd frontend
npm run test       # Run tests
```

## High-Level Architecture

### Core Components

1. **FastAPI Backend** (`src/`)
   - API Layer: FastAPI application with automatic OpenAPI docs at `/docs`
   - Database Layer: SQLite + FTS5 for full-text search, async with aiosqlite
   - Services Layer: Business logic separated by domain (chat, search, sync, etc.)
   - Vector Store: ChromaDB for semantic search (optional, requires Ollama)

2. **Vue 3 Frontend** (`frontend/`)
   - Composition API with TypeScript
   - State management: Pinia stores
   - Charts: ECharts for network visualization and trend analysis
   - Styling: Tailwind CSS with custom components

3. **Data Synchronization**
   - GitHub API client with GraphQL support
   - Incremental sync (daily at 2 AM) + Full validation (weekly at 3 AM)
   - Soft delete protection for user data (notes, tags, collections)

### Key Patterns

1. **Repository Pattern** (`src/db/base.py`)
   - Abstract database interface with SQLite implementation
   - Automatic migration system via `src/db/migrations/`
   - FTS5 triggers for real-time full-text search indexing

2. **Service Layer Architecture**
   - Each service has a single responsibility (chat, search, sync, etc.)
   - Dependency injection through constructor parameters
   - Async/await throughout with proper error handling

3. **Intent Recognition System**
   - Chat requests are routed through intent detection in `src/services/intent.py`
   - Supports three intent types: `chat` (conversational), `stats` (statistics/analysis), `search` (repository search)
   - Intent classifier uses LLM with Chinese-language system prompt
   - Automatically extracts search keywords for search-based queries

4. **Dual Search Architecture**
   - **Full-text search**: SQLite FTS5 on name, description, summary
   - **Semantic search**: ChromaDB with Ollama embeddings (when enabled)
   - Hybrid search with configurable weights in `src/services/hybrid_search.py`
   - Query expansion via `src/services/query_expander.py` enhances search recall

## Important Conventions

### Code Structure
- **API routes**: `src/api/routes/` - FastAPI route definitions
- **Business logic**: `src/services/` - Service layer implementations
- **Database models**: `src/data/` and `src/db/` - Database abstractions
- **LLM abstraction**: `src/llm/` - Provider-agnostic LLM interface (OpenAI, Ollama)

### Database Conventions
- All JSON fields stored as strings with `ensure_ascii=False`
- Soft delete pattern with `is_deleted` flag
- Migration system uses timestamped SQL files in `src/db/migrations/`
- FTS5 virtual table automatically synchronized with main data

### Frontend Patterns
- Vue 3 Composition API with `<script setup>` syntax
- TypeScript types in `frontend/src/types/`
- Composables in `frontend/src/composables/` for reusable logic
- Pinia stores follow domain-based organization

### Configuration
- Environment variables managed via `src/config.py` (Pydantic Settings)
- `.env` file support with sensible defaults
- Optional features (ChromaDB, semantic search) require specific config

## Non-Obvious Aspects

### 1. Automatic Context Management
The chat system maintains conversation context automatically through:
- `src/services/context.py` builds context from conversation history
- Session-based storage with automatic cleanup
- Context window limited to last 10 messages by default

### 2. GitHub API Rate Limiting
- Uses GitHub token for increased rate limits (5,000 requests/hour vs. 60/hour)
- Implements automatic retry with exponential backoff
- Caches README content to avoid repeated API calls

### 3. Hybrid Search Weights
Search results combine FTS5 and semantic search with configurable weights:
- `fts_weight`: 0.3 (default) - Full-text search importance
- `semantic_weight`: 0.7 (default) - Semantic search importance
- Weights can be adjusted in `src/services/hybrid_search.py` constructor
- Parallel execution of both search types for optimal performance

### 4. Data Migration System
- Automatic migration execution on startup
- Migration tracking in `_migrations` table
- Rollback support on failed migrations
- SQL files must be timestamped (e.g., `001_initial_schema.sql`)

### 5. Streaming Response Protocol
Chat endpoints use Server-Sent Events (SSE) with event types:
- `intent`: Detected user intent (chat/stats/search)
- `content`: Response content chunks
- `search_results`: Relevant repositories for context
- `done`: Signal completion

### 6. Knowledge Graph System
- Edge discovery service in `src/services/graph/edges.py` finds relationships between repositories
- Three edge types: `author` (same owner), `ecosystem` (same language), `collection` (same collection)
- Relationship weights computed based on connection strength
- Related repository recommendations based on graph traversal
- Manual rebuild via `/api/graph/rebuild`, incremental updates on sync/user actions

### 7. Soft Delete Protection
When repositories are un-starred:
- Main repository record marked as `is_deleted = 1`
- User data (notes, tags, collections) preserved
- Restore functionality available through API endpoints
- Prevents accidental data loss during sync operations

### 8. Development Server URLs
- Backend: http://localhost:8889 (not 8000 as configured)
- Frontend: http://localhost:3001 (not 3000 as default)
- API docs: http://localhost:8889/docs

## Environment Setup

### Required Variables
```bash
# GitHub API (required for sync)
GITHUB_TOKEN=ghp_xxx

# OpenAI (required for chat)
OPENAI_API_KEY=sk_xxx

# Optional: Ollama for semantic search
OLLAMA_BASE_URL=http://localhost:11434

# Database path (auto-created if not exists)
SQLITE_PATH=data/github_stars.db
```

### Development Workflow
1. Start backend with `uvicorn` on port 8889
2. Start frontend on port 3001
3. Initialize data via `/api/init/start` endpoint
4. Use browser dev tools for API debugging
5. Check `/health` and `/api/stats` for service status

### Language and Localization
- **Chinese Language System**: The application's UI and LLM prompts use Chinese as the primary language
- Intent classifier uses Chinese-language system prompts for better accuracy with Chinese queries
- UI text, error messages, and documentation are in Chinese
- When modifying LLM prompts or adding new features, maintain consistency with Chinese language patterns
