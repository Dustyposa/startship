# GitHub Star Helper 产品进化路线设计

## 产品定位

**核心价值**：从用户的 GitHub stars 中快速找到技术方案，辅助技术决策

**核心约束**：所有推荐和回答只基于用户已 star 的仓库，不引入外部数据

---

## 阶段 1：数据初始化 + 基础搜索

### 功能

1. **数据初始化**
   - 输入 GitHub 用户名
   - GraphQL API 抓取所有 stars
   - 本地数据库存储（SQLite）
   - 后续自动加载，手动刷新

2. **基础搜索**
   - 关键词搜索（仓库名、描述）
   - 按语言/分类筛选
   - 结果列表展示

3. **简单对话**
   - 基于搜索结果回答问题
   - 示例："有哪些 Python 的 AI 项目？"

### 技术实现

**GraphQL 查询**：
```graphql
query GetStarredRepositories($username: String!, $cursor: String) {
  user(login: $username) {
    starredRepositories(
      first: 100
      after: $cursor
      orderBy: { field: STARRED_AT, direction: DESC }
    ) {
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        cursor
        starredAt
        node {
          id
          nameWithOwner
          description
          stargazerCount
          url
          diskUsage
          pushedAt
          forkCount
          primaryLanguage {
            name
          }
          repositoryTopics(first: 10) {
            nodes {
              topic {
                name
              }
            }
          }
          languages(first: 5, orderBy: { field: SIZE, direction: DESC }) {
            edges {
              size
              node {
                name
                color
              }
            }
          }
        }
      }
    }
  }
}
```

**数据处理**：
```python
# 主语言
primary_language = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else None

# 所有语言（按代码量排序）
languages = [
    {
        'name': edge['node']['name'],
        'size': edge['size'],
        'color': edge['node']['color']
    }
    for edge in repo['languages']['edges']
]

# Topics
topics = [node['topic']['name'] for node in repo['repositoryTopics']['nodes']]
```

### 用户场景

**场景 1：回忆收藏过什么**
```
用户："我之前 star 过一个 Python 的 WebSocket 库，叫什么来着？"
痛点：stars 太多，翻 GitHub 页面找不到
解决：关键词搜索 "WebSocket Python" → 快速找到
```

**场景 2：按技术分类浏览**
```
用户："我想看看我收藏了哪些 Rust 项目"
痛点：GitHub 没有"按语言筛选 stars"功能
解决：按语言筛选 → 一屏展示所有 Rust stars
```

**场景 3：发现被遗忘的项目**
```
用户："有些项目 star 了就忘了，想看看都是干嘛的"
痛点：300+ stars，很多不记得了
解决：浏览卡片列表，快速看描述回忆
```

### 核心痛点

- **记忆负担**：stars 太多，记不住收藏了什么
- **检索困难**：GitHub 只能翻页，无法搜索
- **信息缺失**：列表模式看不出项目是干嘛的

---

## 阶段 2：语义搜索 + 意图识别

### 功能

1. **语义搜索**
   - 用户用自然语言描述需求
   - 向量嵌入 + ChromaDB
   - 语义相似度匹配

2. **意图识别**
   - LLM 分类用户意图
   - 避免不必要的搜索
   - 支持追问上下文

3. **方案对比**
   - 识别对比意图（"vs"）
   - 生成对比表格

### 技术实现

**意图分类**：
```python
intent_prompt = f"""
分类用户意图，返回类别：
1. chat - 闲聊（你好、在吗）
2. stats - 统计查询（收藏多少、分布如何）
3. search - 仓库查询/搜索（找Python项目、有哪些工具）
4. compare - 对比（FastAPI vs Flask）
5. followup - 追问（基于对话上下文）

用户输入：{user_input}
上下文：{last_assistant_message if last_assistant_message else "无"}

只返回类别名称，如：search
"""
```

**数据流**：
```
用户输入 → LLM 意图分类
  ├─ chat → 直接回复
  ├─ stats → SQL 聚合
  ├─ followup → 用对话上下文
  └─ search/compare → 向量搜索 + RAG
```

### 用户场景

