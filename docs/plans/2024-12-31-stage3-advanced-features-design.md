# Stage 3: Advanced Features Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to create implementation plan.

**Goal:** 在 Stage 2 基础上增强对话体验和推荐能力

**Architecture:** 在现有架构上添加 4 个新服务，增强对话上下文、查询扩展、推荐和趋势分析

**Tech Stack:** FastAPI + SQLite + ChromaDB + OpenAI (无新增依赖)

---

## 功能概述

### 1. 多轮对话上下文
- 第一轮对话始终保留 + 最近 N-1 轮对话
- 在 LLM 调用时传递上下文
- 支持引用历史对话（如"上面那个项目"）

### 2. 查询扩展
- 基于同义词词库扩展查询
- 提高搜索召回率
- 配合混合搜索使用

### 3. 仓库推荐
- 基于现有 categories 分组
- 相似仓库推荐
- 分类推荐

### 4. 趋势分析
- 时间维度：star 时间分布
- 内容维度：语言、主题趋势
- 可视化数据格式

---

## 组件设计

### ContextService
**文件**: `src/services/context.py`

**方法**:
- `get_context(session_id: str, limit: int = 5) -> str`
  - 获取第一轮对话（按时间最早）
  - 获取最近 limit-1 轮对话
  - 合并格式化为 LLM 上下文

**集成点**: `ChatService.chat_with_rag_stream()`

---

### QueryExpander
**文件**: `src/services/query_expander.py`

**词库**: `src/data/synonyms.json`
```json
{
  "ml": ["机器学习", "machine learning", "人工智能"],
  "前端": ["frontend", "ui", "web"],
  "数据库": ["database", "db", "存储"]
}
```

**方法**:
- `expand(query: str) -> list[str]`
  - 返回原查询 + 同义词扩展列表

**集成点**: `HybridSearch.search()` 之前

---

### RecommendationService
**文件**: `src/services/recommendation.py`

**方法**:
- `get_similar_repos(db: Database, repo_name: str, limit: int = 5) -> list[dict]`
  - 获取目标仓库的 categories
  - 查找共享分类的其他仓库
  - 按 star 数和相似度排序

- `get_recommended_by_category(db: Database, category: str, limit: int = 10) -> list[dict]`
  - 按分类筛选
  - 按 star 数排序

---

### TrendAnalysisService
**文件**: `src/services/trend_analysis.py`

**方法**:
- `get_star_timeline(db: Database, username: str) -> list[dict]`
  - 按月统计 star 数量
  - 返回时间序列数据

- `get_language_trend(db: Database) -> list[dict]`
  - 语言随时间的分布变化

- `get_category_evolution(db: Database) -> list[dict]`
  - 主题兴趣演变

---

## 数据库变更

### repositories 表新增字段
```sql
ALTER TABLE repositories ADD COLUMN starred_at TIMESTAMP;
```

### migrations 目录
**文件**: `src/db/migrations/`
- `001_add_starred_at.sql`

---

## API 端点

### 推荐服务
- `GET /api/recommend/similar/{name_with_owner}` - 相似仓库推荐
- `GET /api/recommend/category/{category}` - 分类推荐

### 趋势分析
- `GET /api/trends/timeline` - star 时间线
- `GET /api/trends/languages` - 语言趋势
- `GET /api/trends/categories` - 主题演变

---

## 数据流

```
用户查询
    ↓
QueryExpander.expand() → [查询1, 查询2, ...]
    ↓
IntentClassifier.classify() → intent
    ↓
┌─────────────────┬──────────────┬──────────────┐
│     chat        │     stats    │    search    │
│  ↓              │  ↓           │  ↓           │
│ ContextService  │StatsService  │HybridSearch  │
│  .get_context() │  .get_stats()│  .search()   │
│  ↓              │              │  ↓           │
│ ChatService     │              │ Recommendation│
│  .chat_with_rag │              │  Service     │
└─────────────────┴──────────────┴──────────────┘
    ↓
响应 (SSE 流式)
```

---

## 前端变更

### 新增组件
- `TrendView.vue` - 趋势分析可视化页面
- `RecommendationCard.vue` - 推荐卡片组件

### 路由
- `/trends` - 趋势分析页

---

## 测试计划

### 单元测试
- `test_context_service.py` - 上下文服务测试
- `test_query_expander.py` - 查询扩展测试
- `test_recommendation_service.py` - 推荐服务测试
- `test_trend_analysis_service.py` - 趋势分析测试

### 集成测试
- 测试完整对话流程带上下文
- 测试查询扩展 + 混合搜索
- 测试推荐结果准确性

---

## 配置项

### 环境变量
- `CONTEXT_WINDOW_SIZE` - 上下文窗口大小（默认 5）
- `ENABLE_QUERY_EXPANSION` - 是否启用查询扩展（默认 true）
- `MAX_QUERY_EXPANSIONS` - 最大扩展数量（默认 3）

---

## 实现任务清单

1. 添加 starred_at 字段到数据库
2. 实现 ContextService
3. 实现 QueryExpander + 同义词词库
4. 实现 RecommendationService
5. 实现 TrendAnalysisService
6. 添加 API 路由
7. 更新 ChatService 集成上下文
8. 更新 HybridSearch 集成查询扩展
9. 前端 TrendView 页面
10. 测试
