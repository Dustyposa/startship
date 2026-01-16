# Graph Knowledge System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个交互式知识图谱系统，让用户能够发现 GitHub 星标项目之间的关联，实现智能召回和知识沉淀。

**Architecture:** 分两层实现 - 第一层基于元数据的关联（作者、依赖、技术栈、收藏夹），第二层基于语义的关联（embedding 相似度）。采用手动/增量更新策略，避免定时任务。

**Tech Stack:**
- 后端: FastAPI, SQLite, aiosqlite
- 前端: Vue 3, ECharts (复用现有网络可视化组件)
- 向量: ChromaDB (Phase 2)
- Embedding: Ollama nomic-embed-text (Phase 2)

---

## Phase 1: 元数据关联图谱

### Task 1: 创建数据库迁移 - 关联表

**Files:**
- Create: `src/db/migrations/004_add_graph_edges_table.sql`

**Step 1: 编写迁移 SQL**

```sql
-- Migration 004: Add graph edges table for knowledge graph
CREATE TABLE IF NOT EXISTS graph_edges (
    source_repo TEXT NOT NULL,
    target_repo TEXT NOT NULL,
    edge_type TEXT NOT NULL,  -- author|dependency|ecosystem|collection
    weight REAL DEFAULT 1.0,
    metadata TEXT,  -- JSON: 额外信息
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (source_repo, target_repo, edge_type),
    FOREIGN KEY (source_repo) REFERENCES repositories(name_with_owner) ON DELETE CASCADE,
    FOREIGN KEY (target_repo) REFERENCES repositories(name_with_owner) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_repo, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_repo, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type, weight DESC);

-- Graph status tracking
CREATE TABLE IF NOT EXISTS graph_status (
    repo_id TEXT PRIMARY KEY,
    edges_computed_at TEXT,
    dependencies_parsed_at TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(name_with_owner)
);

-- Update timestamp trigger
CREATE TRIGGER IF NOT EXISTS update_edges_timestamp
AFTER UPDATE ON graph_edges
FOR EACH ROW
BEGIN
    UPDATE graph_edges SET updated_at = datetime('now')
    WHERE source_repo = NEW.source_repo AND target_repo = NEW.target_repo AND edge_type = NEW.edge_type;
END;
```

**Step 2: 运行迁移验证**

Run: `python -c "from src.db.sqlite import SQLiteDB; import asyncio; asyncio.run(SQLiteDB().run_migrations())"`
Expected: No errors, migration 004 applied

**Step 3: 验证表创建**

Run: `sqlite3 data/github_stars.db ".schema graph_edges"`
Expected: Shows the table schema

**Step 4: Commit**

```bash
git add src/db/migrations/004_add_graph_edges_table.sql
git commit -m "db: add graph_edges table for knowledge graph"
```

---

### Task 2: 数据库层 - 关联操作接口

**Files:**
- Modify: `src/db/sqlite.py`

**Step 1: 在 SQLiteDB 类中添加关联操作方法**

```python
async def add_graph_edge(
    self,
    source_repo: str,
    target_repo: str,
    edge_type: str,
    weight: float = 1.0,
    metadata: Optional[str] = None
) -> None:
    """Add or update a graph edge."""
    await self.execute(
        """INSERT OR REPLACE INTO graph_edges
           (source_repo, target_repo, edge_type, weight, metadata)
           VALUES (?, ?, ?, ?, ?)""",
        (source_repo, target_repo, edge_type, weight, metadata)
    )

async def get_graph_edges(
    self,
    repo: str,
    edge_types: Optional[List[str]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get all edges for a repository."""
    if edge_types:
        placeholders = ','.join('?' * len(edge_types))
        query = f"""
            SELECT source_repo, target_repo, edge_type, weight, metadata
            FROM graph_edges
            WHERE source_repo = ? AND edge_type IN ({placeholders})
            ORDER BY weight DESC
            LIMIT ?
        """
        params = [repo] + edge_types + [limit]
    else:
        query = """
            SELECT source_repo, target_repo, edge_type, weight, metadata
            FROM graph_edges
            WHERE source_repo = ?
            ORDER BY weight DESC
            LIMIT ?
        """
        params = [repo, limit]

    return await self.fetch_all(query, params)

async def delete_repo_edges(self, repo: str) -> None:
    """Delete all edges for a repository (when unstarred)."""
    await self.execute(
        "DELETE FROM graph_edges WHERE source_repo = ? OR target_repo = ?",
        (repo, repo)
    )

async def update_graph_status(
    self,
    repo: str,
    edges_computed: bool = False,
    dependencies_parsed: bool = False
) -> None:
    """Update graph computation status for a repo."""
    updates = []
    params = []

    if edges_computed:
        updates.append("edges_computed_at = ?")
        params.append(datetime.now().isoformat())

    if dependencies_parsed:
        updates.append("dependencies_parsed_at = ?")
        params.append(datetime.now().isoformat())

    if not updates:
        return

    params.append(repo)
    await self.execute(
        f"""INSERT OR REPLACE INTO graph_status (repo_id, {', '.join(updates)})
           VALUES (?, {', '.join(['?'] * len(updates))})""",
        params
    )
```

