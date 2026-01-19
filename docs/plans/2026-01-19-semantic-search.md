# 语义搜索实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 GitHub Star Helper 添加基于 Ollama embedding 的语义搜索功能，提升搜索体验

**Architecture:** 使用 ChromaDB 存储向量，Ollama nomic-embed-text 生成 embedding，混合 FTS 和语义搜索（权重 0.3:0.7），Ollama 失败时自动降级为纯 FTS 搜索

**Tech Stack:** Ollama (nomic-embed-text), ChromaDB, Python 3.13+, FastAPI

---

## Phase 1: 基础设施（README 过滤器）

### Task 1.1: 创建 README 过滤器模块

**Files:**
- Create: `src/vector/__init__.py`
- Create: `src/vector/readme_filter.py`
- Test: `tests/unit/test_readme_filter.py`

**Step 1: 创建 vector 包**

创建 `src/vector/__init__.py`:
```python
"""Vector storage and semantic search components."""
```

**Step 2: 编写 README 过滤器的失败测试**

创建 `tests/unit/test_readme_filter.py`:
```python
import pytest
from src.vector.readme_filter import extract_readme_summary

def test_extract_summary_removes_installation_section():
    """测试过滤 Installation 章节"""
    readme = """
# Project Name

This is a great project.

## Installation

npm install project

## Usage

Run the project with npm start.
"""
    result = extract_readme_summary(readme, max_length=500)
    assert "Installation" not in result
    assert "npm install" not in result
    assert "Usage" in result
    assert "npm start" in result

def test_extract_summary_handles_empty_readme():
    """测试空 README 处理"""
    result = extract_readme_summary("", max_length=500)
    assert result == ""

def test_extract_summary_truncates_badges():
    """测试移除 Badge 徽章"""
    readme = """
![Build Status](badge.png)
![License](MIT)

# Project

A great project.
"""
    result = extract_readme_summary(readme, max_length=500)
    assert "[![" not in result
    assert "A great project" in result

def test_extract_summary_limits_length():
    """测试长度限制"""
    readme = "A" * 1000
    result = extract_readme_summary(readme, max_length=100)
    assert len(result) <= 100
```

**Step 3: 运行测试验证失败**

```bash
pytest tests/unit/test_readme_filter.py -v
```
预期: FAIL - "ModuleNotFoundError: No module named 'src.vector.readme_filter'"

**Step 4: 实现 README 过滤器**

创建 `src/vector/readme_filter.py`:
```python
import re
from typing import List

# 需要跳过的章节（中英文）
SKIP_SECTIONS = {
    "installation", "install", "getting started", "quick start",
    "quickstart", "setup", "安装", "快速开始",
    "contributing", "contribute", "贡献",
    "license", "许可证", "许可",
    "changelog", "change log", "changes", "history",
    "更新日志", "变更记录",
    "tests", "testing", "test", "测试",
    "development", "dev", "开发", "developers",
    "faq", "f.a.q", "常见问题",
    "donate", "sponsor", "捐赠", "赞助",
    "authors", "credits", "作者", "致谢",
    "acknowledgements", "acknowledgments", "致谢"
}

# 移除 Badge 徽章
BADGE_PATTERN = r'\[!\[.*?\]\(.*?\)\]\(.*?\)|\!\[.*?\]\(.*?\)'

def extract_readme_summary(readme_content: str, max_length: int = 500) -> str:
    """
    提取 README 摘要，过滤掉无关章节

    Args:
        readme_content: README 原始内容
        max_length: 最大返回字符数

    Returns:
        清理后的 README 摘要
    """
    if not readme_content:
        return ""

    # 移除 Badge 徽章
    cleaned = re.sub(BADGE_PATTERN, '', readme_content)

    # 移除代码块（可选，根据需求）
    # cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)

    lines = cleaned.split('\n')
    summary_lines = []
    current_section = None
    skipping = False

    for line in lines:
        # 检测章节标题
        section_match = re.match(r'^#{1,6}\s+(.+)$', line)
        if section_match:
            section_title = section_match.group(1).strip().lower()

            # 检查是否在黑名单中
            if any(skip_word in section_title for skip_word in SKIP_SECTIONS):
                skipping = True
                continue
            else:
                skipping = False

        # 如果不在跳过状态，添加到摘要
        if not skipping and line.strip():
            summary_lines.append(line)

        # 检查长度限制
        summary = '\n'.join(summary_lines)
        if len(summary) >= max_length:
            return summary[:max_length]

    return '\n'.join(summary_lines).strip()
```

