# GitHub Star Helper - 业务逻辑文档

> 本文档记录系统各核心功能的业务逻辑和技术实现

---

## 目录

1. [功能概览](#功能概览)
2. [核心功能详解](#核心功能详解)
   - [2.1 GitHub 同步 (Sync)](#21-github-同步-sync)
   - [2.2 仓库搜索 (Search)](#22-仓库搜索-search)
     - [2.2.1 全文搜索 (FTS5)](#221-全文搜索-fts5)
     - [2.2.2 推荐系统](#222-推荐系统)
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
   - 更新: 根据变更类型更新
   - 删除: 标记为已删除
   ↓
5. 记录同步历史
```

**变更检测逻辑**:

系统采用两条主线策略，根据变化的性质选择更新方式。

### 字段来源说明

```
[GitHub] - 从 GitHub API 获取的字段
[LLM]    - 本地 LLM 分析生成的字段
[本地]   - 系统本地生成的字段
```

---

#### 重度更新 (Heavy)

**触发条件**：
```python
- pushed_at 变化    # 仓库有新提交
- languages 为空    # 数据不完整
```

**原因**：`pushed_at` 变化说明仓库有新代码提交，需要完全刷新内容。

**更新内容**：
```python
需要从 GitHub API 获取:
[GitHub] readme_content    # README 内容
[GitHub] topics            # 主题标签
[GitHub] languages         # 语言分布
[GitHub] homepage_url      # 主页链接
[GitHub] description       # 描述
[GitHub] primary_language  # 主语言
[GitHub] stargazer_count    # 星标数
[GitHub] fork_count        # Fork 数
[GitHub] url               # 仓库链接
[GitHub] pushed_at         # 最后推送时间
[GitHub] created_at        # 创建时间
[GitHub] archived          # 归档状态
[GitHub] visibility        # 可见性
[GitHub] owner_type        # 所有者类型
[GitHub] organization      # 组织名
[GitHub] license_key        # 开源协议

本地生成:
[本地] last_synced_at    # 最后同步时间

需要 LLM 重新分析:
[LLM] summary           # 摘要
[LLM] categories         # 分类
[LLM] features          # 特性
[LLM] use_cases         # 使用案例
```

**性能**：~10 秒/仓库

---

#### 轻度更新 (Light)

**触发条件**：除 `pushed_at` 外的所有字段变化

**字段分类**：

```python
# A 类：不需要 LLM 重新分析
[GitHub] stargazer_count   # 星标数
[GitHub] fork_count        # Fork 数
[GitHub] archived          # 归档状态 (0/1)
[GitHub] visibility        # 可见性
[GitHub] owner_type        # 所有者类型

# B 类：需要 LLM 重新分析
[GitHub] description       # 描述变化 → [LLM] summary 基于描述更新
[GitHub] primary_language  # 主语言变化 → [LLM] 完整重新分析所有字段
```

**说明**：
- `description` 变化：只更新 summary，其他分析结果保留
- `primary_language` 变化：触发完整重新分析，因为技术栈变化影响所有分析维度

**更新策略**：

```python
if 变化字段 in A 类:
    # 只更新变化的字段
    # 保留 LLM 分析结果
    update_data = changed_fields
    update_data.update({
        [LLM] "summary": existing.summary,
        [LLM] "categories": existing.categories,
        [LLM] "features": existing.features,
        [LLM] "use_cases": existing.use_cases
    })

elif 变化字段 in B 类:
    # 获取最新 GitHub 数据
    update_data = _build_repo_data(github_repo, existing)
    # 触发 LLM 重新分析
    # update_data 包含 [GitHub] 字段和 [LLM] 生成字段
```

**性能**：
- A 类更新：~0.1 秒/仓库
- B 类更新：~1 秒/仓库

---

**性能优化对比**：

```
假设 1000 个仓库，每天同步一次：

实际变化分布：
- 850 个：只有星标数变化 (A 类)
- 100 个：元数据变化 (A 类 + B 类)
- 50 个：有新提交 (Heavy)

旧逻辑（全量更新）:
1000 × 10 秒 = 10000 秒 (2.8 小时)

新逻辑:
850 × 0.1 + 100 × 1 + 50 × 10 = 735 秒 (12 分钟)
性能提升: 13 倍
```

**引用**:
- 服务: `src/services/sync.py` → `SyncService`
- API: `src/api/routes/sync.py` → `/api/sync/*`

---

### 2.2 仓库搜索 (Search)

**功能定位**: 提供全文搜索和多维度筛选仓库的能力

---

#### 2.2.1 全文搜索 (FTS5)

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
返回结果: { results: [...] }
```

**技术实现**:
- 使用 SQLite FTS5 全文搜索
- 搜索字段: name_with_owner, description, summary, categories
- BM25 算法排序

<details>
<summary><b>📖 FTS5 是什么？(第一性原理)</b></summary>

**FTS5 = Full-Text Search version 5**

SQLite 的全文搜索扩展，专门用于快速搜索大量文本。

**核心原理 - 倒排索引 (Inverted Index)**:

传统搜索（顺序扫描）:
```
搜索 "web framework"
↓
遍历所有文档，检查是否包含 "web" 和 "framework"
↓
1000 个文档 × 平均 500 字 = 50 万字比较
```

FTS5 倒排索引:
```
预处理阶段（建立索引）:
"web"     → [doc1, doc5, doc23, doc67, ...]
"framework"→ [doc1, doc3, doc5, doc8, ...]
...

搜索 "web framework":
↓
1. 找 "web"     → [doc1, doc5, doc23, doc67, ...]
2. 找 "framework"→ [doc1, doc3, doc5, doc8, ...]
3. 求交集      → [doc1, doc5]  ← 瞬间完成
```

**为什么快？**
- 空间换时间：预先建立词→文档的映射
- O(n) → O(log n)：从遍历所有文档变成查表

**BM25 排序算法**:
```
相关性分数 = Σ (IDF × TF × 字段权重)

IDF (逆文档频率) = log(总文档数 / 包含该词的文档数)
  → 稀有词权重高（"grpc" > "web"）

TF (词频) = 词在文档中的出现次数
  → 出现多次权重高

结果: 稀有且多次出现的词得分最高
```

**FTS5 vs LIKE 查询**:

| 特性 | LIKE | FTS5 |
|------|------|------|
| 速度 | O(n) 遍历所有行 | O(log n) 索引查询 |
| 中英文支持 | 只能前缀匹配 | 分词 + 全文匹配 |
| 排序 | 无法按相关性排 | BM25 自动排序 |
| 搜索语法 | `WHERE col LIKE '%keyword%'` | `WHERE fts MATCH 'keyword'` |

</details>

**API**:
- `GET /api/search` - 主搜索接口
- `GET /api/search/fulltext` - 纯 FTS5 搜索

---

#### 2.2.2 推荐系统

**说明**: 搜索结果可附加推荐，基于图谱知识系统实现 (详见 [2.3 图谱知识](#23-图谱知识-graph-knowledge))

**触发方式**: `include_related=true` (默认启用)

**业务流程**:
```
1. 获取搜索结果的前 5 个仓库
2. 查询每个仓库的图谱边 (limit=3)
3. 收集目标仓库，去重
4. 排除已在搜索结果中的仓库
5. 返回前 5 个相关仓库
```

**返回格式**:
```json
{
  "results": [...],   // 直接搜索结果
  "related": [...]    // 推荐结果
}
```

**UI 展示要求**:
- 明确区分两个区块
- 标注推荐来源: "基于知识图谱"
- 使用不同的视觉样式

**引用**:
- 服务: `src/services/search.py` → `SearchService`
- API: `src/api/routes/search.py` → `/api/search`
- 数据库: `src/db/sqlite.py` → `search_repositories_fulltext()`

---

### 2.3 图谱知识 (Graph Knowledge)

**功能定位**: 发现仓库间的关系，为推荐系统提供底层支持

**应用场景**:
1. ✅ 搜索结果的关联推荐 (见 [2.2.2 推荐系统](#222-推荐系统))
2. ✅ 单个仓库的相关推荐: `GET /api/graph/nodes/{repo}/related`
3. ✅ 网络可视化: `GET /api/network/graph`

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

**主题匹配** (Jaccard 相似度)

<details>
<summary><b>📖 Jaccard 相似度是什么？(第一性原理)</b></summary>

**Jaccard 相似度** - 衡量两个集合相似程度的指标

**公式**:
```
J(A, B) = |A ∩ B| / |A ∪ B|
        = 交集大小 / 并集大小
        = 0 ~ 1 之间
```

**直观理解**:

假设两个圆代表两个仓库的主题集合：
```
    A ⊕───┐
      ╱   ╲
     ╱  共同 ╲     ← 交集 A∩B (共同的兴趣)
    ╱     ╲ ╲
   └───────┘─┘
   ↑      ↑
   A      B
```

Jaccard = 重叠部分 / 整体面积

**示例计算**:

```
仓库 A topics: ["web", "api", "python", "async"]
仓库 B topics: ["web", "api", "python", "database"]

交集 A ∩ B = ["web", "api", "python"]     → 3 个
并集 A ∪ B = ["web", "api", "python", "async", "database"] → 5 个

Jaccard = 3/5 = 0.6
```

**为什么不用简单计数？**

| 方法 | A=["web","api"] B=["web","api","python","async"] | A=["web"] B=["web","api","python"] |
|------|--------------------------------------------------|-----------------------------------|
| 简单计数 | 共同 2 个 | 共同 1 个 |
| Jaccard | 2/4 = 0.5 | 1/3 = 0.33 |

简单计数的问题：不考虑集合大小，不公平

**Jaccard 的优势**:
- 归一化：结果总是在 0-1 之间
- 阈值稳定：0.3 在任何规模的数据集都有相同含义
- 惩罚规模差异：小集合重合多 → 分数更高

**在图谱中的应用**:

```
规则: 至少 2 个共同主题 AND Jaccard > 0.3

为什么两个条件？
1. "至少 2 个": 避免偶然匹配（1 个太容易）
2. "Jaccard > 0.3": 确保质量，不是 A 有 100 个 topics，B 只占其中 3 个
```

**边权重设计**:
```
weight = Jaccard 值

好处:
- 相似度越高 → 边越强 → 推荐优先级越高
- 动态权重：反映实际相似程度，而非固定值
```

</details>

**业务流程**:
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