**Step 2: 添加导入**

```python
from datetime import datetime
from typing import List, Dict, Any, Optional
```

**Step 3: 运行测试验证**

Run: `pytest tests/unit/test_graph_db.py -v`
Expected: Tests pass (or create tests first)

**Step 4: Commit**

```bash
git add src/db/sqlite.py
git commit -m "db: add graph edge operations to SQLiteDB"
```

---

### Task 3: 关联发现服务 - 作者关联

**Files:**
- Create: `src/services/graph/__init__.py`
- Create: `src/services/graph/edges.py`

**Step 1: 创建关联发现模块**

```python
# src/services/graph/__init__.py
from .edges import EdgeDiscoveryService

__all__ = ['EdgeDiscoveryService']
```

**Step 2: 实现关联发现服务**

```python
# src/services/graph/edges.py
from typing import List, Dict, Any, Optional
from loguru import logger
from ..base import Service

class EdgeDiscoveryService(Service):
    """Service for discovering relationships between repositories."""

    async def discover_author_edges(self, repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Discover edges based on common author/organization.

        Returns list of edges with format:
        {
            "source": "owner/repo1",
            "target": "owner/repo2",
            "type": "author",
            "weight": 1.0,
            "metadata": {"author": "owner"}
        }
        """
        # Group by owner
        owner_repos: Dict[str, List[str]] = {}
        for repo in repos:
            owner = repo.get('owner', '')
            if owner:
                if owner not in owner_repos:
                    owner_repos[owner] = []
                owner_repos[owner].append(repo['name_with_owner'])

        # Create edges between repos of same owner
        edges = []
        for owner, repo_list in owner_repos.items():
            if len(repo_list) > 1:
                for i, repo1 in enumerate(repo_list):
                    for repo2 in repo_list[i+1:]:
                        edges.append({
                            "source": repo1,
                            "target": repo2,
                            "type": "author",
                            "weight": 1.0,
                            "metadata": f'{{"author": "{owner}"}}'
                        })

        logger.info(f"Discovered {len(edges)} author edges")
        return edges
```

**Step 3: 创建测试文件**

```python
# tests/unit/test_graph_edges.py
import pytest
from src.services.graph.edges import EdgeDiscoveryService

@pytest.mark.asyncio
async def test_discover_author_edges():
    service = EdgeDiscoveryService()

    repos = [
        {"name_with_owner": "tiangolo/fastapi", "owner": "tiangolo"},
        {"name_with_owner": "tiangolo/typer", "owner": "tiangolo"},
        {"name_with_owner": "python/cpython", "owner": "python"}
    ]

    edges = await service.discover_author_edges(repos)

    assert len(edges) == 1
    assert edges[0]["source"] == "tiangolo/fastapi"
    assert edges[0]["target"] == "tiangolo/typer"
    assert edges[0]["type"] == "author"
```

**Step 4: 运行测试**

Run: `pytest tests/unit/test_graph_edges.py::test_discover_author_edges -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/graph/ tests/unit/test_graph_edges.py
git commit -m "feat: add author edge discovery service"
```

---

### Task 4: 关联发现服务 - 技术栈关联

**Files:**
- Modify: `src/services/graph/edges.py`

**Step 1: 添加技术栈关联发现方法**