**Step 5: 运行测试验证通过**

```bash
pytest tests/unit/test_readme_filter.py -v
```
预期: PASS (4 tests)

**Step 6: 提交**

```bash
git add src/vector/ tests/unit/test_readme_filter.py
git commit -m "feat: add README filter for semantic search

- Remove installation, license, changelog sections
- Strip badge images
- Limit summary length
- Add unit tests"
```

---

## Phase 1: 基础设施（Embedding 生成器）

### Task 1.2: 创建 Ollama Embedding 客户端

**Files:**
- Create: `src/vector/embeddings.py`
- Create: `tests/unit/test_embeddings.py`
- Modify: `requirements.txt` (如果需要添加依赖)

**Step 1: 检查依赖**

```bash
grep ollama requirements.txt || echo "需要添加 ollama 依赖"
```
如果没有，添加到 `requirements.txt`:
```
ollama>=0.4.0
```

**Step 2: 编写 Embedding 客户端的测试**

创建 `tests/unit/test_embeddings.py`:
```python
import pytest
from unittest.mock import Mock, patch
from src.vector.embeddings import OllamaEmbeddings

@pytest.fixture
def embeddings():
    return OllamaEmbeddings(base_url="http://localhost:11434")

def test_embed_text_success(embeddings, mocker):
    """测试成功生成 embedding"""
    # Mock ollama 响应
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mocker.patch('requests.post', return_value=mock_response)

    result = embeddings.embed_text("test text")

    assert len(result) == 768
    assert all(isinstance(x, float) for x in result)

def test_embed_text_timeout(embeddings, mocker):
    """测试超时处理"""
    mocker.patch('requests.post', side_effect=TimeoutError)

    result = embeddings.embed_text("test")

    # 超时时返回空向量
    assert result == []

def test_embed_batch(embeddings, mocker):
    """测试批量 embedding"""
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mocker.patch('requests.post', return_value=mock_response)

    texts = ["text1", "text2", "text3"]
    results = embeddings.embed_batch(texts)

    assert len(results) == 3
    assert all(len(r) == 768 for r in results)
```

**Step 3: 运行测试验证失败**

```bash
pytest tests/unit/test_embeddings.py -v
```
预期: FAIL - "ModuleNotFoundError"

**Step 4: 实现 Ollama Embeddings 客户端**

创建 `src/vector/embeddings.py`:
```python
import asyncio
import logging
from typing import List
import requests
from requests.exceptions import Timeout, RequestException

logger = logging.getLogger(__name__)

class OllamaEmbeddings:
    """Ollama embedding 服务客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: int = 30
    ):
        """
        初始化 Ollama embedding 客户端

        Args:
            base_url: Ollama 服务地址
            model: 使用的 embedding 模型
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self._batch_size = 10  # 每批最多处理 10 个文本

    def embed_text(self, text: str) -> List[float]:
        """
        生成单段文本的 embedding

        Args:
            text: 输入文本

        Returns:
            embedding 向量（768 维），失败返回空列表
        """
        if not text or not text.strip():
            return []

        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            embedding = data.get("embedding", [])

            if not embedding:
                logger.warning(f"Empty embedding received for text: {text[:50]}...")

            return embedding

        except Timeout:
            logger.error(f"Ollama timeout after {self.timeout}s")
            return []
        except RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成 embedding

        Args:
            texts: 文本列表

        Returns:
            embedding 向量列表
        """
        results = []

        # 分批处理，避免过载
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]

            # 并行处理当前批次
            batch_results = [self.embed_text(text) for text in batch]
            results.extend(batch_results)

        return results

    def check_health(self) -> bool:
        """
        检查 Ollama 服务是否可用

        Returns:
            True 如果服务正常，否则 False
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
```

**Step 5: 运行测试验证通过**

```bash
pytest tests/unit/test_embeddings.py -v
```
预期: PASS (3 tests)

**Step 6: 提交**

