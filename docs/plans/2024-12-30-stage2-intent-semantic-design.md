# Stage 2: 意图识别与语义搜索设计

**目标：** 理解用户意图，提供智能的混合搜索

---

## 架构概述

```
用户输入 → 意图分类 → [chat → 直接回复]
                      → [stats → 聚合查询]
                      → [search → 混合搜索 → 结果返回]
```

---

## 1. 意图分类器 (IntentClassifier)

**文件：** `src/services/intent.py`

```python
class IntentResult(BaseModel):
    intent: Literal["chat", "stats", "search"]
    keywords: str | None = None
    confidence: float = 1.0

class IntentClassifier:
    async def classify(self, query: str) -> IntentResult:
        """
        使用 LLM 分类用户意图

        Prompt:
        - "你好、谢谢" → chat
        - "多少、分布" → stats
        - "找、推荐" → search
        """
```

---

## 2. 语义搜索 (SemanticSearch)

**文件：** `src/vector/semantic.py`

```python
class OllamaEmbedder:
    async def embed(self, text: str) -> list[float]:
        """调用 Ollama API 生成向量"""

class SemanticSearch:
    def __init__(self, ollama_base_url, model="nomic-embed-text"):
        self.collection = chromadb.PersistentClient(
            path="data/chromadb"
        ).get_or_create_collection("github_repos")

    async def add_repositories(self, repos: list[dict]):
        """批量添加仓库到向量库"""

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """语义搜索返回相似仓库"""
```

---

## 3. 混合搜索 (HybridSearch)

**文件：** `src/services/hybrid_search.py`

```python
class HybridSearch:
    fts_weight = 0.3
    semantic_weight = 0.7

    async def search(
        self, query: str, keywords: str | None = None
    ) -> list[dict]:
        """并行执行 FTS 和向量搜索，合并结果"""
        # 并行搜索
        fts_results = await self._fts_search(keywords or query)
        semantic_results = await self.semantic.search(query)

        # 加权合并
        return self._merge_and_rerank(fts_results, semantic_results)
```

---

## 4. 统计服务 (StatsService)

**文件：** `src/services/stats.py`

```python
class StatsService:
    async def get_stats(self, query: str, db: Database) -> str:
        """LLM 提取统计维度，执行聚合查询，返回文本"""

    async def _stats_by_language(self) -> dict:
        """按语言统计"""

    async def _stats_by_category(self) -> dict:
        """按分类统计"""
```

---

## 5. 初始化流程改造

**文件：** `src/services/init.py`

```python
class InitializationService:
    def __init__(self, db, llm, semantic: SemanticSearch | None = None):
        self.semantic = semantic

    async def initialize_from_stars(self, ...):
        # 现有逻辑

        # 新增：生成向量嵌入
        if self.semantic:
            await self.semantic.add_repositories(repos)
```

**API 扩展：**

```python
# src/api/routes/init.py
class InitRequest(BaseModel):
    enable_semantic: bool = False  # 新增
```

---

## 6. Chat API 改造

**文件：** `src/api/routes/chat.py`

```python
@router.post("/stream")
async def chat_stream(request: ChatRequest):
    # 1. 意图分类
    intent = await IntentClassifier(llm).classify(request.message)

    # 2. 路由处理
    if intent.intent == "chat":
        return _simple_chat(llm, request.message)
    elif intent.intent == "stats":
        return await StatsService().get_stats(request.message, db)
    else:  # search
        results = await HybridSearch(db, semantic).search(
            request.message, intent.keywords
        )
        return _rag_stream(llm, request.message, results)
```

---

## 7. 前端适配

**文件：** `frontend/src/views/InitView.vue`

```vue
<label>
  <input v-model="enableSemantic" type="checkbox">
  启用语义搜索（首次需生成向量）
</label>
```

---

## 8. 错误处理

- 意图分类失败 → 默认 search
- FTS 失败 → 只用向量搜索
- 向量搜索失败 → 只用 FTS
- 两者都失败 → 抛出错误

---

## 9. 测试

```python
# tests/unit/test_intent.py
test_intent_classification()

# tests/unit/test_hybrid_search.py
test_hybrid_search_merge()

# tests/integration/test_intent_flow.py
test_chat_stats_search_flow()
```

---

## 依赖

```
chromadb>=0.4.0
```