```python
async def discover_ecosystem_edges(
    self,
    repos: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Discover edges based on common primary language or topics.

    Uses Jaccard similarity for topics.
    """
    edges = []

    # Group by primary language
    lang_repos: Dict[str, List[str]] = {}
    for repo in repos:
        lang = repo.get('primary_language')
        if lang:
            if lang not in lang_repos:
                lang_repos[lang] = []
            lang_repos[lang].append(repo['name_with_owner'])

    # Create edges for repos with same language (limit to avoid too many)
    for lang, repo_list in lang_repos.items():
        # Only if there are multiple repos with this language
        if len(repo_list) > 1 and len(repo_list) < 50:  # Avoid popular languages
            for i, repo1 in enumerate(repo_list[:20]):  # Limit per language
                for repo2 in repo_list[i+1:20]:
                    edges.append({
                        "source": repo1,
                        "target": repo2,
                        "type": "ecosystem",
                        "weight": 0.6,
                        "metadata": f'{{"language": "{lang}"}}'
                    })

    # Group by topics (Jaccard similarity)
    for i, repo1 in enumerate(repos):
        topics1 = set(repo1.get('topics', []))
        if not topics1:
            continue

        for repo2 in repos[i+1:]:
            topics2 = set(repo2.get('topics', []))
            if not topics2:
                continue

            # Calculate Jaccard similarity
            intersection = len(topics1 & topics2)
            union = len(topics1 | topics2)

            if intersection >= 2:  # At least 2 common topics
                jaccard = intersection / union if union > 0 else 0
                if jaccard > 0.3:  # Threshold for similarity
                    edges.append({
                        "source": repo1['name_with_owner'],
                        "target": repo2['name_with_owner'],
                        "type": "ecosystem",
                        "weight": round(jaccard, 2),
                        "metadata": f'{{"common_topics": {intersection}}}'
                    })

    logger.info(f"Discovered {len(edges)} ecosystem edges")
    return edges
```

**Step 2: 添加测试**

```python
@pytest.mark.asyncio
async def test_discover_ecosystem_edges_language():
    service = EdgeDiscoveryService()

    repos = [
        {"name_with_owner": "owner/fastapi", "primary_language": "Python", "topics": []},
        {"name_with_owner": "owner/flask", "primary_language": "Python", "topics": []},
        {"name_with_owner": "owner/express", "primary_language": "JavaScript", "topics": []}
    ]

    edges = await service.discover_ecosystem_edges(repos)

    # Should find edge between two Python repos
    python_edges = [e for e in edges if e['source'] == 'owner/fastapi']
    assert len(python_edges) > 0
```

**Step 3: 运行测试**

Run: `pytest tests/unit/test_graph_edges.py::test_discover_ecosystem_edges_language -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/services/graph/edges.py tests/unit/test_graph_edges.py
git commit -m "feat: add ecosystem edge discovery"
```

---

### Task 5: 关联发现服务 - 收藏夹关联

**Files:**
- Modify: `src/services/graph/edges.py`

**Step 1: 添加收藏夹关联发现方法**

```python
async def discover_collection_edges(
    self,
    db: Any
) -> List[Dict[str, Any]]:
    """
    Discover edges based on repos in the same collection.
    """
    query = """
        SELECT c1.repo_id as source_repo, c2.repo_id as target_repo, col.name as collection_name
        FROM repo_collections c1
        JOIN repo_collections c2 ON c1.collection_id = c2.collection_id
        JOIN collections col ON col.id = c1.collection_id
        WHERE c1.repo_id < c2.repo_id
    """

    rows = await db.fetch_all(query)

    edges = []
    for row in rows:
        edges.append({
            "source": row['source_repo'],
            "target": row['target_repo'],
            "type": "collection",
            "weight": 0.5,
            "metadata": f'{{"collection": "{row["collection_name"]}"}}'
        })

    logger.info(f"Discovered {len(edges)} collection edges")
    return edges
```

**Step 2: 添加测试**

```python
@pytest.mark.asyncio
async def test_discover_collection_edges(db):
    service = EdgeDiscoveryService()

    # Setup test data
    await db.execute("""
        INSERT INTO collections (id, name) VALUES ('col1', 'Web Frameworks')
    """)
    await db.execute("""
        INSERT INTO repo_collections (repo_id, collection_id) VALUES
        ('owner/fastapi', 'col1'), ('owner/flask', 'col1')
    """)

    edges = await service.discover_collection_edges(db)

    assert len(edges) >= 1
    assert any(e['type'] == 'collection' for e in edges)
```

**Step 3: 运行测试**

Run: `pytest tests/unit/test_graph_edges.py::test_discover_collection_edges -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/services/graph/edges.py tests/unit/test_graph_edges.py
git commit -m "feat: add collection edge discovery"
```