```bash
git add src/vector/embeddings.py tests/unit/test_embeddings.py
git commit -m "feat: add Ollama embedding client

- Implement text and batch embedding
- Add timeout and error handling
- Add health check method
- Add unit tests with mocks"
```

---

## Phase 1: 基础设施（ChromaDB 存储）

### Task 1.3: 创建 ChromaDB 向量存储

**Files:**
- Create: `src/vector/chroma_store.py`
- Create: `tests/unit/test_chroma_store.py`

**Step 1: 检查依赖**

```bash
grep chromadb requirements.txt || echo "chromadb>=0.4.0" >> requirements.txt
```

**Step 2: 编写 ChromaDB 存储测试**

创建 `tests/unit/test_chroma_store.py`:
```python
import pytest
import tempfile
import shutil
from src.vector.chroma_store import ChromaDBStore

@pytest.fixture
def temp_store():
    """创建临时 ChromaDB 存储"""
    temp_dir = tempfile.mkdtemp()
    store = ChromaDBStore(persist_path=temp_dir)
    yield store
    shutil.rmtree(temp_dir)

def test_add_repository(temp_store):
    """测试添加仓库向量"""
    repo_id = "test/repo"
    text = "Test repository description"
    embedding = [0.1] * 768
    metadata = {"language": "Python", "stars": 100}

    temp_store.add(repo_id, text, embedding, metadata)

    # 验证添加成功
    results = temp_store.search(embedding, top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == repo_id

def test_search_returns_empty_when_no_data(temp_store):
    """测试空数据库搜索"""
    results = temp_store.search([0.1] * 768, top_k=5)
    assert results == []

def test_delete_repository(temp_store):
    """测试删除仓库"""
    repo_id = "test/repo"
    temp_store.add(repo_id, "test", [0.1] * 768, {})

    temp_store.delete(repo_id)

    results = temp_store.search([0.1] * 768, top_k=5)
    assert results == []
```

**Step 3: 运行测试验证失败**

```bash
pytest tests/unit/test_chroma_store.py -v
```
预期: FAIL - "ModuleNotFoundError"

**Step 4: 实现 ChromaDB 存储**

创建 `src/vector/chroma_store.py`:
```python
import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class ChromaDBStore:
    """ChromaDB 向量存储管理"""

    def __init__(
        self,
        persist_path: str = "data/chromadb",
        collection_name: str = "github_repos"
    ):
        """
        初始化 ChromaDB 存储

        Args:
            persist_path: 持久化路径
            collection_name: 集合名称
        """
        self.persist_path = persist_path
        self.collection_name = collection_name

        # 初始化客户端
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 余弦相似度
        )

        logger.info(f"ChromaDB initialized at {persist_path}")

    def add(
        self,
        repo_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, any]
    ) -> None:
        """
        添加仓库向量

        Args:
            repo_id: 仓库唯一标识 (name_with_owner)
            text: 原始文本
            embedding: embedding 向量
            metadata: 元数据
        """
        try:
            self.collection.add(
                ids=[repo_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            logger.debug(f"Added embedding for {repo_id}")
        except Exception as e:
            logger.error(f"Failed to add {repo_id}: {e}")

    def add_batch(
        self,
        repo_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, any]]
    ) -> int:
        """
        批量添加仓库向量

        Args:
            repo_ids: 仓库 ID 列表
            texts: 文本列表
            embeddings: embedding 向量列表
            metadata_list: 元数据列表

        Returns:
            成功添加的数量
        """
        if not repo_ids:
            return 0

        try:
            self.collection.add(
                ids=repo_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata_list
            )
            logger.info(f"Added {len(repo_ids)} embeddings")
            return len(repo_ids)
        except Exception as e:
            logger.error(f"Batch add failed: {e}")
            return 0

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        向量搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            where: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )

            # 格式化结果
            formatted = []
            if results and results['ids'] and results['ids'][0]:
                for i, repo_id in enumerate(results['ids'][0]):
                    formatted.append({
                        "id": repo_id,
                        "score": 1 - results['distances'][0][i],  # 转换为相似度
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })

            return formatted

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete(self, repo_id: str) -> None:
        """
        删除仓库向量

        Args:
            repo_id: 仓库 ID
        """
        try:
            self.collection.delete(ids=[repo_id])
            logger.debug(f"Deleted {repo_id}")
        except Exception as e:
            logger.error(f"Failed to delete {repo_id}: {e}")

    def get_count(self) -> int:
        """
        获取向量总数

        Returns:
            向量数量
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get count: {e}")
            return 0

    def clear(self) -> None:
        """清空所有数据"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.warning("Cleared all embeddings")
        except Exception as e:
            logger.error(f"Failed to clear: {e}")
```