**场景 1：用自然语言描述需求**
```
用户："怎么实现用户认证和权限管理？"
痛点：不知道该搜什么关键词（JWT？OAuth？Session？）
解决：语义搜索理解意图，返回相关项目
```

**场景 2：技术选型对比**
```
用户："Celery 和 RQ 哪个更适合我的场景？"
痛点：需要打开多个项目页面，对比优缺点
解决：AI 直接生成对比表格，一目了然
```

**场景 3：快速统计信息**
```
用户："我收藏的 Python 项目大概有多少？"
痛点：GitHub 只显示总数，无法分类统计
解决：直接回答分类统计数字
```

### 核心痛点

- **词不达意**：不知道准确的技术名词，只能描述需求
- **对比成本高**：需要逐个打开项目看文档
- **信息分散**：无法快速获取整体统计

---

## 阶段 3：智能决策辅助

### 功能

1. **需求匹配分析**
   - 提取需求关键词
   - 匹配相关仓库
   - AI 分析推荐理由

2. **技术栈组合推荐**
   - 识别技术领域
   - 推荐完整技术栈组合

3. **依赖关系分析**
   - 基于 topics 关联
   - 发现可配合的工具

### 技术实现

**需求匹配**：
```
1. 提取需求关键词：高并发、API、实时、博客
2. 匹配仓库：基于 topics + description + README 语义匹配
3. LLM 分析：为什么推荐这些，优缺点是什么
```

**输出示例**：
```
基于你的需求"高并发 API 服务"，推荐：

1. FastAPI - 异步支持，性能优秀
2. Starlette - 轻量级，可定制性强
3. Falcon - 高性能，适合微服务

理由：你的核心需求是性能和并发...
```

### 用户场景

**场景 1：基于场景选型**
```
用户："我要做高并发电商后端，推荐个技术栈？"
痛点：知道需求，但不知道收藏里哪个合适
解决：AI 分析需求，匹配最合适的收藏项目
```

**场景 2：技术栈组合**
```
用户："想做全栈 Web，推荐个前端+后端组合？"
痛点：选了后端不知道前端配什么
解决：AI 推荐完整组合（如 FastAPI + Vue）
```

**场景 3：发现相关工具**
```
用户："我在用 FastAPI，还有什么工具可以配合？"
痛点：不知道生态里还有什么好东西
解决：基于 topics 和依赖关系推荐配套工具
```

### 核心痛点

- **选择困难**：收藏了很多，不知道该用哪个
- **搭配盲区**：不知道哪些工具可以配合使用
- **场景匹配**：不知道自己的场景适合什么方案

---

## 技术架构总结

### 当前状态（阶段 1）
- ✅ FastAPI 后端
- ✅ SQLite 数据库
- ✅ GitHub 集成
- ✅ 基础搜索（FTS5）
- ✅ Vue 3 前端
- ✅ RAG 对话
- ✅ 多轮对话

### 待实现（阶段 2-3）
- GraphQL API 迁移
- 向量嵌入（sentence-transformers）
- ChromaDB 向量存储
- 意图识别（LLM 分类）
- 方案对比功能
- 需求匹配分析

---

## 数据模型

### 仓库（Repository）
```python
{
    'id': str,                    # GitHub ID
    'name_with_owner': str,       # "owner/repo"
    'description': str,           # 描述
    'url': str,                   # GitHub URL
    'stars': int,                 # Star 数量
    'forks': int,                 # Fork 数量
    'disk_usage': int,            # 仓库大小
    'pushed_at': str,             # 最后推送时间
    'starred_at': str,            # 用户 star 时间
    'primary_language': str,      # 主语言
    'languages': List[Dict],      # 所有语言
    'topics': List[str],          # Topics
    'categories': List[str],      # AI 生成的分类
    'summary': str,               # AI 生成的摘要
    'readme_summary': str,        # README 摘要
    'embedding': List[float]      # 向量嵌入（阶段 2）
}
```

---

## 实现优先级

### P0（必须）
- GraphQL 数据抓取
- 基础搜索和筛选
- 简单对话

### P1（重要）
- 语义搜索
- 意图识别
- 方案对比

### P2（增强）
- 需求匹配分析
- 技术栈组合推荐
- 依赖关系分析