---

### Task 6: 图谱 API - 获取关联

**Files:**
- Create: `src/api/routes/graph.py`
- Modify: `src/api/app.py`

**Step 1: 创建图谱 API 路由**

```python
# src/api/routes/graph.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..utils import get_db
from ...services.graph.edges import EdgeDiscoveryService

router = APIRouter(prefix="/api/graph", tags=["graph"])

class EdgeResponse(BaseModel):
    source: str
    target: str
    type: str
    weight: float
    metadata: Optional[str] = None

@router.get("/nodes/{repo}/edges", response_model=List[EdgeResponse])
async def get_repo_edges(
    repo: str,
    edge_types: Optional[str] = None,  # Comma-separated: author,ecosystem,collection
    limit: int = 50,
    db = Depends(get_db)
):
    """Get all edges for a repository, sorted by weight."""
    types = edge_types.split(',') if edge_types else None

    edges = await db.get_graph_edges(repo, edge_types=types, limit=limit)

    if not edges:
        # Try to compute edges on-demand
        service = EdgeDiscoveryService()
        repos = await db.search_repositories(limit=1000)
        # This would trigger edge computation...

    return [
        EdgeResponse(
            source=e['source_repo'],
            target=e['target_repo'],
            type=e['edge_type'],
            weight=e['weight'],
            metadata=e.get('metadata')
        )
        for e in edges
    ]

@router.post("/rebuild")
async def rebuild_graph(db = Depends(get_db)):
    """Manually trigger full graph rebuild."""
    service = EdgeDiscoveryService()

    # Get all repos
    repos = await db.search_repositories(limit=1000)

    # Discover all edge types
    all_edges = []
    all_edges.extend(await service.discover_author_edges(repos))
    all_edges.extend(await service.discover_ecosystem_edges(repos))
    all_edges.extend(await service.discover_collection_edges(db))

    # Clear existing edges
    await db.execute("DELETE FROM graph_edges")

    # Insert new edges
    for edge in all_edges:
        await db.add_graph_edge(
            edge['source'],
            edge['target'],
            edge['type'],
            edge['weight'],
            edge.get('metadata')
        )

    return {"status": "success", "edges_count": len(all_edges)}

@router.get("/status")
async def get_graph_status(db = Depends(get_db)):
    """Get graph computation status."""
    status = await db.fetch_all(
        "SELECT repo_id, edges_computed_at, dependencies_parsed_at FROM graph_status LIMIT 10"
    )
    return {"data": status}
```

**Step 2: 注册路由到主应用**

在 `src/api/app.py` 中添加：

```python
from .routes import graph

app.include_router(graph.router)
```

**Step 3: 测试 API**

Run: `curl http://localhost:8889/api/graph/nodes/tiangolo/fastapi/edges`
Expected: Returns JSON with edges array

**Step 4: Commit**

```bash
git add src/api/routes/graph.py src/api/app.py
git commit -m "feat: add graph API endpoints"
```

---

### Task 7: 前端 - 图谱视图增强

**Files:**
- Modify: `frontend/src/views/NetworkView.vue`
- Modify: `frontend/src/router/index.ts`

**Step 1: 添加图谱 API 调用**

```typescript
// frontend/src/api/graph.ts
import axios from 'axios'

export interface GraphEdge {
  source: string
  target: string
  type: string
  weight: number
  metadata?: string
}

export async function getRepoEdges(repo: string, edgeTypes?: string): Promise<GraphEdge[]> {
  const params = edgeTypes ? `?edge_types=${edgeTypes}` : ''
  const response = await axios.get(`/api/graph/nodes/${repo}/edges${params}`)
  return response.data
}

export async function rebuildGraph(): Promise<{status: string, edges_count: number}> {
  const response = await axios.post('/api/graph/rebuild')
  return response.data
}

export async function getGraphStatus(): Promise<any> {
  const response = await axios.get('/api/graph/status')
  return response.data
}
```

**Step 2: 更新网络视图以支持边类型过滤**

在 NetworkView.vue 中添加边类型过滤和更好的交互。

**Step 3: 添加测试**