**Step 5: 运行测试验证通过**

```bash
pytest tests/unit/test_chroma_store.py -v
```
预期: PASS (4 tests)

**Step 6: 提交**

```bash
git add src/vector/chroma_store.py tests/unit/test_chroma_store.py
git commit -m "feat: add ChromaDB vector store

- Implement add, search, delete operations
- Add batch processing support
- Add count and clear methods
- Add unit tests with temp directory"
```

---

## Phase 2: 向量化服务

### Task 2.1: 创建向量化服务

**Files:**
- Create: `src/services/vectorization.py`
- Create: `tests/unit/test_vectorization.py`

**Step 1: 编写向量化服务测试**

创建 `tests/unit/test_vectorization.py`:
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.vectorization import VectorizationService

@pytest.fixture
def mock_embeddings():
    with patch('src.services.vectorization.OllamaEmbeddings') as mock:
        instance = mock.return_value
        instance.embed_text.return_value = [0.1] * 768
        yield instance

@pytest.fixture
def mock_store():
    with patch('src.services.vectorization.ChromaDBStore') as mock:
        instance = mock.return_value
        instance.add_batch.return_value = 1
        yield instance

@pytest.mark.asyncio
async def test_index_repository(mock_embeddings, mock_store):
    """测试索引单个仓库"""
    service = VectorizationService(mock_embeddings, mock_store)

    repo = {
        "name_with_owner": "test/repo",
        "name": "repo",
        "description": "Test repo",
        "readme_content": "# Test\n\nA great project"
    }

    result = await service.index_repository(repo)

    assert result is True
    mock_embeddings.embed_text.assert_called_once()
    mock_store.add.assert_called_once()

@pytest.mark.asyncio
async def test_index_batch(mock_embeddings, mock_store):
    """测试批量索引"""
    service = VectorizationService(mock_embeddings, mock_store)

    repos = [
        {
            "name_with_owner": f"test/repo{i}",
            "name": f"repo{i}",
            "description": f"Test {i}",
            "readme_content": "Content"
        }
        for i in range(5)
    ]

    count = await service.index_batch(repos)

    assert count == 5
    assert mock_embeddings.embed_text.call_count == 5
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_vectorization.py -v
```
预期: FAIL - "ModuleNotFoundError"

**Step 3: 实现向量化服务**

创建 `src/services/vectorization.py`:
```python
import logging
from typing import List, Dict, Any
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.vector.readme_filter import extract_readme_summary

logger = logging.getLogger(__name__)

