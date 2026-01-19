# 语义搜索增强设计文档

**日期**: 2026-01-19
**状态**: 设计完成
**作者**: Claude + User

---

## 概述

为 GitHub Star Helper 项目添加语义搜索功能，通过 Ollama 本地 embedding 模型提升搜索体验，让搜索引擎能够理解查询意图而非仅仅匹配关键词。

**目标**：
- ✅ 概念理解：搜索"异步任务队列"能找到 Celery、RQ、Bull 等项目
- ✅ 模糊匹配：搜索"数据可视化"能找到 D3、ECharts、Plotly
- ✅ 技术栈关联：搜索"Vue 生态"能找到 Vue Router、Pinia、Vite
- ✅ 降级策略：Ollama 失败时自动切换为纯 FTS 搜索

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│   API Layer (搜索接口)                  │
│   /api/search?q=机器学习框架             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   HybridSearch (混合搜索编排)            │
│   - FTS 权重: 0.3                       │
│   - Semantic 权重: 0.7                  │
└──────┬───────────────────┬──────────────┘
       │                   │
┌──────▼──────┐    ┌──────▼──────────────┐
│ FTS Search  │    │ SemanticSearch      │
│ (现有)      │    │ (新增)              │
└─────────────┘    │ - 生成 query embedding│
                   │ - ChromaDB 向量检索  │
                   └──────────────────────┘
```

### 数据流

1. 用户输入查询 → 混合搜索并行执行 FTS 和语义搜索
2. 语义搜索：调用 Ollama 生成 query embedding → ChromaDB 检索最相似的 N 个项目
3. 合并结果，按权重打分排序返回
4. Ollama 失败时自动降级为纯 FTS 搜索

---

## 核心组件

### 1. README 过滤器 (`src/vector/readme_filter.py`)

**职责**：提取 README 的核心内容，去除噪音章节

```python
def extract_readme_summary(readme_content: str, max_length: int = 500) -> str:
    """
    提取 README 摘要，过滤掉无关章节

    跳过的章节：
    - Installation / 安装 / Quick Start
    - Contributing / 贡献
    - License / 许可证
    - Changelog / 更新日志
    - Tests / 测试
    - Development / 开发

    返回前 max_length 字符的核心内容
    """
```

**实现策略**：
- 按行扫描，识别章节标题（`## xxx`）
- 跳过黑名单章节，保留 Overview/Features/Usage
- 如果没有明确章节，取前 500 字
- 移除 Badge 徽章（`[![](...)]`）
- 移除代码块（```code...```）

---

### 2. Embedding 生成器 (`src/vector/embeddings.py`)

**职责**：封装 Ollama embedding 调用

```python
class OllamaEmbeddings:
    def embed_text(self, text: str) -> list[float]:
        """生成单段文本的 embedding"""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成 embedding（优化性能）"""
```

**优化点**：
- 批量处理：每次最多 10 个文本，避免 Ollama 过载
- 超时控制：30 秒超时，失败返回空向量
- 重试机制：失败自动重试 2 次

---

### 3. 向量化服务 (`src/services/vectorization.py`)

**职责**：将仓库数据转换为 embedding 并存入 ChromaDB

```python
class VectorizationService:
    async def index_repository(self, repo: dict) -> bool:
        """为单个仓库生成并存储 embedding"""

    async def index_batch(self, repos: list[dict]) -> int:
        """批量索引仓库，返回成功数量"""
```

**文本拼接策略**：
```
"{name} - {description}. \n\n{readme_summary}"
```

**示例**：
```
"FastAPI - 现代高性能 Web 框架。

FastAPI 是一个基于 Python 3.6+ 类型提示的 Web 框架，具有以下特性：
- 快速：与 NodeJS 和 Go 相当
- 快速编码：将开发速度提高 200-300%
..."
```

---

### 4. ChromaDB 存储 (`src/vector/chroma_store.py`)

**职责**：管理 ChromaDB 向量数据库

```python
class ChromaDBStore:
    """ChromaDB 向量存储管理"""

    def __init__(self, persist_path: str = "data/chromadb"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name="github_repos",
            metadata={"hnsw:space": "cosine"}
        )
```

**数据结构**：
- `id`: 仓库唯一标识（`name_with_owner`）
- `embedding`: 768 维向量（nomic-embed-text）
- `document`: 拼接后的文本
- `metadata`: 用于过滤的字段（`primary_language`, `categories`, `stargazer_count`）

---

## 初始化和更新策略

### 初始化流程

**入口**：`/api/init/start` 启动时增加可选参数 `enable_semantic`

**流程**：
1. 用户点击"启用语义搜索"开关
2. 遍历所有仓库，为每个生成 embedding
3. 批量存入 ChromaDB（每批 10 个）
4. 显示进度条："正在索引 120/941..."
5. 完成后标记 `semantic_enabled=true`