Run: `npm run test`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/api/graph.ts frontend/src/views/NetworkView.vue
git commit -m "feat: add graph API client and enhance network view"
```

---

### Task 8: 搜索增强 - 关联推荐

**Files:**
- Modify: `src/services/search.py`
- Modify: `frontend/src/views/SearchView.vue`

**Step 1: 修改搜索服务返回关联项目**

在搜索结果中添加 `related_repos` 字段：

```python
# In search service
async def search_with_relations(
    self,
    query: str,
    ...
) -> Dict[str, Any]:
    # Get direct matches
    results = await self.db.search_repositories(...)

    # Get related repos for top results
    related = set()
    for repo in results[:5]:  # Top 5 results
        edges = await self.db.get_graph_edges(
            repo['name_with_owner'],
            limit=3
        )
        for edge in edges:
            related.add(edge['target_repo'])

    # Remove already shown repos
    related = related - {r['name_with_owner'] for r in results}

    # Fetch full repo data for related
    related_repos = []
    for repo_name in list(related)[:5]:  # Top 5 related
        repo_data = await self.db.get_repository(repo_name)
        if repo_data:
            related_repos.append(repo_data)

    return {
        "results": results,
        "related": related_repos
    }
```

**Step 2: 更新前端显示关联**

在搜索结果页面添加"相关推荐"区域。

**Step 3: 测试**

Run: `pytest tests/unit/test_search.py -v`
Expected: Tests pass

**Step 4: Commit**

```bash
git add src/services/search.py frontend/src/views/SearchView.vue
git commit -m "feat: add related repos to search results"
```

---

### Task 9: 项目详情页 - 相关星标侧边栏

**Files:**
- Modify: `frontend/src/views/RepoDetailView.vue`
- Modify: `src/api/routes/repositories.py` (or create related endpoint)

**Step 1: 添加相关仓库 API**

```python
# In routes
@router.get("/repo/{name}/related")
async def get_related_repos(
    name: str,
    limit: int = 5,
    db = Depends(get_db)
):
    """Get repos related to the given repo."""
    edges = await db.get_graph_edges(name, limit=limit)

    # Fetch full repo data
    repos = []
    for edge in edges:
        repo = await db.get_repository(edge['target_repo'])
        if repo:
            repo['relation_type'] = edge['edge_type']
            repo['relation_weight'] = edge['weight']
            repos.append(repo)

    return {"data": repos}
```

**Step 2: 前端显示相关星标**

在 RepoDetailView.vue 中添加侧边栏组件。

**Step 3: 测试**

Run: `npm run test`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/views/RepoDetailView.vue src/api/routes/repositories.py
git commit -m "feat: add related repos sidebar to repo detail page"
```

---

### Task 10: 集成测试与文档

**Files:**
- Update: `README.md`
- Create: `tests/integration/test_graph_workflow.py`

**Step 1: 编写集成测试**

```python
# tests/integration/test_graph_workflow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_graph_workflow():
    """Test complete graph workflow: build -> query -> display."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Rebuild graph
        response = await client.post("/api/graph/rebuild")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # 2. Query edges
        response = await client.get("/api/graph/nodes/tiangolo/fastapi/edges")
        assert response.status_code == 200
        edges = response.json()
        assert isinstance(edges, list)

        # 3. Check graph status
        response = await client.get("/api/graph/status")
        assert response.status_code == 200
```

**Step 2: 运行集成测试**

Run: `pytest tests/integration/test_graph_workflow.py -v`
Expected: PASS

**Step 3: 更新 README**

在 README 中添加新功能说明：

```markdown
### 🔗 知识图谱
- **项目关联** - 自动发现项目之间的连接（作者、依赖、技术栈）
- **智能推荐** - 搜索时显示相关的星标项目
- **交互式探索** - 可视化浏览项目关联网络
```

**Step 4: 最终提交**

```bash
git add tests/integration/test_graph_workflow.py README.md
git commit -m "test: add graph integration tests and update documentation"

# 推送到远程
git push origin feature/graph-knowledge
```

---

## 完成检查清单

- [ ] 数据库迁移 004 应用成功
- [ ] 所有数据库操作方法已实现并测试
- [ ] 四种关联类型全部实现（author, dependency, ecosystem, collection）
- [ ] API 端点正常工作
- [ ] 前端图谱视图功能正常
- [ ] 搜索增强功能正常
- [ ] 项目详情页相关推荐正常
- [ ] 集成测试通过
- [ ] README 文档已更新
- [ ] 代码已推送到 feature 分支

## 下一步 (Phase 2 - 语义关联)

Phase 1 完成后，可以开始 Phase 2 实现：
- 生成项目 embedding (description + README)
- 语义相似度计算
- 更智能的关联推荐
