# GitHub 星标图谱知识系统 - 业务逻辑文档

## 概述

本系统通过构建仓库之间的关系图谱，帮助用户发现 GitHub 星标项目之间的关联，实现智能召回和知识沉淀。

## 架构设计

### 数据流

```
仓库数据 (repositories)
    ↓
边发现服务 (EdgeDiscoveryService)
    ↓
图谱边表 (graph_edges)
    ↓
前端展示 (3个位置)
```

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| 边发现服务 | `src/services/graph/edges.py` | 发现仓库间关系 |
| 图谱 API | `src/api/routes/graph.py` | 提供 HTTP 接口 |
| 数据库操作 | `src/db/sqlite.py` | 持久化存储 |
| 前端展示 | `frontend/src/views/*` | 用户界面 |

---

## 边发现逻辑

### 1. 作者边 (Author Edges)

**目的**: 发现同一作者/组织的其他仓库

**逻辑**:
1. 按 `owner` 字段分组仓库
2. 对每个有多于 1 个仓库的作者，创建所有两两配对
3. 边权重固定为 1.0

**数据结构**:
```json
{
  "source": "owner/repo1",
  "target": "owner/repo2",
  "type": "author",
  "weight": 1.0,
  "metadata": {"author": "owner"}
}
```

**示例**:
```
输入: [
  {"owner": "anthropics", "name_with_owner": "anthropics/claude-docs"},
  {"owner": "anthropics", "name_with_owner": "anthropics/claude-cookbook"}
]

输出: [
  {
    "source": "anthropics/claude-docs",
    "target": "anthropics/claude-cookbook",
    "type": "author",
    "weight": 1.0,
    "metadata": {"author": "anthropics"}
  }
]
```

---

### 2. 技术生态边 (Ecosystem Edges)

**目的**: 发现使用相同技术栈或有相关主题的仓库

**逻辑**:
1. **语言匹配**: 按 `primary_language` 分组
   - 只处理有 2-49 个仓库的语言（避免热门语言产生过多边）
   - 每种语言最多取前 20 个仓库
   - 权重固定为 0.6

2. **主题匹配**: 使用 Jaccard 相似度
   - 计算公式: `J(A,B) = |A∩B| / |A∪B|`
   - 条件: 至少 2 个共同主题 且 Jaccard > 0.3
   - 权重为 Jaccard 相似度值（保留 2 位小数）

**数据结构**:
```json
{
  "source": "owner/repo1",
  "target": "owner/repo2",
  "type": "ecosystem",
  "weight": 0.6,
  "metadata": {"language": "Python"}
}
```

**示例**:
```
语言匹配:
两个 Python 仓库 → 边权重 0.6

主题匹配:
Repo1 topics: ["web", "api", "http"]
Repo2 topics: ["web", "api", "graphql"]
Jaccard = 2/4 = 0.5 > 0.3 → 创建边，权重 0.5
```

---

### 3. 收藏边 (Collection Edges)

**目的**: 发现被归入同一收藏夹的仓库

**逻辑**:
1. 查询 `repo_collections` 表，找到同一 `collection_id` 的仓库对
2. 使用 `c1.repo_id < c2.repo_id` 避免重复
3. 边权重固定为 0.5

**数据结构**:
```json
{
  "source": "repo_id_1",
  "target": "repo_id_2",
  "type": "collection",
  "weight": 0.5,
  "metadata": {"collection": "collection_name"}
}
```

**SQL 查询**:
```sql
SELECT c1.repo_id as source_repo,
       c2.repo_id as target_repo,
       col.name as collection_name
FROM repo_collections c1
JOIN repo_collections c2 ON c1.collection_id = c2.collection_id
JOIN collections col ON col.id = c1.collection_id
WHERE c1.repo_id < c2.repo_id
```

---

## 图谱重建逻辑

### 端点: `POST /api/graph/rebuild`

**流程**:
```
1. 获取所有仓库 (limit=1000)
   ↓
2. 发现作者边
3. 发现技术生态边
4. 发现收藏边
   ↓
5. 清空旧边数据
   ↓
6. 批量插入新边
   ↓
7. 更新所有仓库的图谱状态
   ↓
8. 返回结果
```

**状态更新**:
- 每个仓库的 `graph_status.edges_computed_at` 更新为当前时间
- 确保 Network View 能正确显示"Edge computation completed"