**性能**：
- 941 个仓库 × 5秒/批 ≈ 8 分钟（可接受）
- 前端支持"后台运行"，初始化后可关闭页面

---

### 增量更新策略

**触发时机**：
- 每日同步新仓库时 → 自动为新仓库生成 embedding
- 仓库 README 重大更新时（`readme_updated_at` 变化）→ 重新生成 embedding

**实现位置**：`src/services/sync.py` 中的 `_process_updates()`

```python
# 同步后自动索引新仓库
if new_repos:
    vectorization_service.index_batch(new_repos)
```

---

## 错误处理和降级策略

### 降级机制

**核心原则**：语义搜索失败时，自动降级为纯 FTS 搜索，不影响用户体验

**异常场景**：

```python
async def search(self, query: str, top_k: int = 10) -> list[dict]:
    try:
        semantic_results = await self._semantic_search(query, top_k)
    except OllamaTimeoutError:
        logger.warning("Ollama timeout, falling back to FTS only")
        return await self._fts_search(query, top_k * 2)
    except OllamaConnectionError:
        logger.warning("Ollama not available, using FTS only")
        return await self._fts_search(query, top_k * 2)
```

---

### 边界情况处理

**空 README**：
- 仓库没有 README → 只使用 `{name} - {description}`
- 描述为空 → 只使用 `{name}`

**README 过滤后为空**：
- 过滤后内容不足 50 字 → 使用原 README 前 200 字

**超长文本**：
- 单个仓库文本超过 2000 字 → 截断到 2000 字

**特殊字符**：
- 移除大量代码块
- 保留 Markdown 格式（标题、列表）

---

### 健康检查

**新增端点**：`GET /api/vector/status`

```json
{
  "enabled": true,
  "ollama_running": true,
  "model": "nomic-embed-text",
  "indexed_count": 941,
  "total_count": 941,
  "last_indexed_at": "2026-01-19T12:00:00Z"
}
```

---

## 测试策略

### 单元测试

`tests/unit/test_readme_filter.py`:
```python
def test_extract_summary_removes_installation():
    """测试过滤 Installation 章节"""

def test_extract_summary_handles_empty_readme():
    """测试空 README 处理"""

def test_extract_summary_truncates_badges():
    """测试移除 Badge 徽章"""
```

---

### 集成测试

`tests/integration/test_semantic_search.py`:
```python
async def test_semantic_search_with_mock_ollama():
    """Mock Ollama 返回固定向量"""

async def test_hybrid_search_merges_results():
    """测试 FTS 和语义搜索结果合并"""

async def test_fallback_to_fts_on_ollama_failure():
    """测试 Ollama 失败时的降级"""
```

---

## 实施计划

### Phase 1: 基础设施（1-2天）
1. ✅ 实现 `readme_filter.py` - README 过滤器
2. ✅ 实现 `chroma_store.py` - ChromaDB 封装
3. ✅ 实现 `embeddings.py` - Ollama embedding 调用
4. ✅ 单元测试

### Phase 2: 向量化服务（1天）
5. ✅ 实现 `vectorization_service.py` - 批量索引
6. ✅ 集成到 `/api/init/start` - 初始化流程
7. ✅ 集成到 `sync.py` - 增量更新

### Phase 3: 搜索集成（1天）
8. ✅ 修改 `HybridSearch` - 启用语义搜索
9. ✅ 实现 `/api/vector/status` - 健康检查
10. ✅ 集成测试

### Phase 4: 前端适配（可选，0.5天）
11. ⚪ 初始化页面增加"启用语义搜索"开关
12. ⚪ 搜索结果显示匹配类型标签（FTS/语义/混合）

---

## 性能指标

**预期效果**：
- 初始化 941 个仓库：~8 分钟
- 单次查询延迟：200-500ms（Ollama embedding 生成）
- 存储空间：~50MB（ChromaDB 向量数据）

**优化方向**（后续迭代）：
- 向量缓存：相同 query 不重复生成 embedding
- 批量查询优化：提高并发数

---

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| Embedding 模型 | Ollama nomic-embed-text | 本地免费，隐私安全 |
| 向量数据库 | ChromaDB | 轻量级，支持持久化 |
| 搜索架构 | 混合搜索（FTS + 语义） | 平衡准确性和召回率 |
| 权重配置 | FTS: 0.3, Semantic: 0.7 | 语义理解优先 |

---

## 后续功能扩展

本设计是第一阶段（提升搜索体验），后续可添加：

### 第二阶段：发现隐藏关联
- 项目相似度推荐
- 同一作者项目发现
- 技术栈关联分析

### 第三阶段：增强对话能力
- AI 助手基于向量检索增强回答
- 上下文感知推荐

---

## 相关文档

- [FTS5 全文搜索指南](../fts5-guide.md)
- [业务逻辑文档](../business-logic.md)
- [产品计划](../../product_plan.md)