class VectorizationService:
    """仓库向量化服务"""

    def __init__(
        self,
        embeddings: OllamaEmbeddings,
        store: ChromaDBStore
    ):
        """
        初始化向量化服务

        Args:
            embeddings: Embedding 生成器
            store: 向量存储
        """
        self.embeddings = embeddings
        self.store = store

    def _prepare_text(self, repo: Dict[str, Any]) -> str:
        """
        准备用于 embedding 的文本

        Args:
            repo: 仓库数据

        Returns:
            拼接后的文本
        """
        name = repo.get("name", "")
        description = repo.get("description", "")
        readme = repo.get("readme_content", "")

        # 提取 README 摘要
        readme_summary = extract_readme_summary(readme, max_length=500)

        # 拼接文本
        parts = []
        if name:
            parts.append(name)
        if description:
            parts.append(f"- {description}")
        if readme_summary:
            parts.append(f"\n\n{readme_summary}")

        return " ".join(parts)

    def _prepare_metadata(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备元数据

        Args:
            repo: 仓库数据

        Returns:
            元数据字典
        """
        return {
            "name": repo.get("name", ""),
            "owner": repo.get("owner", ""),
            "primary_language": repo.get("primary_language", ""),
            "stargazer_count": repo.get("stargazer_count", 0),
            "topics": str(repo.get("topics", []))
        }

    async def index_repository(self, repo: Dict[str, Any]) -> bool:
        """
        为单个仓库生成并存储 embedding

        Args:
            repo: 仓库数据

        Returns:
            是否成功
        """
        try:
            repo_id = repo.get("name_with_owner")
            if not repo_id:
                logger.warning("Repository missing name_with_owner")
                return False

            # 准备文本
            text = self._prepare_text(repo)
            if not text or len(text.strip()) < 10:
                logger.warning(f"Insufficient text for {repo_id}")
                return False

            # 生成 embedding
            embedding = self.embeddings.embed_text(text)
            if not embedding:
                logger.error(f"Failed to generate embedding for {repo_id}")
                return False

            # 准备元数据
            metadata = self._prepare_metadata(repo)

            # 存储向量
            self.store.add(repo_id, text, embedding, metadata)

            logger.debug(f"Indexed {repo_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index repository: {e}")
            return False

    async def index_batch(self, repos: List[Dict[str, Any]]) -> int:
        """
        批量索引仓库

        Args:
            repos: 仓库列表

        Returns:
            成功索引的数量
        """
        if not repos:
            return 0

        repo_ids = []
        texts = []
        embeddings = []
        metadata_list = []

        success_count = 0

        for repo in repos:
            try:
                repo_id = repo.get("name_with_owner")
                if not repo_id:
                    continue

                # 准备文本
                text = self._prepare_text(repo)
                if not text or len(text.strip()) < 10:
                    continue

                # 生成 embedding
                embedding = self.embeddings.embed_text(text)
                if not embedding:
                    logger.warning(f"Skipping {repo_id}: no embedding generated")
                    continue

                # 准备元数据
                metadata = self._prepare_metadata(repo)

                repo_ids.append(repo_id)
                texts.append(text)
                embeddings.append(embedding)
                metadata_list.append(metadata)
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to prepare {repo.get('name_with_owner')}: {e}")

        # 批量添加到存储
        if repo_ids:
            self.store.add_batch(repo_ids, texts, embeddings, metadata_list)
            logger.info(f"Batch indexed {success_count}/{len(repos)} repositories")

        return success_count
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_vectorization.py -v
```
预期: PASS (2 tests)

**Step 5: 提交**

```bash
git add src/services/vectorization.py tests/unit/test_vectorization.py
git commit -m "feat: add vectorization service

- Implement single and batch repository indexing
- Combine name, description, and README summary
- Prepare metadata for filtering
- Add unit tests"
```

---

## Phase 3: 搜索集成

### Task 3.1: 更新 HybridSearch 启用语义搜索

**Files:**
- Modify: `src/services/hybrid_search.py`
- Modify: `src/api/app.py`

**Step 1: 检查现有 HybridSearch 代码**

```bash
grep -n "semantic" src/services/hybrid_search.py | head -20
```

**Step 2: 编写集成测试**

创建 `tests/integration/test_hybrid_search.py`:
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
async def test_hybrid_search_with_semantic():
    """测试混合搜索包含语义搜索结果"""
    with patch('src.services.hybrid_search.SemanticSearch') as mock_semantic_class:
        # 设置 mock
        mock_semantic = AsyncMock()
        mock_semantic.search.return_value = [
            {"name_with_owner": "semantic/repo", "match_type": "semantic"}
        ]
        mock_semantic_class.return_value = mock_semantic

        from src.services.hybrid_search import HybridSearch

        # 创建 HybridSearch（传入 semantic 实例）
        from src.db import Database
        # 这里需要 mock db
        # ...
```

**Step 3: 修改 HybridSearch 配置**

在 `src/api/app.py` 中初始化 SemanticSearch:

```python
# 在导入部分添加
from src.vector.embeddings import OllamaEmbeddings
from src.vector.chroma_store import ChromaDBStore
from src.vector.semantic import SemanticSearch

# 在 FastAPI app 初始化后添加
@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    # ... 现有代码 ...

    # 初始化语义搜索（可选）
    try:
        embeddings = OllamaEmbeddings()
        if embeddings.check_health():
            store = ChromaDBStore()
            semantic_search = SemanticSearch(store, embeddings)

            # 更新 HybridSearch
            from src.services.hybrid_search import HybridSearch
            hybrid_search = HybridSearch(
                db=db,
                semantic=semantic_search,  # 启用语义搜索
                fts_weight=0.3,
                semantic_weight=0.7
            )
            logger.info("Semantic search enabled")
        else:
            logger.warning("Ollama not available, semantic search disabled")
    except Exception as e:
        logger.error(f"Failed to initialize semantic search: {e}")
```

**Step 4: 提交**

```bash
git add src/services/hybrid_search.py src/api/app.py
git commit -m "feat: enable semantic search in HybridSearch

- Initialize OllamaEmbeddings and ChromaDBStore on startup
- Create SemanticSearch instance if Ollama is available
- Pass to HybridSearch with configured weights
- Graceful degradation if Ollama not available"
```

---

## Phase 3: 健康检查

### Task 3.2: 添加向量搜索状态端点

**Files:**
- Create: `src/api/routes/vector.py`
- Modify: `src/api/app.py`

**Step 1: 创建向量状态路由**

创建 `src/api/routes/vector.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/vector", tags=["vector"])

class VectorStatusResponse(BaseModel):
    """向量搜索状态响应"""
    enabled: bool
    ollama_running: bool
    model: Optional[str] = None
    indexed_count: int
    total_count: int
    last_indexed_at: Optional[str] = None

@router.get("/status", response_model=VectorStatusResponse)
async def get_vector_status():
    """获取向量搜索状态"""
    from src.api.app import db

    # 检查是否启用
    enabled = False
    ollama_running = False
    model = None

    try:
        from src.vector.embeddings import OllamaEmbeddings
        embeddings = OllamaEmbeddings()
        ollama_running = embeddings.check_health()
        model = embeddings.model if ollama_running else None
        enabled = True
    except Exception:
        pass

    # 获取索引数量
    indexed_count = 0
    try:
        from src.vector.chroma_store import ChromaDBStore
        store = ChromaDBStore()
        indexed_count = store.get_count()
    except Exception:
        pass

    # 获取总仓库数
    total_count = 0
    try:
        cursor = await db._connection.execute(
            "SELECT COUNT(*) FROM repositories WHERE is_deleted = 0"
        )
        result = await cursor.fetchone()
        total_count = result[0] if result else 0
    except Exception:
        pass

    return VectorStatusResponse(
        enabled=enabled,
        ollama_running=ollama_running,
        model=model,
        indexed_count=indexed_count,
        total_count=total_count
    )
```

**Step 2: 注册路由**

在 `src/api/app.py` 中添加:

```python
from src.api.routes import vector

app.include_router(vector.router)
```

**Step 3: 测试端点**

```bash
# 启动服务
uvicorn src.api.app:app --reload --port 8889

# 测试端点（另一个终端）
curl http://localhost:8889/api/vector/status
```

预期返回:
```json
{
  "enabled": true,
  "ollama_running": false,
  "model": null,
  "indexed_count": 0,
  "total_count": 941
}
```

**Step 4: 提交**

```bash
git add src/api/routes/vector.py src/api/app.py
git commit -m "feat: add vector status endpoint

- Add /api/vector/status endpoint
- Check Ollama availability
- Report indexed vs total repository count
- Return model information"
```

---

## 验收标准

### 功能验收

- [ ] README 过滤器能正确移除 Installation/License 等章节
- [ ] Ollama Embeddings 客户端能生成 768 维向量
- [ ] ChromaDB 存储能添加、搜索、删除向量
- [ ] 向量化服务能批量索引仓库
- [ ] HybridSearch 能使用语义搜索
- [ ] `/api/vector/status` 端点返回正确状态

### 性能验收

- [ ] 单个仓库索引时间 < 1 秒
- [ ] 批量索引（10 个）< 5 秒
- [ ] 语义搜索查询 < 500ms

### 降级验收

- [ ] Ollama 未启动时，自动降级为纯 FTS 搜索
- [ ] Ollama 超时时，自动降级为纯 FTS 搜索
- [ ] 用户无感知降级（不显示错误）

---

## 后续步骤

完成本计划后，可以继续：

1. **前端适配**：在初始化页面添加"启用语义搜索"开关
2. **性能优化**：添加向量缓存，减少重复计算
3. **监控**：添加 embedding 生成成功率和延迟监控
4. **下一功能**：实现项目相似度推荐（第二阶段）
