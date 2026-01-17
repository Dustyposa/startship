# GitHub Star Helper - 业务逻辑文档

> 本文档记录系统各核心功能的业务逻辑和技术实现

---

## 目录

1. [功能概览](#功能概览)
2. [核心功能详解](#核心功能详解)
   - [2.1 GitHub 同步 (Sync)](#21-github-同步-sync)
   - [2.2 仓库搜索 (Search)](#22-仓库搜索-search)
   - [2.3 图谱知识 (Graph Knowledge)](#23-图谱知识-graph-knowledge)
   - [2.4 趋势分析 (Trend Analysis)](#24-趋势分析-trend-analysis)
   - [2.5 用户数据管理 (User Data)](#25-用户数据管理-user-data)
   - [2.6 网络可视化 (Network Visualization)](#26-网络可视化-network-visualization)
   - [2.7 AI 对话 (AI Chat)](#27-ai-对话-ai-chat)
3. [数据模型](#数据模型)
4. [API 端点总览](#api-端点总览)

---

## 功能概览

| 功能 | 核心价值 | 引用位置 |
|------|----------|----------|
| GitHub 同步 | 自动同步 GitHub 星标仓库到本地 | `src/services/sync.py` |
| 仓库搜索 | 全文搜索和多维度筛选仓库 | `src/services/search.py` |
| 图谱知识 | 发现仓库间的关系和关联推荐 | `src/services/graph/edges.py` |
| 趋势分析 | 展示星标时间线和语言分布趋势 | `src/services/trend_analysis.py` |
| 用户数据管理 | 收藏夹、标签、笔记管理 | `src/api/routes/user_data.py` |
| 网络可视化 | 交互式关系图谱展示 | `src/services/network.py` |
| AI 对话 | 自然语言查询仓库信息 | `src/services/chat.py` |

---

## 核心功能详解

### 2.1 GitHub 同步 (Sync)

**功能定位**: 将用户在 GitHub 上的星标仓库同步到本地数据库

**业务流程**:
```
1. 从 GitHub GraphQL API 获取所有星标仓库
   ↓
2. 从本地数据库获取现有仓库
   ↓
3. 对比发现:
   - 新增的仓库 (在 GitHub 有，本地没有)
   - 删除的仓库 (本地有，GitHub 没有)
   - 更新的仓库 (两边都有，但数据有变化)
   ↓
4. 执行操作:
   - 新增: 插入新仓库记录
   - 更新: 更新变化的字段
   - 删除: 标记为已删除
   ↓
5. 记录同步历史
```

**变更检测逻辑**:
```python
# 检测字段:
- pushed_at          # 最后推送时间
- stargazer_count    # 星标数量
- fork_count         # Fork 数量
- primary_language   # 主语言
- description        # 描述
- archived           # 是否归档
- visibility         # 可见性
- owner_type         # 所有者类型
- languages          # 语言分布 (数组)
```

**引用**:
- 服务: `src/services/sync.py` → `SyncService`
- API: `src/api/routes/sync.py` → `/api/sync/*`

---

### 2.2 仓库搜索 (Search)

**功能定位**: 提供全文搜索和多维度筛选仓库的能力

**业务流程**:
```
用户输入搜索条件
   ↓
选择搜索模式:
   - 有搜索词 → 全文搜索 (FTS5)
   - 无搜索词 → 过滤搜索
   ↓
应用筛选条件:
   - 语言筛选
   - 星标数量范围
   - 活跃维护 (7天内有更新)
   - 新项目 (6个月内创建)
   - 所有者类型 (组织/个人)
   - 排除归档项目
   ↓
排序:
   - 默认按 starred_at DESC (最新星标优先)
   ↓
返回结果
```

**全文搜索**:
- 使用 SQLite FTS5 全文搜索
- 搜索字段: name_with_owner, description, summary, categories, tech_stack
- BM25 算法排序

**关联推荐** (当 `include_related=true`):
```
1. 获取搜索结果前 5 个仓库
2. 查询每个仓库的图谱边 (limit=3)
3. 收集目标仓库，去重
4. 排除已在搜索结果中的仓库
5. 返回前 5 个相关仓库
```

**引用**:
- 服务: `src/services/search.py` → `SearchService`
- API: `src/api/routes/search.py` → `/api/search`
- 数据库: `src/db/sqlite.py` → `search_repositories_fulltext()`

---

### 2.3 图谱知识 (Graph Knowledge)

**功能定位**: 发现仓库间的关系，实现智能关联推荐

**三种边发现算法**:

#### 2.3.1 作者边 (Author Edges)

**逻辑**: 同一作者/组织的仓库相互关联

```
1. 按 owner 字段分组仓库
2. 对每个有多于 1 个仓库的作者:
   - 创建所有两两配对
   - 边权重 = 1.0 (固定)
3. 元数据: {"author": "owner_name"}
```

**示例**:
```
anthropics/claude-docs ←→ anthropics/claude-cookbook
weight: 1.0
metadata: {"author": "anthropics"}
```

#### 2.3.2 技术生态边 (Ecosystem Edges)

**逻辑**: 相同技术栈或相关主题的仓库相互关联

**语言匹配**:
```
1. 按 primary_language 分组
2. 限制: 2 ≤ 仓库数 < 50 (避免热门语言)
3. 每种语言最多取 20 个仓库
4. 创建两两配对
5. 边权重 = 0.6 (固定)
```

**主题匹配** (Jaccard 相似度):
```
1. 计算两个仓库的主题交集
2. Jaccard = |A∩B| / |A∪B|
3. 条件: 至少 2 个共同主题 AND Jaccard > 0.3
4. 边权重 = Jaccard 值 (保留 2 位小数)
```

**示例**:
```
web-frameworks/api ←→ web-frameworks/http
topics: ["web", "api", "http"] vs ["web", "api", "graphql"]
Jaccard = 2/4 = 0.5
weight: 0.5
metadata: {"common_topics": 2}
```

#### 2.3.3 收藏边 (Collection Edges)

**逻辑**: 被归入同一收藏夹的仓库相互关联

```
1. 查询 repo_collections 表
2. 找到同一 collection_id 的仓库对
3. 使用 c1.repo_id < c2.repo_id 避免重复
4. 边权重 = 0.5 (固定)
```

**SQL 查询**:
```sql
SELECT c1.repo_id, c2.repo_id, col.name
FROM repo_collections c1
JOIN repo_collections c2 ON c1.collection_id = c2.collection_id
JOIN collections col ON col.id = c1.collection_id
WHERE c1.repo_id < c2.repo_id
```

**图谱重建流程**:
```
POST /api/graph/rebuild
   ↓
1. 获取所有仓库 (limit=1000)
2. 发现作者边
3. 发现技术生态边
4. 发现收藏边
5. 清空旧边数据
6. 批量插入新边
7. 更新所有仓库的 graph_status.edges_computed_at
8. 返回结果 {status: "success", edges_count: N}
```

**引用**:
- 服务: `src/services/graph/edges.py` → `EdgeDiscoveryService`
- API: `src/api/routes/graph.py` → `/api/graph/*`
- 数据库表: `graph_edges`, `graph_status`

---

### 2.4 趋势分析 (Trend Analysis)

**功能定位**: 展示用户星标仓库的时间分布和趋势

**三个趋势维度**:

#### 2.4.1 星标时间线 (Star Timeline)

**逻辑**: 按月统计星标数量

```
1. 查询所有仓库的 starred_at 字段
2. 按 YYYY-MM 格式分组
3. 统计每月的星标数量
4. 按时间排序返回
```

**返回格式**:
```json
[
  {"month": "2024-01", "count": 15},
  {"month": "2024-02", "count": 23}
]
```

#### 2.4.2 语言趋势 (Language Trend)

**逻辑**: 展示编程语言的时间分布

```
1. 按月统计每种语言的仓库数量
2. 返回矩阵数据: [月份, 语言1, 语言2, ...]
```

#### 2.4.3 分类演进 (Category Evolution)

**逻辑**: 展示技术分类的时间变化

```
1. 按月统计每个分类的仓库数量
2. 返回矩阵数据
```

**引用**:
- 服务: `src/services/trend_analysis.py` → `TrendAnalysisService`
- API: `src/api/routes/trends.py` → `/api/trends/*`

---

### 2.5 用户数据管理 (User Data)

**功能定位**: 允许用户自定义组织和标注仓库

#### 2.5.1 收藏夹 (Collections)

**业务逻辑**:
```
创建收藏夹:
1. 生成唯一 ID: "coll-{timestamp}"
2. 设置 position = 现有收藏夹数量
3. 存储: id, name, icon, color, position

添加仓库到收藏夹:
1. 验证收藏夹存在
2. 设置 position = 现有仓库数量
3. 插入关联记录

删除收藏夹:
1. 级联删除所有仓库关联
2. 删除收藏夹记录
```

**引用**: `src/api/routes/user_data.py` → `/api/user/collections/*`

#### 2.5.2 标签 (Tags)

**业务逻辑**:
```
创建标签:
1. 生成唯一 ID: "tag-{timestamp}"
2. 存储: id, name, color

给仓库打标签:
1. 插入 repo_tags 关联表
2. 允许多个仓库共享同一标签
```

**引用**: `src/api/routes/user_data.py` → `/api/user/tags/*`

#### 2.5.3 笔记 (Notes)

**业务逻辑**:
```
创建/更新笔记:
1. 使用 repo_id 作为主键
2. 存储: note (文本), rating (1-5分)
3. 支持部分更新 (只更新 note 或只更新 rating)

查询笔记:
1. 按 repo_id 查询
2. 返回 note, rating, created_at, updated_at
```

**引用**: `src/api/routes/user_data.py` → `/api/user/repos/{repo_id}/note`

---

### 2.6 网络可视化 (Network Visualization)

**功能定位**: 将图谱数据可视化为交互式力导向图

**业务流程**:
```
1. 获取图谱数据:
   - 节点: 所有仓库
   - 边: 按权重筛选的边

2. 图布局算法:
   - Force Layout: 力导向布局
   - Circular Layout: 环形布局

3. 渲染:
   - 使用 Echarts graph 类型
   - 节点大小 = 星标数量
   - 边粗细 = 权重
   - 颜色 = 主语言

4. 交互:
   - 点击节点: 跳转到仓库详情
   - 悬停: 显示仓库信息
   - 缩放/拖拽: 自由浏览
```

**数据格式**:
```json
{
  "nodes": [
    {"id": "owner/repo", "name": "repo", "category": "Python", "value": 1000}
  ],
  "edges": [
    {"source": "repo1", "target": "repo2", "weight": 0.8}
  ]
}
```

**引用**:
- 服务: `src/services/network.py` → `NetworkService`
- API: `src/api/routes/network.py` → `/api/network/graph`
- 前端: `frontend/src/views/NetworkView.vue`

---

### 2.7 AI 对话 (AI Chat)

**功能定位**: 通过自然语言查询和操作仓库

**业务流程**:
```
1. 用户输入自然语言问题
2. 意图识别 (Intent Recognition):
   - search_query: 搜索仓库
   - get_repo: 获取仓库详情
   - list_repos: 列出仓库
   - get_stats: 获取统计信息
3. 参数提取:
   - 从问题中提取实体 (仓库名、语言、数量等)
4. 执行操作:
   - 调用相应的服务
5. 生成回复:
   - 将结果转换为自然语言
```

**支持的查询类型**:
- "搜索 Python 的 Web 框架"
- "anthropics/claude-docs 这个项目怎么样?"
- "我有多少个 Go 语言的项目?"
- "最近 star 的项目有哪些?"

**引用**:
- 服务: `src/services/chat.py` → `ChatService`
- API: `src/api/routes/chat.py` → `/api/chat`

---

## 数据模型

### 核心表

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| repositories | 仓库主表 | id, name_with_owner, owner, name, starred_at |
| graph_edges | 图谱边 | source_repo, target_repo, edge_type, weight |
| graph_status | 图谱状态 | repo_id, edges_computed_at |
| collections | 收藏夹 | id, name, icon, color, position |
| repo_collections | 仓库-收藏夹关联 | repo_id, collection_id, position |
| tags | 标签 | id, name, color |
| repo_tags | 仓库-标签关联 | repo_id, tag_id |
| repo_notes | 仓库笔记 | repo_id, note, rating |
| sync_history | 同步历史 | sync_type, started_at, stats_added |

---

## API 端点总览

### 同步
- `POST /api/sync` - 触发全量同步
- `GET /api/sync/status` - 获取同步状态
- `POST /api/sync/reanalyze/{repo}` - 重新分析仓库

### 搜索
- `GET /api/search` - 搜索/筛选仓库
- `GET /api/search/fulltext` - 全文搜索

### 图谱
- `POST /api/graph/rebuild` - 重建图谱
- `GET /api/graph/status` - 获取图谱状态
- `GET /api/graph/nodes/{repo}/edges` - 获取仓库的边
- `GET /api/graph/nodes/{repo}/related` - 获取相关仓库

### 趋势
- `GET /api/trends/timeline` - 星标时间线
- `GET /api/trends/languages` - 语言趋势
- `GET /api/trends/categories` - 分类演进

### 用户数据
- `GET/POST/PUT/DELETE /api/user/collections/*` - 收藏夹管理
- `GET/POST/PUT/DELETE /api/user/tags/*` - 标签管理
- `GET/PUT /api/user/repos/{repo}/note` - 笔记管理
- `GET/PUT /api/user/repos/{repo}/tags` - 仓库标签关联
- `GET/PUT /api/user/repos/{repo}/collection` - 仓库收藏关联

### 网络
- `GET /api/network/graph` - 获取网络图数据

### 对话
- `POST /api/chat` - AI 对话

---

## 版本历史

- v1.0.0 - 初始版本，实现核心功能
- v1.1.0 - 添加图谱知识功能
- v1.2.0 - 添加趋势分析功能