---

## 相关仓库查询逻辑

### 端点: `GET /api/graph/nodes/{repo:path}/related`

**流程**:
```
1. 获取指定仓库的所有边
   ↓
2. 按权重降序排序 (limit=5)
   ↓
3. 获取每个目标仓库的完整信息
   ↓
4. 组装返回数据
```

**返回数据结构**:
```json
{
  "data": [
    {
      "name_with_owner": "anthropics/claude-docs",
      "name": "claude-docs",
      "owner": "anthropics",
      "description": "...",
      "primary_language": "Python",
      "stargazer_count": 42663,
      "relation_type": "author",
      "relation_weight": 1.0
    }
  ]
}
```

---

## 前端展示逻辑

### 1. Repo 详情页 - 相关星标侧边栏

**位置**: 右侧固定面板

**数据来源**: `GET /api/graph/nodes/{repo}/related`

**显示内容**:
- 仓库卡片（名称、描述、语言、星标数）
- 关系类型标签（同一作者 / 技术生态 / 同一收藏）
- 关系权重进度条

**代码位置**: `frontend/src/views/RepoDetailView.vue`

---

### 2. Search 页面 - 关联推荐

**位置**: 搜索结果上方

**数据来源**: `GET /api/search?include_related=true`

**触发条件**:
- 第一页搜索结果 (`page === 1`)
- 后端返回 `related` 字段

**显示内容**:
- 5 个网格布局的仓库卡片
- 标注"基于知识图谱"

**代码位置**: `frontend/src/views/SearchView.vue`

---

### 3. Network View 页面 - 图谱可视化

**位置**: 独立页面 `/network`

**功能**:
- **Graph Status**: 显示图谱计算状态
- **Graph Controls**: Rebuild、Force Layout、Circular Layout、Export
- **Graph Canvas**: Echarts 力导向图可视化

**代码位置**: `frontend/src/views/NetworkView.vue`

---

## 数据库表结构

### graph_edges

| 字段 | 类型 | 说明 |
|------|------|------|
| source_repo | TEXT | 源仓库 name_with_owner |
| target_repo | TEXT | 目标仓库 name_with_owner |
| edge_type | TEXT | 边类型: author/ecosystem/collection |
| weight | REAL | 边权重 0-1 |
| metadata | TEXT | JSON 格式的额外信息 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

**主键**: (source_repo, target_repo, edge_type)

**索引**:
- `idx_edges_source`: (source_repo, weight DESC)
- `idx_edges_target`: (target_repo, weight DESC)
- `idx_edges_type`: (edge_type, weight DESC)

### graph_status

| 字段 | 类型 | 说明 |
|------|------|------|
| repo_id | INTEGER | 仓库 ID (主键) |
| edges_computed_at | TEXT | 边计算时间 |
| dependencies_parsed_at | TEXT | 依赖解析时间 (Phase 2) |

---

## 边权重说明

| 边类型 | 权重 | 说明 |
|--------|------|------|
| author | 1.0 | 固定权重，同一作者强关联 |
| ecosystem (语言) | 0.6 | 固定权重，相同技术栈 |
| ecosystem (主题) | 0.3-1.0 | Jaccard 相似度 |
| collection | 0.5 | 固定权重，用户归类关联 |

---

## API 端点总览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/graph/rebuild` | POST | 重建整个图谱 |
| `/api/graph/status` | GET | 获取图谱计算状态 |
| `/api/graph/nodes/{repo}/edges` | GET | 获取仓库的所有边 |
| `/api/graph/nodes/{repo}/related` | GET | 获取相关仓库列表 |
| `/api/network/graph` | GET | 获取网络可视化数据 |

---

## 性能考虑

1. **边数量控制**:
   - 语言边: 限制每种语言最多 20 个仓库
   - 跳过热门语言（>49 个仓库）

2. **查询优化**:
   - 使用索引按权重降序排序
   - 默认 limit=5 限制返回数量

3. **更新策略**:
   - 手动触发 rebuild
   - 不使用定时任务
   - Phase 2 将支持增量更新

---

## Phase 2 计划

- [ ] 依赖关系边 (dependency)
- [ ] Embedding 相似度边 (semantic)
- [ ] 增量更新机制
- [ ] 向量数据库集成 (ChromaDB)
